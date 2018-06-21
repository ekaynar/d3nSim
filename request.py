class Request:
	

	def __init__(self,reqId, source,dest,key,size,rtype,path,client,layer):
		self.reqId=reqId
		self.source=source
		self.dest = dest
		self.key=key
		self.size=size
		self.rtype = rtype
		self.path = path
		self.client = client
		self.startTime = 0
		self.endTime = 0
		self.compTime = 0
		self.fetch = layer
		self.info = None
	def set_startTime(self,time):
                self.startTime = time
	def set_endTime(self,time):
                self.endTime = time
	def set_compTime(self,time):
                self.compTime = time
	def set_info(self,info):
                self.info = info
	def set_source(self,source):
		self.source = source
	def set_fetch(self,layer):
		self.fetch = layer
	def set_destination(self,dest):
		self.dest = dest
	def get_source(self):
		return self.source 
	def get_compTime(self):
		return self.compTime
	def get_fetch(self):
		return self.fetch
	def get_destination(self):
		return self.dest 
	def get_info(self):
                return self.info



