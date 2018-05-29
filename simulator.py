from simpy.util import start_delayed
from cache import Cache
import ConfigParser, cache, argparse, logging, pprint
import numpy as np
from uhashring import HashRing
import loadDistribution, multiThread,shadow
from client import Client
from request import Request
import utils,os,time,simpy,datetime
from threading import Thread
from inputParser import inputParser
from inputParser import inputParser2
import multiprocessing as mp
cephLayer=3
reqList,jobList=[],[]
algo_start = False
#L1_lat_count=0
#L2_lat_count=0
#L1_miss_lat=0
#L2_miss_lat=0

sim_req_num=sim_end=0
sim_req_comp=[]
def build_network(config,logger,env):
	# 1 Gbps = 125 MB/s
	# 10 Gbps = 1250 MB/s
	# 40 Gbps = 5000 MB/s
	TOR_SIZE=1
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



def build_d3n(config, logger):
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
			caches_l1[i]=build_cache(config, name, 'L1', hr, hashType,logger) 
			hierarchy[name]=caches_l1[i]
	if config.get('Simulation', 'L2') == "true" :
		cephLayer=3
		for i in range(numNodes):
			name = "2-"+str(i)
			caches_l2[i]=build_cache(config, name, 'L2', hr, hashType, logger)
			hierarchy[name]=caches_l2[i]

	backend=build_cache(config, name, 'BE', hr, hashType, logger)
	name = str(cephLayer)+"-0"
	hierarchy[name]=backend	


	return hierarchy
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
    #	shadow.print_shadows(hierarchy,cacheId)
    #	shadow.set_cache_size(hierarchy,env)
        request.set_fetch(cacheId)
        utils.display(env,logger,request,"Hit")
        source = [ request.dest[0],request.dest[1] ]
        dest = request.path.pop()
        if dest[0]==0:
                source =  [ request.dest[0], request.dest[1] ]
                req = Request(request.reqId,source,dest,request.key,request.size,"completion",request.path,request.client,request.get_fetch())
        else:
                req = Request(request.reqId,source,dest,request.key,request.size,"send_data",request.path,request.client,request.get_fetch())
        req.set_startTime(request.startTime)
        req.set_endTime(request.endTime)
        req.missLayer1=request.missLayer1
        req.missLayer2=request.missLayer2
        generateEvent(req,hierarchy,logger,env,links)


def miss(request,hierarchy,logger,env,links,cacheId):
        request.path.append( [ request.dest[0],request.dest[1] ] )
#       print request.dest[0],request.dest[1],request.reqId,request.path
        utils.display(env,logger,request,"Miss")
        path,source,dest=[],[],[]
        dest.append(int(request.dest[0])+1)
        dest.append(int(hierarchy[cacheId].get_l2_address(request.key)))
        source = request.dest
        cid= str(dest[0])+"-"+str(dest[1])
        r = hierarchy[cid].read(request.key,request.size)
        if r:
                if ((request.dest[1] == dest[1] ) and (request.dest[0] == 1)):
                        hierarchy[cacheId]._miss_count-=1
                else:
			request.missLayer1=str(request.dest[0])+"-"+str(request.dest[1])
                request.source = source
                request.dest = dest

		hit(request,hierarchy,logger,env,links,cid)
		
        else:

		if ((request.dest[1] == dest[1] ) and (request.dest[0] == 1)):
                        request.missLayer2=cid
                else:
			request.missLayer1=str(request.dest[0])+"-"+str(request.dest[1])
			request.missLayer2=cid

		request.source = source
                request.dest = dest
                request.path.append([dest[0],dest[1] ])
                utils.display(env,logger,request,"Miss")
                cacheId = "3-0"
                request.source = request.dest
                request.dest = [3,0]
                hit(request,hierarchy,logger,env,links,cacheId)


def readEvent(request,hierarchy,logger,env,links):
        yield env.timeout(0)
        cacheId = str(request.dest[0])+"-"+str(request.dest[1])
        r = hierarchy[cacheId].read(request.key,request.size)
        if r:
                hit(request,hierarchy,logger,env,links,cacheId)
				
        else:
		miss(request,hierarchy,logger,env,links,cacheId)
				



