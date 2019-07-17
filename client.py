import multiThread
import numpy as np
from collections import deque
class Client:


	def __init__(self, id, rackid, trace,obj_size, threadNum):
		self._id = id
		self._rackid= rackid
		self._trace = deque(trace)
		self._obj_size = obj_size
		self._pool = multiThread.ThreadPool(1) 
		self._fname = str(id)
		#self._jlist = np.asarray(self._trace)
		self.ave_latency = 0
		self.request_count = 0
	def _log1(self,line):
		f = open(self._fname,"a")
		f.write(line)
		f.close()
	





