from simpy.util import start_delayed
from cache import Cache
import ConfigParser, cache, argparse, logging, pprint
import numpy as np
from uhashring import HashRing
import loadDistribution, multiThread,adaptive
from client import Client
from request import Request
import utils,os,time,simpy,datetime
from threading import Thread
from inputParser import inputParser
from inputParser import inputParser2
import multiprocessing as mp
from collections import deque

cephLayer = 3
algo_start = False

count_w=0
warmup=sim_req_num=sim_end=0
sim_req_comp=[]
def build_network(config,logger,env):
	# 1 Gbps = 125 MB/s
	# 10 Gbps = 1250 MB/s
	# 40 Gbps = 5000 MB/s
	links={}
	L1_In = float(config.get('Network', 'L1_In').split("G")[0])/8*1000*1000*1000
	L2_In = float(config.get('Network', 'L2_In').split("G")[0])/8*1000*1000*1000
	L1_Out = float(config.get('Network', 'L1_Out').split("G")[0])/8*1000*1000*1000
	L2_Out = float(config.get('Network', 'L2_Out').split("G")[0])/8*1000*1000*1000
	numNodes = int(config.get('Simulation', 'nodeNum'))
        if config.get('Simulation', 'L1') == "true" :
                for i in range(numNodes):
			linkId = "L1in1r"+str(i)
                        links[linkId]=simpy.Container(env, L1_In, init=L1_In)
			linkId = "L1out0r"+str(i)
                        links[linkId]=simpy.Container(env, L1_Out, init=L1_Out)
	
	if config.get('Simulation', 'L2') == "true" :		
		for i in range(numNodes):
			linkId = "L2in1r"+str(i)
                        links[linkId]=simpy.Container(env, L2_In, init=L2_In)
			linkId = "L2out0r"+str(i)
                        links[linkId]=simpy.Container(env, L2_Out, init=L2_Out)
	linkId = "Cephout"
	links[linkId]=simpy.Container(env, L2_In, init=L2_In)	

	return links



def build_d3n(config, logger,env):
	#Build the cache hierarchy with the given configuration
	hierarchy = {}
	numNodes = int(config.get('Simulation', 'nodeNum'))
	hashType =  config.get('Simulation', 'hashType')
	if (hashType == "consistent"):
		hr = loadDistribution.consistentHashing(numNodes)	
	elif (hashType == "rendezvous"):
		hr = loadDistribution.consistentHashing(numNodes)	
	elif (hashType == "rr"):
		hr = numNodes
	caches_l1,caches_l2, backend= {},{},{}
	if config.get('Simulation', 'L1') == "true" :
		cephLayer=2
		for i in range(numNodes):
			name = "1-"+str(i)
			hierarchy[name]=build_cache(config, name, 'L1', hr, hashType,logger)
	if config.get('Simulation', 'L2') == "true" :
		cephLayer=3
		for i in range(numNodes):
			name = "2-"+str(i)
			hierarchy[name]=build_cache(config, name, 'L2', hr, hashType, logger)

	backend=build_cache(config, name, 'BE', hr, hashType, logger)
	name = str(cephLayer)+"-0"
	hierarchy[name]=backend	
	
	links = build_network(config,logger,env)

	return hierarchy, links
def build_cache(config, name, layer, hr, hashType,logger):
	obj_size=utils.get_obj_size(config)
	if layer == "L1":
        	name = 'L1_rep'
		size = utils.get_cache_size(config,obj_size,'L1_size')
	elif layer =="L2":
		name = 'L2_rep'
		size = utils.get_cache_size(config,obj_size,'L2_size')
	elif layer =="BE":
		name = 'L1_rep'	
		size=1
	shadow_size =int(utils.get_cache_size(config,obj_size,'shadow_size'))
	return cache.Cache(layer,size , config.get('Simulation', name) , "WT", hr, hashType, obj_size,shadow_size,logger)


def hit(request,hierarchy,logger,env,links,cacheId):
        request.set_fetch(cacheId)
        utils.display(env,logger,request,"Hit")
        source = [ request.dest[0],request.dest[1] ]
        dest = request.path.pop()
        if dest[0]==0:
       		request.rtype="completion"	       
        else:
       		request.rtype="send_data"	       
	request.source = source
     	request.dest=dest
        generate_event(request,hierarchy,logger,env,links)


