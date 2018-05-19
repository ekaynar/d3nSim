import createConfig
import math
import subprocess

cachespace=64
num=9

ratios=[]
for i in range(1,10):
	ratios.append( [ int(math.ceil(cachespace*i/10)),int(cachespace-math.ceil(cachespace*i/10))])

for i in range(num):
	cfile="config_"+str(i)+".ini"
	rfile="results.txt_"+str(i)
	lfile="logs_"+str(i)
	L1=str(ratios[i][0])+"G"
	L2=str(ratios[i][1])+"G"
	data=[3,1100,1,'true','true',L1,L2,'32G','LRU','LRU','4M','consistent',lfile,'40T_job_list.txt',rfile]
	data2=["20Gbps","40Gbps","5Gbps","20Gbps"]
	createConfig.gen_config(data,data2,cfile)



bashCommand="for i in {0.."+str(num-1)+"}; do time python simulator.py -c config_$i.ini & done;wait"
process = subprocess.Popen([bashCommand],shell=True)
#process = subprocess.Popen([bashCommand],shell=True, stdin=subprocess.PIPE, stdout = subprocess.PIPE,
#                    universal_newlines=True, bufsize=0)

process.wait()

