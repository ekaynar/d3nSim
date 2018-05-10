from cache import Cache
import ConfigParser, cache, argparse, logging, pprint
import re
import numpy as np
from uhashring import HashRing
import loadDistribution
import multiThread
from request import Request
import random
from random import randrange
import time
import simpy

eventQueue=[]
BE_capacity=65
cephLayer=3


def build_network(config,logger,env):
	# 1 Gbps = 125 MB/s
	# 10 Gbps = 1250 MB/s
	# 40 Gbps = 5000 MB/s
	TOR_SIZE=1
	links={}
	numNodes = int(config.get('Simulation', 'nodeNum'))
        if config.get('Simulation', 'L1') == "true" :
                for i in range(numNodes):
			linkId = "L1in1r"+str(i)
                        links[linkId]=simpy.Container(env, TOR_SIZE, init=TOR_SIZE)
			linkId = "L1out0r"+str(i)
                        links[linkId]=simpy.Container(env, TOR_SIZE, init=TOR_SIZE)
	
	if config.get('Simulation', 'L2') == "true" :		
		for i in range(numNodes):
			linkId = "L2in1r"+str(i)
                        links[linkId]=simpy.Container(env, TOR_SIZE, init=TOR_SIZE)
			linkId = "L2out0r"+str(i)
                        links[linkId]=simpy.Container(env, TOR_SIZE, init=TOR_SIZE)

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
		for i in range(numNodes):
			name = "1-"+str(i)
			caches_l1[i]=build_cache(config, name, 'L1', hr, hashType, logger) 
			hierarchy[name]=caches_l1[i]
	if config.get('Simulation', 'L2') == "true" :
		for i in range(numNodes):
			name = "2-"+str(i)
			caches_l2[i]=build_cache(config, name, 'L1', hr, hashType, logger)
			hierarchy[name]=caches_l2[i]

	backend=build_cache(config, name, 'BE', hr, hashType, logger)
	name = "3-0"
	hierarchy[name]=backend	


	return hierarchy
def build_cache(config, name, layer, hr, hashType, logger):
	match = re.match(r"([0-9]+)([a-z]+)", config.get('Simulation', 'L1_size'), re.I)
	if match:
		items = match.groups()
		if items[1] =="G" or items[1] =="g":
			size=(int(items[0])*1024/4)
		elif  items[1] =="M" or items[1] =="m":
			size=(items[0]*1024*1024)
	return cache.Cache(layer,size , config.get('Simulation', 'L1_rep') , "WT", hr, hashType, logger)

def display(*arg):
	env=arg[0]
	request=arg[1]
	if len(arg)>2:
		info=arg[2]
	else:
		info=""
	out = ""
	if str(request.rtype) == "read_req":
		out = "time:"+str(env.now)+" Requested:"+str(request.dest)+" "+info +" ReqId:"+str(request.reqId)+" key:"+str(request.key)+" size:"+str(request.size)+" from:"+str(request.source)+" to:"+str(request.dest)+" path:"+str(request.path)
		print out
	if str(request.rtype) == "send_data":
		out = "time:"+str(env.now)+" Received:"+str(request.dest)+" "+info+" ReqId:"+str(request.reqId)+" key:"+str(request.key)+" size:"+str(request.size)+" from:"+str(request.source)+" to:"+str(request.dest)+" path:"+str(request.path)
		print out
	if str(request.rtype) == "completion":
		out = "time:"+str(env.now)+" Completion:"+str(request.dest)+" ReqId:"+str(request.reqId)+" key:"+str(request.key)+" size:"+str(request.size)
		print out


