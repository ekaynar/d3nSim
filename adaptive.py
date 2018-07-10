import simplejson
import multiThread
import numpy as np

def calculate_prefix_sum(cache1,cache2):
	cache1.prefix_sum = np.sum(cache1.hist) - np.cumsum(cache1.hist)		
	cache2.prefix_sum = np.sum(cache2.hist) - np.cumsum(cache2.hist)		

def cost2(cache1,cache2,l1_pos,l2_pos,L1_lat,L2_lat,size):
	mc_l1=mc_l2=0
	mc_l1= cache1.prefix_sum[l1_pos]
	mc_l2= cache2.prefix_sum[l2_pos]
	return (mc_l1*L1_lat) + (mc_l2*L2_lat)



def cost(cache1,cache2,l1_pos,l2_pos,L1_lat,L2_lat,size):
        mc_l1=mc_l2=0
        for i in range(l1_pos,size):
                mc_l1+=cache1.hist[i]

        for i in range(l2_pos,size):
                mc_l2+=cache2.hist[i]

        res = (mc_l1*L1_lat) + (mc_l2*L2_lat)
        return res



def set_cache(hierarchy,env,shadow_window,racknum):
	print racknum
	pool = multiThread.ThreadPool(racknum)
        for rackid in range(racknum):
        	pool.add_task(set_cache_size2,hierarchy,env,shadow_window,rackid)
        pool.wait_completion()
	
	fd = open("position", "a")
        fd.write("\n")
        fd.write("------------------------------")
        fd.write("\n")
        fd.close()

	reset_counters(hierarchy,racknum)
def set_cache_size2(hierarchy,env,shadow_window,rid):
        layers=2
        min_cost=None
        l1_pos=l2_pos=0
        
	cache_1="1-"+str(rid)
        cache_2="2-"+str(rid)
        size = len(hierarchy[cache_1].hist)
	
        l1_lat= float(hierarchy[cache_1].miss_lat)/float(hierarchy[cache_1].lat_count)
        l2_lat= float(hierarchy[cache_2].miss_lat)/float(hierarchy[cache_2].lat_count)

	current_l1_pos = hierarchy[cache_1].cache.get_size()
	current_l2_pos = hierarchy[cache_2].cache.get_size()

	
     #   for i in range(1,size):
       	for i in range(current_l1_pos-shadow_window-5,current_l1_pos+shadow_window+5):
       		if ( current_l1_pos-shadow_window <= i <= current_l1_pos +shadow_window):
	        	res = cost(hierarchy[cache_1],hierarchy[cache_2],i,size-i,l1_lat,l2_lat,size)
                	if min_cost != None:
                       		if ( res < min_cost):
                               		min_cost = res
                        	       	l1_pos = i
                                	l2_pos = size-i
	       		else:
                		min_cost=res
                      	 	l1_pos = i
                        	l2_pos = size-i
	# Increase L1 Size
	if (int(l1_pos) > int(current_l1_pos)):
		new_l1_size = current_l1_pos + shadow_window
		if (new_l1_size > size):
			new_l1_size = size
		new_l2_size = current_l2_pos - shadow_window
		if (new_l2_size < 0):
			new_l1_size = 0;
	#Increase L2 Size
	else :
		new_l1_size = current_l1_pos - shadow_window
		if (new_l1_size < 0):
			new_l1_size = 0
		new_l2_size = current_l2_pos + shadow_window
		if (new_l2_size > size):
			new_l2_size = size;
	hierarchy[cache_1].cache.set_size(new_l1_size)
	hierarchy[cache_2].cache.set_size(new_l2_size)

	fd = open("position", "a")
	fd.write(str(cache_1)+","+str(cache_2)+","+str(new_l1_size)+","+ str(new_l2_size)+","+str(env.now))
	fd.write("\n")
        fd.close()
