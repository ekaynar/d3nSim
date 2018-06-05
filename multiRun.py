import createConfig
import math
import subprocess

cachespace=9216
num=11
#num=9

ratios=[]

ratios.append(["4M","16384M"])
#ratios.append(["4M","32764M"])
for i in range(1,10):
	ratios.append( [ int(math.ceil(cachespace*i/10)),int(cachespace-math.ceil(cachespace*i/10))])

ratios.append(["16384M","4M"])
for i in range(num):
	cfile="config_"+str(i)+".ini"
	rfile="results.txt_"+str(i)
	lfile="logs_"+str(i)
	if (i==0):
		L1=str(ratios[i][0])
		L2=str(ratios[i][1])
	elif (i==num-1):
		L1=str(ratios[i][0])
		L2=str(ratios[i][1])
	else:
		L1=str(ratios[i][0])+"M"
		L2=str(ratios[i][1])+"M"
	data=[10,1100,1,'true','true',L1,L2,'16G',100,'LRU_S','LRU_S','4M','rr',lfile,'40T_job_list.txt','test1','test2','test3','test4','test5','test6','test7','test8','test9','test10','test11','test12',rfile]
	data2=["15Gbps","20Gbps","5Gbps","15Gbps"]
	createConfig.gen_config(data,data2,cfile)
#	print data
#	print data2


bashCommand="for i in {0.."+str(num-1)+"}; do time python simulator.py -c config_$i.ini & done;wait"
process = subprocess.Popen([bashCommand],shell=True)
process.wait()

