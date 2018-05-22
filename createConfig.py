import ConfigParser

def gen_config(array,array2,fname):

	config = ConfigParser.ConfigParser()

	section="Simulation"
	name=[
            'nodeNum',
                'threadNum',
                'clientNum',
                'L1',
                'L2',
                'L1_size',
                'L2_size',
                'shadow_size',
                'L1_rep',
                'L2_rep',
                'obj_size',
                'hashType',
                'log_file',
                'input',
                'input1',
                'input2',
                'input3',
                'res_file',
 ]

	network=[
'L1_In',
'L1_Out',
'L2_In',
'L2_Out'


]	
	with open(fname, 'w') as cfgfile:
		config.add_section(section)
		for i in range(len(name)):
			config.set(section,name[i],array[i] )
	
		section="Network"	
		config.add_section(section)
		for i in range(len(network)):
			config.set(section,network[i],array2[i] )
		config.write(cfgfile)
	cfgfile.close()

data=[3,1100,1,'true','true','56G','8G','32G','LRU','LRU','4M','consistent','logs','40T_job_list.txt','fout1','fout2','fout2','results.txt']
data2=["20Gbps","40Gbps","5Gbps","20Gbps",]
fname='example.ini'
gen_config(data,data2,fname)







