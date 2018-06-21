import createConfig
import math
import subprocess

cachespace=512
ratios=[]

#ratios.append(["4M","16384M"])
for i in range(1,10):
#	ratios.append( [ int(math.ceil(cachespace*i/10)),int(cachespace-math.ceil(cachespace*i/10))])
	ratios.append([int(cachespace/i),int(cachespace/i) ])
#ratios.append(["16384M","4M"])

num=len(ratios)
print ratios
unit="G"

for i in range(num):
	cfile="config_"+str(i)+".ini"
	rfile="results.txt_"+str(i)
	lfile="logs_"+str(i)
	adapt='false'
#	if (i==0):
#		L1=str(ratios[i][0])
#		L2=str(ratios[i][1])
#	elif (i==num-1):
#		L1=str(ratios[i][0])
#		L2=str(ratios[i][1])
#	else:	
	L1_size=str(ratios[i][0])+unit
	L2_size=str(ratios[i][1])+unit

	data=[10,1100,1,'true','true',L1_size,L2_size,'16G',100,'LRU_S','LRU_S','4M','consistent',lfile,'40T_job_list.txt',rfile,adapt]
	network=["15Gbps","20Gbps","5Gbps","15Gbps"]
	createConfig.gen_config(data,network,cfile)
#	print data
#	print data2


bashCommand="for i in {0.."+str(num-1)+"}; do time python simulator.py -c config_$i.ini & done;wait"
process = subprocess.Popen([bashCommand],shell=True)
process.wait()

