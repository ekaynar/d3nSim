import datetime
from cache import Cache
import ConfigParser, cache, argparse, logging, pprint
import numpy as np
from uhashring import HashRing
import loadDistribution
import multiThread
from client import Client
from request import Request
import time
import simpy
import utils
from threading import Thread
from inputParser import inputParser
cephLayer=3
reqList,jobList=[],[]

L1_lat_count=0
L2_lat_count=0
L1_miss_lat=0
L2_miss_lat=0

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




def readEvent(request,hierarchy,logger,env,links):
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
		if 1:
			path,source,dest=[],[],[]
			dest.append(int(request.dest[0])+1)
                        if int(request.dest[0])+1 == 3:
				dest.append(0)
			else:
				dest.append(int(hierarchy[cacheId].get_l2_address(request.key)))
                        
			source = request.dest
			path = request.path[:]
			path.append( [ request.dest[0],request.dest[1] ] )
			req = Request(request.reqId,source,dest,request.key,request.size,"read_req",path,request.client,request.get_fetch())
			req.set_startTime(request.startTime)
			req.set_endTime(request.endTime)
			generateEvent(req,hierarchy,logger,env,links)


def writelogs(env,logger,req,option):
	out = "time:"+str(env.now)+" "+option+" ReqId:"+str(req.reqId) +" key:"+req.key+" size:"+str(req.size)
	logger.info(out)
	return out

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

	#cacheinfo2(hierarchy)	
	sLinkId,dLinkId = findLinkId(request.source, request.dest)
	if (request.source[0]==2 and request.dest[0]==1 and request.source[1]==request.dest[1]):
		yield env.timeout(0)	
	else:

		# Get the required amount of Bandwidth
		if sLinkId: 
			yield links[sLinkId].get(links[sLinkId].capacity)
			latency = float(request.size) / links[sLinkId].capacity
		if dLinkId:
			yield links[dLinkId].get(links[dLinkId].capacity)
			latency = float(request.size) / links[dLinkId].capacity
	
		# The "actual" refueling process takes some time
		yield env.timeout(latency)
	
	
		# Put the required amount of Bandwidth
		if sLinkId:
			yield links[sLinkId].put(links[sLinkId].capacity)
		if dLinkId:
			yield links[dLinkId].put(links[dLinkId].capacity)
		
	cacheId = str(request.dest[0])+"-"+str(request.dest[1])
	if (request.source[0] == cephLayer):
		utils.display(env,logger,request,"From Ceph")
		size = float(request.size)/float(obj_size)
		hierarchy[cacheId]._insert(request.key,size)
	elif (request.source[1] != request.dest[1]):
		utils.display(env,logger,request,"Remote L2")
		size = float(request.size)/float(obj_size)
		hierarchy[cacheId]._insert(request.key,size)
	else:
		utils.display(env,logger,request,"Local L2")
	
	dest = request.path.pop()
	if dest[0]==0:
		source =  [ request.dest[0], request.dest[1] ] 
       		req = Request(request.reqId,source,dest,request.key,request.size,"completion",request.path,request.client,request.get_fetch())
		req.set_startTime(request.startTime)
		req.set_endTime(request.endTime)
		generateEvent(req,hierarchy,logger,env,links)
	else:
		source = [ request.dest[0], request.dest[1] ]
		req = Request(request.reqId,source,dest,request.key,request.size,"send_data",request.path,request.client,request.get_fetch())
		req.set_startTime(request.startTime)
		req.set_endTime(request.endTime)
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
	sim_req_num = request.reqId
	global  sim_req_comp
	sim_req_comp.append(request.get_compTime())
	global  sim_end
	sim_end = env.now
	global  L1_miss_lat
	global  L2_miss_lat
	global  L1_lat_count
	global  L2_lat_count
	if(int( request.fetch.split("-")[0]) == 2) or (int( request.fetch.split("-")[0]) == 3 ):
		L1_miss_lat+=float(request.get_compTime())
		L1_lat_count+=1
	if (int( request.fetch.split("-")[0]) == 3 ):
		L2_miss_lat+=float(request.get_compTime())
		L2_lat_count+=1
	utils.display(env,logger,request)
	#utils.cacheinfo2(hierarchy)
	issueRequests(request.client,hierarchy,logger,env,links,1)
