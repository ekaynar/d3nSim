from lru import LRU
from collections import deque
import random

class Cache:

	"""Class representing D3N."""


	# Replacement policies
    	LRU = "LRU"
    	LFU = "LFU"
    	FIFO = "FIFO"
    	RAND = "RAND"

	# Write policies
	WRITE_BACK = "WB"
	WRITE_THROUGH = "WT"

	# Layer
	L1 = "L1"
	L2 = "L2"

	consistent = "consistent"	
	rendezvous = "rendezvous"	

	def __init__(self, layer, size, replace_pol, write_pol, hash_ring, hash_type, logger):
        	self._replace_pol = replace_pol  # Replacement policy
        	self._write_pol = write_pol  # Write policy
		self._layer = layer # Layer info
		self._size = size # Cache size
		self.spaceLeft = size # Cache size
		self._logger = logger
		self.hashmap = {} # Mapping
		self.hit_count = 0
		self.miss_count = 0
		self.hash_ring = hash_ring
		self._hash_type = hash_type
	
		if (self._replace_pol == Cache.LRU):
			self.cache = LRU(self._size)		
		elif (self._replace_pol == Cache.FIFO):
			self.cache = deque()		
		elif (self._replace_pol == Cache.LFU):
			self.cache = deque()		
		

	def _insert(self, key, size):
		# No eviction
		if (int(size) <= self.spaceLeft):
			if (self._replace_pol == Cache.LRU):
				self.cache[key]=int(size)
			elif (self._replace_pol == Cache.FIFO):
                        	self.cache.append(key)
			self.hashmap[key] = int(size)
			self.spaceLeft -= int(size)
		else:
			while(int(size) > self.spaceLeft):
				self._evict()
			if (self._replace_pol == Cache.LRU):
                                self.cache[key]=int(size)
                        elif (self._replace_pol == Cache.FIFO):
                                self.cache.append(key)
                        self.hashmap[key] = int(size)
                        self.spaceLeft -= int(size)	
	
	
	def read(self, key, size):
		"""Read a object from the cache."""
		r = None
		if key in self.hashmap:
			if (self._replace_pol == Cache.LRU):
                        	self._update_use(key)
			self.hit_count+=1
			r = 1
		else:
			self.miss_count+=1
			self._insert(key, size)

		return r

	def _evict(self):
		if (self._replace_pol == Cache.LRU):
			id = self.cache.peek_last_item()[0]
			del self.cache[id]
		elif (self._replace_pol == Cache.FIFO):		
			id = self.cache.popleft()
		self.spaceLeft += int(self.hashmap[id])
		del self.hashmap[id]
		

	def _update_use(self, key):
		"""Update the use of a cache."""
		if (self._replace_pol == Cache.LRU):
			self.cache[key]= self.hashmap[key]

	       
	def get_hit_count(self):
		return self.hit_count
	
	def get_miss_count(self):
		return self.miss_count
	
	def get_available_space(self):
		return self.spaceLeft  
	
	def get_replace_poll(self):
                return self._replace_pol

	def print_cache(self):
		print self.cache

	def get_l2_address(self,key):
		if (self._hash_type == Cache.consistent):
			return self.hash_ring.get_node(key)	
		elif (self._hash_type == Cache.rendezvous):
			return self.hash_ring.find_node(key)	
			