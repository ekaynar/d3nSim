from cache import Cache
import ConfigParser, cache, argparse, logging, pprint
import re
import numpy as np
from uhashring import HashRing
import loadDistribution
import multiThread
from client import Client
from request import Request
import time
import simpy
from threading import Thread
from inputParser import inputParser
cephLayer=3




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
	shadow_size =  int(config.get('Simulation', 'shadow_size'))
	if (hashType == "consistent"):
		hr = loadDistribution.consistentHashing(numNodes)	
	elif (hashType == "rendezvous"):
		hr = loadDistribution.consistentHashing(numNodes)	
	caches_l1,caches_l2, backend= {},{},{}
	if config.get('Simulation', 'L1') == "true" :
		cephLayer=2
		for i in range(numNodes):
			name = "1-"+str(i)
			caches_l1[i]=build_cache(config, name, 'L1', hr, hashType, shadow_size,logger) 
			hierarchy[name]=caches_l1[i]
	if config.get('Simulation', 'L2') == "true" :
		cephLayer=3
		for i in range(numNodes):
			name = "2-"+str(i)
			caches_l2[i]=build_cache(config, name, 'L1', hr, hashType,shadow_size, logger)
			hierarchy[name]=caches_l2[i]

	backend=build_cache(config, name, 'BE', hr, hashType, shadow_size,logger)
	name = str(cephLayer)+"-0"
	hierarchy[name]=backend	


	return hierarchy
def build_cache(config, name, layer, hr, hashType, shadow_size,logger):
	obj_size=get_obj_size(config)
	match=""
	match = re.match(r"([0-9]+)([a-z]+)", config.get('Simulation', 'L1_size'), re.I)
	if match:
		items = match.groups()
		if items[1] =="G" or items[1] =="g":
			size=(int(items[0])*1024*1024*1024/obj_size)
		elif  items[1] =="M" or items[1] =="m":
			size=(int(items[0])*1024*1024/obj_size)
	return cache.Cache(layer,size , config.get('Simulation', 'L1_rep') , "WT", hr, hashType, obj_size,shadow_size,logger)

def display(*arg):
	env=arg[0]
	request=arg[1]
	if len(arg)>2:
		info=arg[2]
	else:
		info=""
	out = ""
	if str(request.rtype) == "read_req":
		out = "time:"+str(env.now)+" Client:"+str(request.client._id)+" Requested:"+str(request.dest)+" "+info +" ReqId:"+str(request.reqId)+" key:"+str(request.key)+" size:"+str(request.size)+" from:"+str(request.source)+" to:"+str(request.dest)+" path:"+str(request.path)
		print out
	if str(request.rtype) == "send_data":
		out = "time:"+str(env.now)+" Received:"+str(request.dest)+" "+info+" ReqId:"+str(request.reqId)+" key:"+str(request.key)+" size:"+str(request.size)+" from:"+str(request.source)+" to:"+str(request.dest)+" path:"+str(request.path)
		print out
	if str(request.rtype) == "completion":
		out = "time:"+str(env.now)+" Completion:"+str(request.dest)+" ReqId:"+str(request.reqId)+" key:"+str(request.key)+" size:"+str(request.size)
		print out


def cacheinfo(hierarchy):
	for key in hierarchy.keys():
		print"Shadow", key,hierarchy[key].shadow_cache
		print "Actual", key,hierarchy[key].cache

def cacheinfo2(hierarchy):
	cacheId="3-0"
	print cacheId, hierarchy[cacheId].cache, "Shadow:",hierarchy[cacheId].shadow_cache,"---", hierarchy[cacheId].base, hierarchy[cacheId].plus, hierarchy[cacheId].minus,"---", "Size:",hierarchy[cacheId].cache.get_size() #, "Space:", hierarchy[cacheId].spaceLeft
	for i in range(2,-1,-1):
		print""""-------Rack #"""+str(i)+"-------"
		for j in range(2,0,-1):
			cacheId=str(j)+"-"+str(i) 
			print cacheId, hierarchy[cacheId].cache, "Shadow:",hierarchy[cacheId].shadow_cache,"---", hierarchy[cacheId].base, hierarchy[cacheId].plus, hierarchy[cacheId].minus,"---", "Size:",hierarchy[cacheId].cache.get_size()
# "Space:", hierarchy[cacheId].spaceLeft


def set_cache_size(hierarchy,env):

	layerNum=2
	rackNum =  (len(hierarchy)-1)/layerNum
	print "--------------------"
	for i in range(rackNum):
		caches=[]
		for j in xrange(1,layerNum+1,1):
			cacheId1=str(j)+"-"+str(i)
		 	caches.append(cacheId1)
		if (hierarchy[caches[0]].plus > hierarchy[caches[1]].minus):	
			print "Add to " ,caches[0]
			hierarchy[caches[0]].set_cache_size(1)	
			hierarchy[caches[1]].set_cache_size(-1)
			#print hierarchy[caches[0]].cache.get_size()	
			#print hierarchy[caches[1]].cache.get_size()	
		elif (hierarchy[caches[1]].plus > hierarchy[caches[0]].minus):	
			print "Add to " ,caches[1]
			hierarchy[caches[0]].set_cache_size(-1)	
			hierarchy[caches[1]].set_cache_size(1)	
			#print hierarchy[caches[0]].cache.get_size()	
			#print hierarchy[caches[1]].cache.get_size()	
		else:
			print "no Changes"	