def readEvent2(request,hierarchy,logger,env,links):
	cacheId = str(request.dest[0])+"-"+str(request.dest[1])
	r = hierarchy[cacheId].read(request.key,request.size)
	yield env.timeout(0)
	# If it is a Hit
	if r:
		request.set_fetch(cacheId)
		utils.display(env,logger,request,"Hit")
		source = [ request.dest[0],request.dest[1] ]
		dest = request.path.pop()
		if dest[0]==0:
			source =  [ request.dest[0], request.dest[1] ]
                	req = Request(request.reqId,source,dest,request.key,request.size,"completion",request.path,request.client,request.get_fetch())
			req.set_startTime(request.startTime)
			req.set_endTime(request.endTime)
                	generateEvent(req,hierarchy,logger,env,links)
		else:
			
			req = Request(request.reqId,source,dest,request.key,request.size,"send_data",request.path,request.client,request.get_fetch())
			req.set_startTime(request.startTime)
			req.set_endTime(request.endTime)
			
                	generateEvent(req,hierarchy,logger,env,links)
			
	else:
		# Miss on Layer
		utils.display(env,logger,request,"Miss")
		path,source,dest=[],[],[]
		dest.append(int(request.dest[0])+1)
	        if int(request.dest[0])+1 == 3:
			dest.append(0)
		else:
			
			dest.append(int(hierarchy[cacheId].get_l2_address(request.key)))
#			print request.key, dest[1]
			if ((request.dest[1] == dest[1] ) and (request.dest[0] == 1)): 
				cid= str(dest[0])+"-"+str(dest[1])
				if(hierarchy[cid].checkKey(request.key)):
					hierarchy[cacheId]._miss_count-=1
		source = request.dest
		path = request.path[:]
		path.append( [ request.dest[0],request.dest[1] ] )
		req = Request(request.reqId,source,dest,request.key,request.size,"read_req",path,request.client,request.get_fetch())
		req.set_startTime(request.startTime)
		req.set_endTime(request.endTime)
	#		req.set_time(env.now)
        #		req.set_startTime(env.now)
		generateEvent(req,hierarchy,logger,env,links)
			#readEvent(req,hierarchy,logger,env,links)



def findLinkId(source,dest):
	slayer=source[0]
	srack=source[1]
	dlayer=dest[0]
	drack=dest[1]

	sLinkId=dLinkId=None	
	if (slayer == 3):
		sLinkId = None
	else:
		sLinkId = "L"+str(slayer)+"out0r"+str(srack)
	
	if (dlayer == 0):
		dLinkId=None
	else:
		dLinkId = "L"+str(dlayer)+"in1r"+str(drack)

	return sLinkId,dLinkId

def SendEvent(request,hierarchy,logger,env,links):

	sLinkId,dLinkId = findLinkId(request.source, request.dest)
	if (request.source[0]==2 and request.dest[0]==1 and request.source[1]==request.dest[1]):
		yield env.timeout(0)	
	else:

		# Get the required amount of Bandwidth
		if sLinkId: 
			yield links[sLinkId].get(links[sLinkId].capacity)
			latency = float(request.size) / links[sLinkId].capacity
		else:
			yield links["Cephout"].get(links["Cephout"].capacity)

		if dLinkId:
			yield links[dLinkId].get(links[dLinkId].capacity)
			latency = float(request.size) / links[dLinkId].capacity
	
		# The "actual" refueling process takes some time
		yield env.timeout(latency)
	
	
		# Put the required amount of Bandwidth
		if sLinkId:
			yield links[sLinkId].put(links[sLinkId].capacity)
		else:

			yield links["Cephout"].put(links["Cephout"].capacity)

		if dLinkId:
			yield links[dLinkId].put(links[dLinkId].capacity)
		
	cacheId = str(request.dest[0])+"-"+str(request.dest[1])
	if (request.source[0] == cephLayer):
		utils.display(env,logger,request,"From Ceph")
		size = float(request.size)/float(obj_size)
		hierarchy[cacheId]._insert(request.key,size)
		#hierarchy[cacheId]._miss_count+=1
	
	elif (int(request.source[1]) != int(request.dest[1])):
		utils.display(env,logger,request,"Remote L2")
		size = float(request.size)/float(obj_size)
		hierarchy[cacheId]._insert(request.key,size)
		request.set_info("Remote_L2")
	else:
		utils.display(env,logger,request,"Local L2")
		request.set_info("Local_L2")

	dest = request.path.pop()
	if dest[0]==0:
		typeReq = "completion"
	else:
		typeReq = "send_data"
	source =  [ request.dest[0], request.dest[1] ] 
       	req = Request(request.reqId,source,dest,request.key,request.size,typeReq,request.path,request.client,request.get_fetch())
	req.set_startTime(request.startTime)
        req.set_info(request.get_info())
	req.set_endTime(request.endTime)
	req.missLayer1=request.missLayer1
        req.missLayer2=request.missLayer2
	generateEvent(req,hierarchy,logger,env,links)

	