def miss(request,hierarchy,logger,env,links,cacheId):
        request.path.append( [ request.dest[0],request.dest[1] ] )
        utils.display(env,logger,request,"Miss")
        dest=[]
	dest.extend([(int(request.dest[0])+1) ,int(hierarchy[cacheId].get_l2_address(request.key))])
        request.source = request.dest
        cid= str(dest[0])+"-"+str(dest[1])
        r = hierarchy[cid].read(request.key,request.size)
        if r:
                if ((request.dest[1] == dest[1] ) and (request.dest[0] == 1)):
                        hierarchy[cacheId]._miss_count-=1
                request.dest = dest
		hit(request,hierarchy,logger,env,links,cid)
		
        else:

		utils.add_cache_request_time(hierarchy[cid],env.now,request)
                request.dest = dest
		request.path.append([dest[0],dest[1] ])
                utils.display(env,logger,request,"Miss")
                cacheId = "3-0"
                request.source = dest
                request.dest = [3,0]
		hit(request,hierarchy,logger,env,links,cacheId)


def readEvent(request,hierarchy,logger,env,links):
        yield env.timeout(0)
        cacheId = str(request.dest[0])+"-"+str(request.dest[1])
        r = hierarchy[cacheId].read(request.key,request.size)
        if r:
                hit(request,hierarchy,logger,env,links,cacheId)
				
        else:
		utils.add_cache_request_time(hierarchy[cacheId],env.now,request)
		miss(request,hierarchy,logger,env,links,cacheId)
				
def SendEvent(request,hierarchy,logger,env,links):

	sLinkId,dLinkId = utils.get_link_id(request.source, request.dest)
	if (request.source[0]==2 and request.dest[0]==1 and request.source[1]==request.dest[1]):
		yield env.timeout(0)	
	else:
		# Get the required amount of Bandwidth
		if sLinkId: 
			yield links[sLinkId].get(links[sLinkId].capacity)
			latency = float(request.size) / links[sLinkId].capacity
#		else:
#			yield links["Cephout"].get(links["Cephout"].capacity)

		if dLinkId:
			yield links[dLinkId].get(links[dLinkId].capacity)
			latency = float(request.size) / links[dLinkId].capacity
	
		# The "actual" refueling process takes some time
		yield env.timeout(latency)
	
		# Put the required amount of Bandwidth
		if sLinkId:
			yield links[sLinkId].put(links[sLinkId].capacity)
#		else:
#			yield links["Cephout"].put(links["Cephout"].capacity)

		if dLinkId:
			yield links[dLinkId].put(links[dLinkId].capacity)
		
	cacheId = str(request.dest[0])+"-"+str(request.dest[1])
	if (request.source[0] == cephLayer):
		utils.display(env,logger,request,"From Ceph")
		size = float(request.size)/float(obj_size)
		hierarchy[cacheId].insert(request.key,size)
		utils.get_latency(request,hierarchy[cacheId],env.now)		
			
	elif (int(request.source[1]) != int(request.dest[1])):
		utils.display(env,logger,request,"Remote L2")
		size = float(request.size)/float(obj_size)
		hierarchy[cacheId].insert(request.key,size)
		request.set_info("Remote_L2")
		#if ( int(request.fetch.split("-")[0]) == 2):
		#	utils.get_latency(request,hierarchy[cacheId],env.now)		
		#if ( int(request.fetch.split("-")[0]) == 2):
		utils.get_latency(request,hierarchy[cacheId],env.now)		
	else:
		utils.display(env,logger,request,"Local L2")
		request.set_info("Local_L2")

	dest = request.path.pop()
	if dest[0]==0:
		request.rtype= "completion"
	else:
		request.rtype = "send_data"
	request.source =  [ request.dest[0], request.dest[1] ] 
	request.dest=dest
	generate_event(request,hierarchy,logger,env,links)

	
def CompletionEvent(request,hierarchy,logger,env,links):
	sLinkId,dLinkId = utils.get_link_id(request.source, request.dest)
	
	if sLinkId:
                yield links[sLinkId].get(links[sLinkId].capacity)
		latency = float(request.size) / links[sLinkId].capacity
        if dLinkId:
		print "Error on Completion"
	
	yield env.timeout(latency)
	if sLinkId:
                yield links[sLinkId].put(links[sLinkId].capacity)

	request.set_endTime(env.now)
	request.set_compTime( request.endTime - request.startTime)

	
	global  sim_req_num
	sim_req_num +=1
	global  sim_req_comp
	global  count_w
	count_w+=1
	sim_req_comp.append(request.get_compTime())
	global  sim_end
	sim_end = env.now

	utils.display(env,logger,request)
	cid = request.client
	del request
	request_generator(cid,hierarchy,logger,env,links,1)

def generate_event(request,hierarchy,logger,env,links):
	if request.rtype == "read_req":
		request.set_startTime(env.now)
		env.process(readEvent(request,hierarchy,logger,env,links))
	elif request.rtype == "send_data":
		env.process(SendEvent(request,hierarchy,logger,env,links))
	elif request.rtype == "completion":
		env.process(CompletionEvent(request,hierarchy,logger,env,links))

		
