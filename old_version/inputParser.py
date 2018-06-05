import sys
import numpy as np
def inputParser(fin):
	joblist=[]
        fd = open(fin, 'r')
        fdout = open("fout", 'w')
        for line in fd:
		val = line.split(" ")
                jobId= val[3]
		for i in range(1):
			key=val[1]+"-"+val[2]+"_"+str(i)
			fdout.write(key+"\n")
			joblist.append(key)
        fd.close()
        fdout.close()
	return joblist


def inputParser3(fin):
        num=10
	#a=["a","b","c","d","e","f","g","h","i","j"]
	a=["","","","","","","","","","","",""]
	for k in range(1,num+1):
		name = fin+str(k)
		fdout = open(name, 'w')
		for j in range(3):
			for i in range(4096):
				key = "key"+a[k-1]+"_"+str(i)
				fdout.write(key+"\n")
        	fdout.close()
def zipf():

	a = 2. # parameter
	s = np.random.zipf(a, 1000)
	print s

def inputParser2(fin):
	joblist=[]
        fdout = open(fin, 'r')
	for line in fdout:
		joblist.append(line.replace("\n",""))
        fdout.close()
	return joblist
if __name__ == '__main__':
#	zipf()
	inputParser(sys.argv[1])
