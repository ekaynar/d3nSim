import collections
import re

def get_cache_size(config,obj_size,name):
	size=0
	match=""
        match = re.match(r"([0-9]+)([a-z]+)", config.get('Simulation', name), re.I)
        if match:
                items = match.groups()
                if items[1] =="G" or items[1] =="g":
                        size=(int(items[0])*1024*1024*1024/obj_size)
                elif  items[1] =="M" or items[1] =="m":
                        size=(int(items[0])*1024*1024/obj_size)

        return size
def get_obj_size(config):
        match = re.match(r"([0-9]+)([a-z]+)", config.get('Simulation', 'obj_size'), re.I)
        if match:
                items = match.groups()
                if items[1] =="M" or items[1] =="m":
                        obj_size=(int(items[0])*1024*1024)
        return obj_size

def get_link_id(source,dest):
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

def add_cache_request_time(cache,time,request):
	cache.request_list[request.reqId]=time	


def get_latency(request, cache, time):
	cache.miss_lat += (time - cache.request_list[request.reqId])
	cache.lat_count += 1
	print request.reqId, (time - cache.request_list[request.reqId])

def display(*arg):
        env=arg[0]
	logger=arg[1]
        request=arg[2]
        if len(arg)>3:
                info=arg[3]
        else:
                info=""
        out = ""
        if str(request.rtype) == "read_req":
                out = "time:"+str(env.now)+" Client:"+str(request.client._id)+" Requested:"+str(request.dest)+" "+info +" ReqId:"+str(request.reqId)+" key:"+str(request.key).replace("\n","")+" size:"+str(request.size)+" from:"+str(request.source)+" to:"+str(request.dest)+" path:"+str(request.path)
                #print out
		logger.info(out)
        if str(request.rtype) == "send_data":
                out = "time:"+str(env.now)+" Received:"+str(request.dest)+" "+info+" ReqId:"+str(request.reqId)+" key:"+str(request.key).replace("\n","")+" size:"+str(request.size)+" from:"+str(request.source)+" to:"+str(request.dest)+" path:"+str(request.path)
                #print out
		logger.info(out)
        if str(request.rtype) == "completion":
                out = "time:"+str(env.now)+" Completion:"+str(request.dest)+" ReqId:"+str(request.reqId)+" key:"+str(request.key).replace("\n","")+" size:"+str(request.size) + "StartTime:"+str(request.startTime)+" EndTime:"+str(request.endTime)+" CompTime:"+str(request.compTime)+" Hit on:"+str(request.get_fetch()) + " Info:"+str(request.get_info()) + " L1 Miss ID:" + str(request.missLayer1) + " L2 Miss ID:" + str(request.missLayer2) 

                #print out
		logger.info(out)



def missCost(hierarchy,config,fd):
	RackNum=int(config.get('Simulation', 'nodeNum'))-1
	for i in range(RackNum,-1,-1):
		print""""-------Rack #"""+str(i)+"-------"
		for j in range(2,0,-1):
			cacheId=str(j)+"-"+str(i)
			out = str(cacheId) + "Miss Latenyc:"+ str(hierarchy[cacheId].miss_lat) + " Miss Count:" + str(hierarchy[cacheId].lat_count)
			print out
def stats(hierarchy,config,fd,stats):
	printSetupInfo(config,fd)
	printHitMissInfo(hierarchy,fd)
	printRequestInfo(fd,stats,config)
	cacheinfo2(hierarchy,config)
	fd.close()

