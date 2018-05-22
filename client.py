import multiThread

class Client:


	def __init__(self, id, rackid, trace,obj_size, threadNum):
		self._id = id
		self._rackid= rackid
		self._trace = trace[:]
		self._obj_size = obj_size
		self._pool = multiThread.ThreadPool(2) 
		self._fname = str(id)

	def _log1(self,line):
		f = open(self._fname,"a")
		f.write(line)
		f.close()