def readEvent(request,hierarchy,logger,env,links):
	cacheId = str(request.dest[0])+"-"+str(request.dest[1])
	r = hierarchy[cacheId].read(request.key,request.size)
	yield env.timeout(0)
	
	# If it is a Hit
	if r:
		display(env,request,"Hit")
		# writelogs(env,logger,request,"Hit "+str(cacheId))
		source = [ request.dest[0],request.dest[1] ]
		dest = request.path.pop()
		if dest[0]==0:
			source =  [ request.dest[0], request.dest[1] ]
                	req = Request(request.reqId,source,dest,request.key,request.size,"completion",request.path)
                	#env.process(generateEvent(req,hierarchy,logger,env,links))
                	generateEvent(req,hierarchy,logger,env,links)
		else:
			req = Request(request.reqId,source,dest,request.key,request.size,"send_data",request.path)
			#env.process(generateEvent(req,hierarchy,logger,env,links))
                	generateEvent(req,hierarchy,logger,env,links)
			
	else:
		# Miss on Layer
		display(env,request,"Miss")
		#writelogs(env,logger,request,"Miss "+str(cacheId))
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
			req = Request(request.reqId,source,dest,request.key,request.size,"read_req",path)
                        #env.process(generateEvent(req,hierarchy,logger,env,links))		
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
			yield links[sLinkId].get(1)
			latency = float(request.size) / links[sLinkId].capacity
		else:
			latency = float(request.size) / BE_capacity
		if dLinkId:
			yield links[dLinkId].get(1)
	
		#latency = request.size / 
		# The "actual" refueling process takes some time
		yield env.timeout(latency)
	
	
		# Put the required amount of Bandwidth
		if sLinkId:
			yield links[sLinkId].put(1)
		if dLinkId:
			yield links[dLinkId].put(1)
		
	cacheId = str(request.dest[0])+"-"+str(request.dest[1])
	if (request.source[0] == cephLayer):
		display(env,request,"From Ceph")
		hierarchy[cacheId]._insert(request.key,request.size)
	elif (request.source[1] != request.dest[1]):
		display(env,request,"Remote L2")
		hierarchy[cacheId]._insert(request.key,request.size)
	else:
		display(env,request,"Local L2")
	
	#print "time:"+str(env.now),"Data is received:"+str(request.dest), "ReqId:"+str(request.reqId),"key:"+request.key,"size:"+ "from:",request.source,"to:" ,request.dest, "path", request.path
	
	dest = request.path.pop()
	if dest[0]==0:
		source =  [ request.dest[0], request.dest[1] ] 
       		req = Request(request.reqId,source,dest,request.key,request.size,"completion",request.path)
                #env.process(generateEvent(req,hierarchy,logger,env,links))
                generateEvent(req,hierarchy,logger,env,links)
	else:
		source = [ request.dest[0], request.dest[1] ]
		req = Request(request.reqId,source,dest,request.key,request.size,"send_data",request.path)
                #env.process(generateEvent(req,hierarchy,logger,env,links))
                generateEvent(req,hierarchy,logger,env,links)


def CompletionEvent(request,hierarchy,logger,env,links):
	#linkId="0-"+str(request.dest[1])
	bw_required = request.size
	sLinkId,dLinkId = findLinkId(request.source, request.dest)
	
	if sLinkId:
                yield links[sLinkId].get(1)
		latency = float(request.size) / links[sLinkId].capacity
        if dLinkId:
		print "Error on Completion"
                #yield links[dLinkId].get(bw_required)
	
	yield env.timeout(latency)

	if sLinkId:
                yield links[sLinkId].put(1)
#	if dLinkId:
#		yield links[dLinkId].put(bw_required)	

	display(env,request)
#	out = "time:"+str(env.now)+" Completion:"+str(request.dest) +" ReqId:"+str(req.reqId) +" key:"+req.key+" size:"+str(req.size)
#	print out 
	
def generateEvent(request,hierarchy,logger,env,links):
#	yield env.timeout(request.arrTime)
	cacheId = str(request.dest[0])+"-"+str(request.dest[1])
	request.set_time(env.now)
	if request.rtype == "read_req":
		#env.process(readEvent(request,hierarchy,logger,env,links))
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
	
	# Instantiate a thread pool with N worker threads
	pool = multiThread.ThreadPool(8)
	trace=["a", "b", "c", "d", "a", "b", "f","dd","ee","g","x"]
	trace=["a","b"]
	tasks=[]
	counter = 0
	for key in trace:
		path,destination,source=[],[],[]
		counter +=1
		destination.append(1)
		num= random.randint(0, 2)
		destination.append(num)
		arrTime = random.randint(0, 3)
		arrTime = 0
		num=2
		source=[0,num]
		path = [[0,num]]
		size = 4	
		#arrTime = 2
		print key, arrTime
		#  def __init__(self,reqId, source,dest,key,size,rtype):
#		print arrTime,key,counter
		req = Request(counter,source,destination,key,size,"read_req",path)
		req.set_time(arrTime)
		generateEvent(req,hierarchy,logger,env,links)	
#		pool.add_task(read,i,rand,i,1,hierarchy,logger)
#	pool.wait_completion()
	#env.run(until=40)
	env.run()
 	print "Simulation Ends"
	trace = ["a", "b", "c","a"]
#	for i in trace:
#		read(i,2,i,1,hierarchy,logger)
	for i in eventQueue:
		print i.e_type,i.req.key	
	print "Collecting Statistics..."	
#	collect_stats(hierarchy,link)

	for i in hierarchy:
		print i, hierarchy[i].cache, hierarchy[i]._size, hierarchy[i].spaceLeft