def request_generator(client,hierarchy,logger,env,links,reqNum):
	if client._trace:
#	if jobList:
		for i in range(int(reqNum)) :
			obj=client._trace.popleft()
#			obj=jobList.popleft()
			reqid=int(reqList.popleft())
			path,destination,source=[],[],[]
	                destination.extend([1,client._rackid])
			source=[0,client._rackid]
	                path = [[0,client._rackid]]
			req = Request(reqid,source,destination,obj,client._obj_size,"read_req",path,client,"")
			generate_event(req,hierarchy,logger,env,links)


def adaptive_algorithm(hierarchy,env,shadow_window,nodeNum,warmup,a_time):
	global algo_start
	while(utils.check_remaning_events(clientList)):
	#for i in range(10):
		if (algo_start == False):
			yield env.timeout(warmup)
			algo_start =True
			#adaptive.reset_counters(hierarchy,nodeNum)
		else:
			yield env.timeout(a_time)
	
	#	adaptive.set_cache(hierarchy,env,shadow_window,nodeNum)
		adaptive.set_cache_size(hierarchy,env,shadow_window,nodeNum)
		
if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='Simulate a cache')
    	parser.add_argument('-c','--config-file', help='Configuration file for the memory heirarchy', required=True)
	arguments = vars(parser.parse_args())
	
        config_file = arguments['config_file']		
	config = ConfigParser.ConfigParser()
	config.readfp(open(config_file))
	
	log_filename = 'simulator.log'
	if config.get('Simulation', 'log_file'):
		log_filename = config.get('Simulation', 'log_file')
	
	time=str(datetime.datetime.now()).replace(" ","_")
	log_filename+=time	
	#Clear the log file if it exists
    	with open(log_filename, 'w'):
        	pass
	logger = logging.getLogger()
	fh = logging.FileHandler(log_filename)
    	logger.addHandler(fh)
	logger.setLevel(logging.DEBUG)
	
	logger.info('Loading config...')
	print 'Loading config...'

	env = simpy.Environment()
	hierarchy, links = build_d3n(config, logger,env)

	logger.info('Creating Enviroment...')
	print 'Creating Enviroment...'

	utils.delete_old_files(config)

	logger.info('Parsing Trace File...')
	print "Parsing Trace File..."	
	jobList=deque()
	inputParser(config.get('Simulation', 'input'),jobList)
	# Instantiate a thread pool with N worker threads
     

	clientNum = int(config.get('Simulation', 'clientNum'))
        nodeNum = int(config.get('Simulation', 'nodeNum'))
        threadNum = int(config.get('Simulation', 'threadNum'))
        shadow_window = int(config.get('Simulation', 'shadow_window'))
        f_adapt = config.get('Simulation', 'adaptive_algorithm')
        warmup = int(config.get('Simulation', 'warmup_time'))
        a_time = int(config.get('Simulation', 'algorithm_time'))

	clientList={}
	counter=0
	reqList=deque()

	obj_size=utils.get_obj_size(config)

	jobList2=deque()
	inputs=["input1","input2","input3","input4","input5"]
	for i in range(nodeNum):
		for j in range(clientNum):
			jobList3=deque()
			inputParser2(config.get('Simulation', inputs[i]),jobList3)
			clientList[counter]=Client(counter,i,jobList3,obj_size,threadNum)	
			counter+=1	
	
#	for i in xrange(len(jobList)):
	for i in xrange(len(jobList3)*nodeNum):
		reqList.append(i+1)
	pool = multiThread.ThreadPool(clientNum)
	for key in clientList.keys():
		pool.add_task(request_generator, clientList[key],hierarchy,logger,env,links,threadNum)
	pool.wait_completion()
	if( f_adapt == 'true'):
		env.process(adaptive_algorithm(hierarchy,env,shadow_window,nodeNum,warmup,a_time))
	
	logger.info('Running Simulation...')
	print "Running Simulation..."	
				
	env.run()

 	logger.info("Simulation Ends")
 	logger.info("Collecting Statistics...")
	print "Simulation Ends"
	print "Collecting Statistics..."	
	
	#utils.cacheinfo2(hierarchy)
	stats={}
	stats["rn"]=sim_req_num
	stats["clist"]=sim_req_comp
	stats["sim_end"]=sim_end
	stats["warmup"]=warmup
	stats["count_w"]=count_w


	res_file=config.get('Simulation', 'res_file')
	fd = open(res_file,"a")
	fd.write("\n\n")
	fd.write("-------------RESULTS---------------------\n")
	fd.write("Date:"+time+"\n")
	utils.stats(hierarchy,config,fd,stats)	
	utils.missCost(hierarchy,config,fd)	
	
	fd.close()