def generateEvent(request,hierarchy,logger,env,links):
#	yield env.timeout(request.arrTime)
	cacheId = str(request.dest[0])+"-"+str(request.dest[1])
	request.set_time(env.now)
	request.set_startTime(env.now)
	if request.rtype == "read_req":
		env.process(readEvent(request,hierarchy,logger,env,links))
	elif request.rtype == "send_data":
		env.process(SendEvent(request,hierarchy,logger,env,links))
	elif request.rtype == "completion":
		env.process(CompletionEvent(request,hierarchy,logger,env,links))

		
def issueRequests(client,hierarchy,logger,env,links,reqNum):
	#if client._trace:
	if jobList:
	#	reqid=0	
		for i in range(int(reqNum)) :
			#obj=client._trace.pop(0)
			obj=jobList.pop(0)
			reqid=int(reqList.pop(0))
	#		print obj
			path,destination,source=[],[],[]
	#		reqid +=1
	                destination.append(1)
	                destination.append(client._rackid)
			arrTime = 0
			source=[0,client._rackid]
	                path = [[0,client._rackid]]
			req = Request(reqid,source,destination,obj,client._obj_size,"read_req",path,client,"")
	                req.set_time(arrTime)
			generateEvent(req,hierarchy,logger,env,links)
	else:
		print "Finished Client:"+str(client._id)

def cost(cache1,cache2,l1_pos,l2_pos,L1_lat,L2_lat,size):
	mc_l1=mc_l2=0
	for i in range(l1_pos+1,size):
		mc_l1+=cache1.hist[i]
	
	for i in range(l2_pos,size):
		mc_l2+=cache2.hist[i]

	res = (mc_l1*L1_lat) + (mc_l2*L2_lat)
#	print l1_pos,l2_pos
#	print mc_l1,mc_l2
#	print res
	return res


def set_cache_size(hierarchy,env):
	layers=2
	racknum=3
	cache_1=cache_2=""
	for i in range(racknum):
		min_cost=None
		l1_pos=l2_pos=0
                print""""-------Rack #"""+str(i)+"-------"
                cache_1="1-"+str(i)
                cache_2="2-"+str(i)
		size = len(hierarchy[cache_1].hist)-1
		for i in range(size):
			print hierarchy[cache_1].hist, hierarchy[cache_2].hist
			res = cost(hierarchy[cache_1],hierarchy[cache_2],i,size-i,1,1,size)
			if min_cost != None:
				#print "more",min_cost
				if ( res < min_cost):
					min_cost = res
					l1_pos = i
					l2_pos = size-i
			else:
				#print "first",min_cost
				min_cost=res
				l1_pos = i
				l2_pos = size-i
       		print min_cost,l1_pos,l2_pos

def reset_counters():
	return 0

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


	env = simpy.Environment()

	links = build_network(config,logger,env)
#	jobList = [] 
	fin = config.get('Simulation', 'input')
	jobList=inputParser(fin)
	
	
	logger.info('Running Simulation...')
	print "Running Simulation..."	
	
	# Instantiate a thread pool with N worker threads
        clientNum = int(config.get('Simulation', 'clientNum'))
        nodeNum = int(config.get('Simulation', 'nodeNum'))
        threadNum = int(config.get('Simulation', 'threadNum'))

	obj_size=utils.get_obj_size(config)
	
	clientList={}
	counter=0
	trace=["a","b","d","a","f","h","b","ff","a","x","y","b","a","z","a","b","d"]
	#trace=["a", "b", "c", "d", "a", "b", "f","dd","ee","g","x"]
	#jobList=trace[:]
	for i in xrange(len(jobList)):
		reqList.append(i+1)
	#print jobList,reqList
	for i in range(nodeNum):
		for j in range(clientNum):
			clientList[counter]=Client(counter,i,trace,obj_size,threadNum)	
			counter+=1	
	#for i in clientList.keys():
	#	print i, clientList[i]._trace
	
	pool = multiThread.ThreadPool(clientNum)
	for key in clientList.keys():
		pool.add_task(issueRequests, clientList[key],hierarchy,logger,env,links,threadNum)
	pool.wait_completion()


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


	res_file=config.get('Simulation', 'res_file')
	fd = open(res_file,"a")
	fd.write("Date:"+str(datetime.datetime.now()))
	utils.stats(hierarchy,config,fd,stats)	
	
	fd.close()	
	print L1_miss_lat, L1_lat_count, L2_miss_lat,L2_lat_count
#	set_cache_size(hierarchy,env)

