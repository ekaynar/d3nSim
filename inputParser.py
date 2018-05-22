def inputParser(fin):
	joblist=[]
        fd = open(fin, 'r')
        fdout = open("fout", 'w')
        for line in fd:
		val = line.split(" ")
                jobId= val[3]
		for i in range(1):
			key=val[1]+"_"+val[2]+"_"+str(i)
			fdout.write(key+"\n")
			joblist.append(key)
        fd.close()
        fdout.close()
	return joblist


def inputParser3(fin):
        fdout = open("fout", 'w')
	for i in range(8192):
		key = "key_"+str(i)
		fdout.write(key+"\n")
        fdout.close()

def inputParser2(fin):
	joblist=[]
        fdout = open(fin, 'r')
	for line in fdout:
		joblist.append(line)
        fdout.close()
	return joblist
if __name__ == '__main__':
	inputParser3(1)