def CompletionEvent(request,hierarchy,logger,env,links):
	sLinkId,dLinkId = findLinkId(request.source, request.dest)
	
	if sLinkId:
                yield links[sLinkId].get(links[sLinkId].capacity)
		latency = float(request.size) / links[sLinkId].capacity
        if dLinkId:
		print "Error on Completion"
	
	yield env.timeout(latency)

	if sLinkId:
                yield links[sLinkId].put(links[sLinkId].capacity)
#	if dLinkId:
#		yield links[dLinkId].put(bw_required)	

	request.set_endTime(env.now)
	request.set_compTime( request.endTime - request.startTime)

	global  sim_req_num
	sim_req_num +=1
	global  sim_req_comp
	sim_req_comp.append(request.get_compTime())
	global  sim_end
	sim_end = env.now
	if request.missLayer1:
		cacheId = request.missLayer1
		hierarchy[cacheId].miss_lat+=float(request.get_compTime())
		hierarchy[cacheId].lat_count+=1
	if request.missLayer2:
		cacheId = request.missLayer2
		hierarchy[cacheId].miss_lat+=float(request.get_compTime())
		hierarchy[cacheId].lat_count+=1

	#global  L1_miss_lat
	#global  L2_miss_lat
	#global  L1_lat_count
	#global  L2_lat_count
	#if (int( request.fetch.split("-")[0]) == 2) :
	#	if (request.get_info() == "Remote_L2"):
	#		cacheId = request.fetch
	#		hierarchy[cacheId].miss_lat+=float(request.get_compTime())
	#		hierarchy[cacheId].lat_count+=1
	#if (int( request.fetch.split("-")[0]) == 3 ):
	#	L2_miss_lat+=float(request.get_compTime())
	#	cacheId = request.fetch
	#	hierarchy[cacheId].miss_lat+=float(request.get_compTime())
	#	hierarchy[cacheId].lat_count+=1
	#	L2_lat_count+=1
	#	L1_miss_lat+=float(request.get_compTime())
	#	L1_lat_count+=1
	
	utils.display(env,logger,request)
	#global algo_start	
	#if (algo_start== False) and (int(sim_req_num) > 6061):
	#	algo_start = True
	#	print "algo"
	#	algo(hierarchy,env)
	cid = request.client
	del request
	issueRequests(cid,hierarchy,logger,env,links,1)
def generateEvent(request,hierarchy,logger,env,links):
	request.set_time(env.now)
	if request.rtype == "read_req":
		request.set_startTime(env.now)
		env.process(readEvent(request,hierarchy,logger,env,links))
	elif request.rtype == "send_data":
		env.process(SendEvent(request,hierarchy,logger,env,links))
	elif request.rtype == "completion":
		env.process(CompletionEvent(request,hierarchy,logger,env,links))

		
def issueRequests(client,hierarchy,logger,env,links,reqNum):
	#if client._trace:
	if jobList:
		for i in range(int(reqNum)) :
			#obj=client._trace.pop(0)
			obj=jobList.pop(0)
			reqid=int(reqList.pop(0))
			path,destination,source=[],[],[]
			#reqid +=1
	                destination.append(1)
	                destination.append(client._rackid)
			source=[0,client._rackid]
	                path = [[0,client._rackid]]
			req = Request(reqid,source,destination,obj,client._obj_size,"read_req",path,client,"")
	                req.set_time(0)
			generateEvent(req,hierarchy,logger,env,links)


