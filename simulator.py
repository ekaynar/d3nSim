from cache import Cache
import ConfigParser, cache, argparse, logging, pprint
import re
import numpy as np
from uhashring import HashRing
import loadDistribution
import multiThread
import random
from random import randrange
import time
def build_d3n(config, logger):
	#Build the cache hierarchy with the given configuration
	hierarchy = {}
	numNodes = int(config.get('Simulation', 'nodeNum'))
	hashType =  config.get('Simulation', 'hashType')
	if (hashType == "consistent"):
		hr = loadDistribution.consistentHashing(numNodes)	
	elif (hashType == "rendezvous"):
		hr = loadDistribution.consistentHashing(numNodes)	
	caches_l1,caches_l2= {},{}
	if config.get('Simulation', 'L1') == "true" :
		for i in range(numNodes):
			name = "layer1-"+str(i)
			caches_l1[i]=build_cache(config, name, 'L1', hr, hashType, logger) 
			hierarchy[name]=caches_l1[i]
	if config.get('Simulation', 'L2') == "true" :
		for i in range(numNodes):
			name = "layer2-"+str(i)
			caches_l2[i]=build_cache(config, name, 'L1', hr, hashType, logger)
			hierarchy[name]=caches_l2[i]

	return hierarchy
def build_cache(config, name, layer, hr, hashType, logger):
	match = re.match(r"([0-9]+)([a-z]+)", config.get('Simulation', 'L1_size'), re.I)
	if match:
		items = match.groups()
		if items[1] =="G" or items[1] =="g":
			size=int(items[0])
		elif  items[1] =="M" or items[1] =="m":
			size=(items[0]*1024*1024)
	return cache.Cache(layer,size , config.get('Simulation', 'L1_rep') , "WT", hr, hashType, logger)


def read(node,key,size,hierarchy,logger):
	name = "layer1-"+str(node)
#	print "arguments",node,key,size
	r = hierarchy[name].read(key,size)
	if r:
		out = name+" Hit,"+key+","+str(size)
		#logger.info(name+" Hit,"+key+","+str(size))
		logger.info(out)
	else:
		#logger.info(name+" Miss,"+key+","+str(size))
		out = name+" Miss,"+key+","+str(size)
		logger.info(out)
		l2_add = hierarchy[name].get_l2_address(key)
		print node,l2_add,key,time.clock(),"\n"
		if (int(l2_add) == int(node)) :
			hierarchy[name].set_intrarack_bw(1)
		else:
			hierarchy[name].set_crossrack_bw(1)
		
		name = "layer2-"+str(l2_add)
		r = hierarchy[name].read(key,size)
		if r:
			out = name+" Hit,"+key+","+str(size)
			logger.info(out)
		else:
			hierarchy[name].set_backend_bw(1)
			out = name+" Miss,"+key+","+str(size)+", Fetch from backend"
			logger.info(out)
			
def collect_stats(hierarchy):
	for i in hierarchy:
		print "Cache Name", i
		#print hierarchy[i].cache
		print "Hit Count" , hierarchy[i].get_hit_count()
		print "Miss Count", hierarchy[i].get_miss_count()
		print "Intrarack BW", hierarchy[i].get_intrarack_bw()
		print "Crossrack BW", hierarchy[i].get_crossrack_bw()
		print "Backend BW", hierarchy[i].get_backend_bw()



if __name__ == '__main__':
	#input_file = config.get('section', 'input_file')
	parser = argparse.ArgumentParser(description='Simulate a cache')
    	parser.add_argument('-c','--config-file', help='Configuration file for the memory heirarchy', required=True)
    	parser.add_argument('-p', '--pretty', help='Use pretty colors', required=False, action='store_true')
	arguments = vars(parser.parse_args())

	if arguments['pretty']:
        	import colorer
	
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
	hierarchy = build_d3n(config, logger)
#	print hierarchy

	logger.info('Running Simulation...')

	# Instantiate a thread pool with N worker threads
	pool = multiThread.ThreadPool(8)
	trace=["a", "b", "c", "d", "a", "b", "f","dd","ee","g","x"]
	def wait_delay(d):
		read(d[0],d[1],d[2],d[3],d[4])
	tasks=[]
	for i in trace:
#		read(0,i,1,hierarchy,logger)
		rand= random.randint(0, 2)
#		tasks.append([rand,i,1,hierarchy,logger])
		pool.add_task(read,rand,i,1,hierarchy,logger)
	#pool.map(wait_delay,tasks)
	pool.wait_completion()

	trace = ["a", "b", "c"]
	for i in trace:
		read(2,i,1,hierarchy,logger)

	print "********************"
	collect_stats(hierarchy)

