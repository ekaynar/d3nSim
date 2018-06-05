def parse(fname):
        fd = open(fname, 'r')
        for line in fd:
                print line 
		key1=line
                osize.append(size)
                key.append(key1)
                if key1 not in dict:
                        dict[key1]=1
                        data+=int(size)
                        miss+=int(size)
                else:
                        hit+=int(size)
#               if(warmup <miss ):
#                       print counter
#                       print miss, hit, warmup
#                       break;
        fd.close()
        dict.clear()
        print data,"data"
        logging.info("Footprint " + str(data))
        logging.info("Hit " + str(hit))
        logging.info("Miss " + str(miss))
        print hit, miss
        return data