def readEvent(request,hierarchy,logger,env,links):
	cacheId = str(request.dest[0])+"-"+str(request.dest[1])
	r = hierarchy[cacheId].read(request.key,request.size)
	yield env.timeout(0)
	
	# If it is a Hit
	if r:
		display(env,request,"Hit")
		source = [ request.dest[0],request.dest[1] ]
		dest = request.path.pop()
		if dest[0]==0:
			source =  [ request.dest[0], request.dest[1] ]
                	req = Request(request.reqId,source,dest,request.key,request.size,"completion",request.path,request.client)
                	generateEvent(req,hierarchy,logger,env,links)
		else:
			req = Request(request.reqId,source,dest,request.key,request.size,"send_data",request.path,request.client)
                	generateEvent(req,hierarchy,logger,env,links)
			
	else:
		# Miss on Layer
		display(env,request,"Miss")
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
			req = Request(request.reqId,source,dest,request.key,request.size,"read_req",path,request.client)
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
		display(env,request,"From Ceph")
		size = float(request.size)/float(obj_size)
		hierarchy[cacheId]._insert(request.key,size)
	elif (request.source[1] != request.dest[1]):
		display(env,request,"Remote L2")
		size = float(request.size)/float(obj_size)
		hierarchy[cacheId]._insert(request.key,size)
	else:
		display(env,request,"Local L2")
	
	#print "time:"+str(env.now),"Data is received:"+str(request.dest), "ReqId:"+str(request.reqId),"key:"+request.key,"size:"+ "from:",request.source,"to:" ,request.dest, "path", request.path
	
	dest = request.path.pop()
	if dest[0]==0:
		source =  [ request.dest[0], request.dest[1] ] 
       		req = Request(request.reqId,source,dest,request.key,request.size,"completion",request.path,request.client)
                #env.process(generateEvent(req,hierarchy,logger,env,links))
                generateEvent(req,hierarchy,logger,env,links)
	else:
		source = [ request.dest[0], request.dest[1] ]
		req = Request(request.reqId,source,dest,request.key,request.size,"send_data",request.path,request.client)
                #env.process(generateEvent(req,hierarchy,logger,env,links))
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


	display(env,request)
#	cacheinfo(hierarchy)
	issueRequests(request.client,hierarchy,logger,env,links,1)
def generateEvent(request,hierarchy,logger,env,links):
#	yield env.timeout(request.arrTime)
	cacheId = str(request.dest[0])+"-"+str(request.dest[1])
	request.set_time(env.now)
	if request.rtype == "read_req":
		env.process(readEvent(request,hierarchy,logger,env,links))
	elif request.rtype == "send_data":
		env.process(SendEvent(request,hierarchy,logger,env,links))
	elif request.rtype == "completion":
		env.process(CompletionEvent(request,hierarchy,logger,env,links))

		
def collect_stats(hierarchy,links):
	for i in hierarchy:
		print "Cache Name", i
		#print hierarchy[i].cache
		print "Hit Count" , hierarchy[i].get_hit_count()
		print "Miss Count", hierarchy[i].get_miss_count()
		print "Intrarack BW", hierarchy[i].get_intrarack_bw()
		print "Crossrack BW", hierarchy[i].get_crossrack_bw()
		print "Backend BW", hierarchy[i].get_backend_bw()


	for i in sorted(links.keys()):
		print i
def issueRequests(client,hierarchy,logger,env,links,reqNum):
	if client._trace:
		counter=0	
		for i in range(int(reqNum)) :
			obj=client._trace.pop(0)
			path,destination,source=[],[],[]
			counter +=1
	                destination.append(1)
	                destination.append(client._rackid)
			arrTime = 0
			source=[0,client._rackid]
	                path = [[0,client._rackid]]
			req = Request(counter,source,destination,obj,client._obj_size,"read_req",path,client)
	                req.set_time(arrTime)
			generateEvent(req,hierarchy,logger,env,links)
	else:
		print "Finished Client:"+str(client._id)

def get_obj_size(config):
	match = re.match(r"([0-9]+)([a-z]+)", config.get('Simulation', 'obj_size'), re.I)
        if match:
                items = match.groups()
                if items[1] =="M" or items[1] =="m":
                        obj_size=(int(items[0])*1024*1024)
	return obj_size

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='Simulate a cache')
    	parser.add_argument('-c','--config-file', help='Configuration file for the memory heirarchy', required=True)
	arguments = vars(parser.parse_args())
	
        config_file = arguments['config_file']		
	config = ConfigParser.ConfigParser()
	config.readfp(open(config_file))
	
	log_filename = 'simulator.log'
	if config.get('Simulation', 'log_file'):
		log_file = config.get('Simulation', 'log_file')
	
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


	logger.info('Running Simulation...')
	print "Running Simulation..."	
	env = simpy.Environment()

	links = build_network(config,logger,env)
	jobList = [] 
	fin = config.get('Simulation', 'input')
	#jobList=inputParser(fin)
	
	# Instantiate a thread pool with N worker threads
        clientNum = int(config.get('Simulation', 'clientNum'))
        nodeNum = int(config.get('Simulation', 'nodeNum'))
        threadNum = int(config.get('Simulation', 'threadNum'))

	obj_size=get_obj_size(config)
	
	clientList={}
	counter=0
	#trace=["a", "b", "c", "d", "a", "b", "f","dd","ee","g","x"]
	trace=["a","b","d","a"]
	for i in range(nodeNum):
		for j in range(clientNum):
			clientList[counter]=Client(counter,i,trace,obj_size,threadNum)	
			counter+=1	
	for i in clientList.keys():
		print i, clientList[i]._trace
	
	pool = multiThread.ThreadPool(3)
	for key in clientList.keys():
		pool.add_task(issueRequests, clientList[key],hierarchy,logger,env,links,1)
	pool.wait_completion()


	env.run()
 	print "Simulation Ends"
	print "Collecting Statistics..."	

	cacheinfo2(hierarchy)

	set_cache_size(hierarchy,env)
	cacheinfo2(hierarchy)
