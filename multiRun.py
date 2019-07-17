import createConfig
import math
import subprocess


# Configurations
#################################
warmup_time=200
#algorithm_time=50
cache_space=['256G','512G']
per_cache_space=['128G','256G']
ratios=[]
#input_file="binomial-trace"
input_file="trace"
run_num=2
rack_num=10
input,network_speed=[],[]
network_speed.append(["15Gbps","20Gbps","15Gbps","15Gbps"])
network_speed.append(["15Gbps","20Gbps","10Gbps","15Gbps"])
network_speed.append(["15Gbps","20Gbps","5Gbps","15Gbps"])
window_size=[50,100,200,400,800,1600]
algorithm_time=[20,40,100,150]
unit="G"



#ratios.append(["4M","16384M"])
#for i in range(1,rack_num):
#	ratios.append( [ int(math.ceil(cache_space*i/10)),int(cache_space-math.ceil(cache_space*i/10))])

#	ratios.append([int(cache_space/i),int(cache_space/i) ])

#ratios.append(["16384M","4M"])

print ratios
for i in range(10):
	input.append(input_file+str(i))


# Create Config file for each run
################################################################333
for i in range(run_num):
	cfile="config_"+str(i)+".ini"
	rfile="results.txt_"+str(i)
	lfile="logs_"+str(i)
	position="position_"+str(i)
	adapt='false'
#	if (i==0):
#		L1=str(ratios[i][0])
#		L2=str(ratios[i][1])
#	elif (i==num-1):
#		L1=str(ratios[i][0])
#		L2=str(ratios[i][1])
#	else:	
#	L1_size=str(ratios[i][0])+unit
#	L2_size=str(ratios[i][1])+unit

	data=[rack_num,1100,1,'true','true',per_cache_space[i],per_cache_space[i],cache_space[i],1600,'LRU_S','LRU_S','4M','rr',lfile,
input[0],input[1],input[2],input[3],input[4],input[5],input[6],input[7],input[8],input[9],
'40T_job_list.txt',rfile,adapt,warmup_time , algorithm_time[i],position]
	network=["15Gbps","20Gbps","5Gbps","15Gbps"]
	createConfig.gen_config(data,network,cfile)
#	createConfig.gen_config(data,network_speed[i],cfile)


bashCommand="for i in {0.."+str(run_num-1)+"}; do time python simulator.py -c config_$i.ini & done;wait"
process = subprocess.Popen([bashCommand],shell=True)
process.wait()