def x(hierarchy,env):
	global algo_start
	for i in range(10):
		
		if (algo_start== False):
			yield env.timeout(100)
			algo_start =True
		else:
			yield env.timeout(50)
		shadow.set_cache_size(hierarchy,env)
		shadow.reset_counters(hierarchy,10)
		print "shadow"

def algo(hierarchy,env):
	for i in range (20):
		env.process(x(hierarchy,env))
		#shadow.set_cache_size(hierarchy,env)
#		yield env.timeout(10)
		




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
	hierarchy = build_d3n(config, logger)
	try:
    		os.remove("shadow.log")
    		os.remove("position")
	except OSError:
    		pass

	env = simpy.Environment()

	links = build_network(config,logger,env)
	jobList = [] 
	jobList=inputParser(config.get('Simulation', 'input'))
	logger.info('Running Simulation...')
	print "Running Simulation..."	
	
	# Instantiate a thread pool with N worker threads
        clientNum = int(config.get('Simulation', 'clientNum'))
        nodeNum = int(config.get('Simulation', 'nodeNum'))
        threadNum = int(config.get('Simulation', 'threadNum'))

	obj_size=utils.get_obj_size(config)
	clientList={}
	counter=0
	#trace=["a","b","d","a","f","h","b","ff","a","x","y","b","a","z","a","b","d"]
	#trace=["a", "b", "c", "d", "a", "b", "f","dd","ee","g","x"]
	trace=["a","b","c","a","b","a","d","c","a","b","c"]
	#trace=[]
#	jobList=[]
#	jobList.append(inputParser2(config.get('Simulation', 'input1')))
#	jobList.append(inputParser2(config.get('Simulation', 'input2')))
#	jobList.append(inputParser2(config.get('Simulation', 'input3')))
#	jobList.append(inputParser2(config.get('Simulation', 'input4')))
#	jobList.append(inputParser2(config.get('Simulation', 'input5')))
#	jobList.append(inputParser2(config.get('Simulation', 'input6')))
#	jobList.append(inputParser2(config.get('Simulation', 'input7')))
#	jobList.append(inputParser2(config.get('Simulation', 'input8')))
#	jobList.append(inputParser2(config.get('Simulation', 'input9')))
#	jobList.append(inputParser2(config.get('Simulation', 'input10')))
#	jobList.append(inputParser2(config.get('Simulation', 'input11')))
#	jobList.append(inputParser2(config.get('Simulation', 'input12')))
#	#jobList=[]
	#jobList=trace[:]
	for i in xrange(10000000):
		reqList.append(i+1)
	for i in range(nodeNum):
		for j in range(clientNum):
			clientList[counter]=Client(counter,i,trace,obj_size,threadNum)	
			counter+=1	
	#for i in clientList.keys():
	#	print i, clientList[i]._trace
	print "Input file is read"
#	jobList=[]
#	jobList.append(inputParser2(config.get('Simulation', 'input')))	
	pool = multiThread.ThreadPool(clientNum)
	for key in clientList.keys():
		pool.add_task(issueRequests, clientList[key],hierarchy,logger,env,links,threadNum)
	pool.wait_completion()

	env.process(x(hierarchy,env))
	
	env.run()

	#test_cache(jobList,hierarchy)	

 	logger.info("Simulation Ends")
 	logger.info("Collecting Statistics...")
	print "Simulation Ends"
	print "Collecting Statistics..."	
	
	#utils.cacheinfo2(hierarchy)
	stats={}
	stats["rn"]=sim_req_num
	stats["clist"]=sim_req_comp
	stats["sim_end"]=sim_end


	res_file=config.get('Simulation', 'res_file')
	fd = open(res_file,"a")
	fd.write("\n\n")
	fd.write("-------------RESULTS---------------------\n")
	fd.write("Date:"+time+"\n")
	utils.stats(hierarchy,config,fd,stats)	
	utils.missCost(hierarchy,config,fd)	
	
	fd.close()




#	shadow.set_cache_size(hierarchy,env)
#	shadow.reset_counters(hierarchy,nodeNum)

#	shadow.set_cache_size(hierarchy,env)

