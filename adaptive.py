import simplejson
def cost(cache1,cache2,l1_pos,l2_pos,L1_lat,L2_lat,size):
        mc_l1=mc_l2=0
        for i in range(l1_pos,size):
                mc_l1+=cache1.hist[i]

        for i in range(l2_pos,size):
                mc_l2+=cache2.hist[i]

        res = (mc_l1*L1_lat) + (mc_l2*L2_lat)
#       print l1_pos,l2_pos,L1_lat,L2_lat
#       print mc_l1,mc_l2, res
        return res




def set_cache_size(hierarchy,env,shadow_window,racknum):
        layers=2
        cache_1=cache_2=""
        for i in range(racknum):
                min_cost=None
                l1_pos=l2_pos=0
               # print""""-------Rack #"""+str(i)+"-------"
                cache_1="1-"+str(i)
                cache_2="2-"+str(i)
                size = len(hierarchy[cache_1].hist)
                if (hierarchy[cache_1].lat_count == 0):
                        hierarchy[cache_1].lat_count=1
                if (hierarchy[cache_2].lat_count == 0):
                        hierarchy[cache_2].lat_count=1
                l1_lat= float(hierarchy[cache_1].miss_lat)/float(hierarchy[cache_1].lat_count)
                l2_lat= float(hierarchy[cache_2].miss_lat)/float(hierarchy[cache_2].lat_count)
		current_s_l1 = hierarchy[cache_1].cache.get_size()
		current_s_l2 = hierarchy[cache_2].cache.get_size()
                for i in range(1,size):
              #          print hierarchy[cache_1].hist, hierarchy[cache_2].hist
			if ( current_s_l1-shadow_window <= i <= current_s_l1 +shadow_window):
	#			print "10thres",i,current_s_l1
                       		res = cost(hierarchy[cache_1],hierarchy[cache_2],i,size-i,l1_lat,l2_lat,size)
                        	if min_cost != None:
                                	#print "more",min_cost
                                	if ( res < min_cost):
                                        	min_cost = res
                                        	l1_pos = i
	                                        l2_pos = size-i
        	                else:
                	                #print "first",min_cost
                        	        min_cost=res
                               		l1_pos = i
	                                l2_pos = size-i
        	     #   print min_cost,l1_pos,l2_pos
	#	print cache_1, hierarchy[cache_1].cache.get_size(),l1_pos,cache_2, hierarchy[cache_2].cache.get_size(),l2_pos

		hierarchy[cache_1].cache.set_size(l1_pos)
		if ( int(current_s_l2) > int(l2_pos)):
			move2layer1(hierarchy[cache_1].cache,hierarchy[cache_2].cache,l1_pos,l2_pos)
		hierarchy[cache_2].cache.set_size(l2_pos)
		fd = open("position", "a")
        	fd.write(str(cache_1)+","+str(cache_2)+","+str(l1_pos)+","+ str(l2_pos)+","+str(env.now))
        	fd.write("\n")
        	fd.close()


	fd = open("position", "a")
        fd.write("------------------------------")
        fd.write("\n")
        fd.close()


def move2layer1(cache1,cache2,pos1,pos2):
	orig_size = cache2.get_size()
	keys =cache2.keys()[:]
	#print "insert", "l1",cache1.get_size(),"l2", orig_size ,  pos2, "keysize",len(keys)
	for i in range(pos2,len(keys)):
		cache1[keys[i]]=1



def reset_counters(hierarchy,nodeNum ):

	for j in range(2,0,-1):
		for i in range(nodeNum-1,-1,-1):
			cache=str(j)+"-"+str(i)
			hierarchy[cache].miss_lat = 0
			hierarchy[cache].lat_count = 0
			for i in range(len(hierarchy[cache].hist)):
                                hierarchy[cache].hist[i]=0
			
        return 0


def print_shadows(hierarchy,cache):
	fd = open("shadow.log", "a")
	fd.write("CacheID:"+ str(cache))
	#fd.write(",".join(hierarchy[cache].hist))
	simplejson.dump(hierarchy[cache].hist, fd)
	fd.write("\n")
	fd.close()
	