def printSetupInfo(config,fd):
	fd.write("\nSetup Info\n")
	fd.write("-----------------------------------------------------\n")
	RackNum=int(config.get('Simulation', 'nodeNum'))
	policy=config.get('Simulation', 'L1_rep')
	LayerNum=0
	if (config.get('Simulation', 'L1') == 'true'):
		LayerNum+=1
	if (config.get('Simulation', 'L2') == 'true'):
		LayerNum+=1
	out = "# of Racks: "+str(RackNum)+"\n"
	fd.write(out)
	out = "# of Layers: "+str(LayerNum)+"\n"
	fd.write(out)
	out = "Cache Eviction Policy: "+policy+"\n"
	fd.write(out)
	out = "L1 size: "+config.get('Simulation', 'L1_size')+"\n"
	fd.write(out)
	out = "L2 size: "+config.get('Simulation', 'L2_size')+"\n"
	fd.write(out)
	fd.write("\nClient Info\n")
        fd.write("-----------------------------------------------------\n")
	out = "Parallel # of Req per client: "+config.get('Simulation', 'threadNum')+"\n"
	fd.write(out)
	fd.write("\nNetwork Info\n")
	fd.write("-----------------------------------------------------\n")
	out=config.get('Network', 'L1_In')
	fd.write("L1_In: "+out+"\n")
	out=config.get('Network', 'L1_Out')
	fd.write("L1_Out: "+out+"\n")
	out=config.get('Network', 'L2_In')
	fd.write("L2_In: "+out+"\n")
	out=config.get('Network', 'L2_Out')
	fd.write("L2_Out: "+out+"\n")
	fd.write("\n")	

def printHitMissInfo(hierarchy,fd):
	cache = collections.OrderedDict(sorted(hierarchy.items()))
	data,arr=[],[]
	headers=["Cache ID", "Hit Count", "Miss Count", "Miss Ratio"]
	data.append(headers)
	print "Cache Statistics"
	fd.write("Cache Statistics\n")
	print "-----------------------------------------------------"
	fd.write("-----------------------------------------------------\n")
	for key in cache.keys():
		arr.append(key)
		arr.append(str(cache[key]._hit_count))
		arr.append(str(cache[key]._miss_count))
		if (cache[key]._hit_count+cache[key]._miss_count) != 0:
			mr = float(cache[key]._miss_count)/(cache[key]._hit_count+cache[key]._miss_count)
			arr.append(str(mr))
		else:
			arr.append("0")	
		data.append(arr)
		arr=[]	


        widths = [max(map(len, col)) for col in zip(*data)]
        for row in data:
                print "  ".join((val.ljust(width) for val, width in zip(row, widths)))
                fd.write("  ".join((val.ljust(width) for val, width in zip(row, widths))))
                fd.write("\n")

def printRequestInfo(fd,stats,config):


	obj_size=get_obj_size(config)
	print "Request Statistics"
	fd.write("\nRequest Statistics\n")
	print "-----------------------------------------------------"
	fd.write("-----------------------------------------------------\n")
	out = "# of Request: "+str(stats["rn"])+"\n"
        fd.write(out)
	out = "Total Run Time: "+str(stats["sim_end"])+"\n"
        fd.write(out)
	sum=0
	for time in stats["clist"]:
		sum+=time
	print len(stats["clist"])
	out = "AVG Response Time: "+str(float(sum)/len(stats["clist"]))+"\n"
	fd.write(out)
	data = float(stats["count_w"])*obj_size/1024/1024
	out = "Processed Data: "+str(data)+" MB \n"
	fd.write(out)
	th =  data/(float(stats["sim_end"])-float(stats["warmup"]))
	out = "AVG Throughput: "+str(th)+" MB/s \n"
	
	fd.write(out)


def cacheinfo2(hierarchy,config):
	RackNum=int(config.get('Simulation', 'nodeNum'))-1
 	print""""-------Rack #"""+str(3)+"-------"

        cacheId="3-0"
	print cacheId, "Size",hierarchy[cacheId].cache.get_size(),hierarchy[cacheId]._replace_pol,hierarchy[cacheId]._hit_count, hierarchy[cacheId]._miss_count
        for i in range(RackNum,-1,-1):
                print""""-------Rack #"""+str(i)+"-------"
                for j in range(2,0,-1):
                        cacheId=str(j)+"-"+str(i)
                        #print cacheId, hierarchy[cacheId].cache, "Size",hierarchy[cacheId].cache.get_size(), "Shadow", hierarchy[cacheId].shadow,"Size:",hierarchy[cacheId].shadow.get_size()," Hist", hierarchy[cacheId].hist
                        print cacheId, "Size",hierarchy[cacheId].cache.get_size(),hierarchy[cacheId]._replace_pol,hierarchy[cacheId]._hit_count, hierarchy[cacheId]._miss_count
# "Space:", hierarchy[cacheId].spaceLeft
	