def set_cache_size(hierarchy,env,shadow_window,racknum):
        layers=2
	fd = open("position", "a")
	fd2 = open("latency", "a")
        for j in range(racknum):
                min_cost=None
                l1_pos=l2_pos=0
                
		cache_1="1-"+str(j)
                cache_2="2-"+str(j)
                size = len(hierarchy[cache_1].hist)
	
			
                l1_lat= float(hierarchy[cache_1].miss_lat)/float(hierarchy[cache_1].lat_count)
                l2_lat= float(hierarchy[cache_2].miss_lat)/float(hierarchy[cache_2].lat_count)
	
		current_l1_pos = hierarchy[cache_1].cache.get_size()
		current_l2_pos = hierarchy[cache_2].cache.get_size()
		calculate_prefix_sum(hierarchy[cache_1],hierarchy[cache_2])
		for i in range(1,size):
               		res = cost2(hierarchy[cache_1],hierarchy[cache_2],i,size-i,l1_lat,l2_lat,size)
	          	if min_cost != None:
                       		if ( res < min_cost):
                               		min_cost = res
		               		l1_pos = i
                                	l2_pos = size-i
	        	else:
                		min_cost=res
                       		l1_pos = i
                        	l2_pos = size-i
		# Increase L1 Size
		
		if abs(current_l1_pos-l1_pos) > shadow_window:
			win_size = shadow_window
	
		else:
			win_size = abs(current_l1_pos-l1_pos)
				
		if (int(l1_pos) > int(current_l1_pos)):
			new_l1_size = current_l1_pos + win_size
			if (new_l1_size > size):
				new_l1_size = size
			new_l2_size = current_l2_pos - win_size
			if (new_l2_size < 0):
				new_l1_size = 0;
		#Increase L2 Size
		else :
			new_l1_size = current_l1_pos - win_size
			if (new_l1_size < 0):
				new_l1_size = 0
			new_l2_size = current_l2_pos + win_size
			if (new_l2_size > size):
				new_l2_size = size;
		hierarchy[cache_1].cache.set_size(new_l1_size)
		hierarchy[cache_2].cache.set_size(new_l2_size)
        	fd.write(str(cache_1)+","+str(cache_2)+","+str(new_l1_size)+","+ str(new_l2_size)+","+str(env.now))
        	fd.write("\n")

		fd2.write(str(cache_1)+","+str(cache_2)+","+str(hierarchy[cache_1].miss_lat)+","+ str(hierarchy[cache_2].miss_lat)+","+str(hierarchy[cache_1].lat_count)+","+str(hierarchy[cache_2].lat_count)+","+str(l1_lat)+","+str(l2_lat)+","+str(env.now))
		fd2.write("\n")
       		print(str(cache_1)+","+str(cache_2)+","+str(hierarchy[cache_1].miss_lat)+","+ str(hierarchy[cache_2].miss_lat)+","+str(hierarchy[cache_1].lat_count)+","+str(hierarchy[cache_2].lat_count)+","+str(l1_lat)+","+str(l2_lat)+","+str(env.now)) 
        fd2.write("------------------------------")
	fd2.write("\n")
	fd2.close()
        fd.write("------------------------------")
        fd.write("\n")
        fd.close()


	reset_counters(hierarchy,racknum)

def move2layer1(cache1,cache2,pos1,pos2):
	orig_size = cache2.get_size()
	keys =cache2.keys()[:]
	for i in range(pos2,len(keys)):
		cache1[keys[i]]=1

# Decay counter list and latency parameter by 2
def reset_counters(hierarchy,rackNum):
	for j in range(2,0,-1):
		for i in range(rackNum-1,-1,-1):
			cache=str(j)+"-"+str(i)
			hierarchy[cache].miss_lat = float(hierarchy[cache].miss_lat)/2
			for i in range(len(hierarchy[cache].hist)):
                                hierarchy[cache].hist[i]=float(hierarchy[cache].hist[i])/2
        		hierarchy[cache].lat_count = 0
		print hierarchy[cache].lat_count, hierarchy[cache].miss_lat
	return 0

def print_shadows(hierarchy,cache):
	fd = open("shadow.log", "a")
	fd.write("CacheID:"+ str(cache))
	#fd.write(",".join(hierarchy[cache].hist))
	simplejson.dump(hierarchy[cache].hist, fd)
	fd.write("\n")
	fd.close()
	




