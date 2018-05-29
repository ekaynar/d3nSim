import multiThread
import numpy as np
class Client:


	def __init__(self, id, rackid, trace,obj_size, threadNum):
		self._id = id
		self._rackid= rackid
		self._trace = trace[:]
		self._obj_size = obj_size
		self._pool = multiThread.ThreadPool(1) 
		self._fname = str(id)
		#self._jlist = np.asarray(self._trace)

	def _log1(self,line):
		f = open(self._fname,"a")
		f.write(line)
		f.close()






