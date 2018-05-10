class Request:
	

	def __init__(self,reqId, source,dest,key,size,rtype,path):
		self.reqId=reqId
		self.source=source
		self.dest = dest
		self.key=key
		self.size=size
		self.arrTime=0
		self.layer=0
		self.rtype = rtype
		self.path = path
     
	def set_time(self,time):
                self.arrTime = time
	def set_source(self,source):
		self.source = source
	def set_destination(self,dest):
		self.dest = dest
	def get_source(self):
		return self.source 
	def get_destination(self):
		return self.dest 
	def get_time(self):
		return self.arrTime



