from cache import Cache
import ConfigParser, cache, argparse, logging, pprint
import re
import numpy as np
from uhashring import HashRing
import loadDistribution

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
		name = "layer2-"+str(l2_add)
		r = hierarchy[name].read(key,size)
		if r:
			out = name+" Hit,"+key+","+str(size)
			logger.info(out)
		else:
			out = name+" Miss,"+key+","+str(size)+", Fetch from backend"
			logger.info(out)
			


if __name__ == '__main__':
	#input_file = config.get('section', 'input_file')
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
	hierarchy = build_d3n(config, logger)
#	print hierarchy

	logger.info('Running Simulation...')

	trace=["a", "b", "c", "d", "a", "b", "f","dd","ee"]

	for i in trace:
		read(0,i,1,hierarchy,logger)
	trace = ["a", "b", "c"]
	for i in trace:
		read(2,i,1,hierarchy,logger)
#	read(0,"a",1,hierarchy,logger)
#	read(0,"a",1,hierarchy,logger)
#	read(0,"b",1,hierarchy,logger)
#	read(0,"e",1,hierarchy,logger)
#	read(1,"e",1,hierarchy,logger)
#	read(1,"a",1,hierarchy,logger)
#	read(2,"a",1,hierarchy,logger)

	print "********************"
	print hierarchy['layer1-0'].cache
	print hierarchy['layer1-1'].cache
	print hierarchy['layer1-2'].cache
	print hierarchy['layer2-0'].cache
	print hierarchy['layer2-1'].cache
	print hierarchy['layer2-2'].cache

	#print configs
	#logger = logging.getLogger()
    	#fh = logging.FileHandler(log_filename)
    	#sh = logging.StreamHandler()
    	#logger.addHandler(fh)
    	#logger.addHandler(sh)


	#while (command != "quit"):
    	#	operation = input("> ")
    	#	operation = operation.split()



#       cache = Cache("L1",30,"LRU","WT","a")
#       r=cache.read("a",10)
#       r=cache.read("a",10)
#       r=cache.read("b",10)
#       r=cache.read("c",10)
#       r=cache.read("d",10)
#       h=cache.get_hit_count()
#       m=cache.get_miss_count()
#       cache.print_cache()
#       print h,m
 #      cachefifo = Cache("L1",100,"FIFO","WT","a")
#       cachelfu = Cache("L1",100,"LFU","WT","a")

#       cachefifo.insert("c",10)
#       cachefifo.insert("d",10)
#       cachefifo.insert("e",10)
#       cachefifo.print_cache()

