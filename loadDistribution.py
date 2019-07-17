from uhashring import HashRing
from clandestined import Cluster
from clandestined import RendezvousHash
##############################################################

def setUp(hashType,nodeNum):
	# node config
	nodes={}
	if (hashType == "consistent"):
		for i in range(int(nodeNum)):
			sname='layer2-'+str(i)
			nodes[str(i)]={'hostname':sname, 'weight': 1}
		
	elif (hashType == "rendezvous"):
		for i in range(int(nodeNum)):
			sname='layer2-'+str(i)
			nodes[str(i)]={'name':sname }
	return nodes

def rendezvousHashing(nodeNum):
	nodes=setUp("rendezvous",nodeNum)
	hr = RendezvousHash(nodes.keys(),seed=1337)
	return hr

def consistentHashing(nodeNum):
	nodes=setUp("consistent",nodeNum)
	hr = HashRing(nodes,vnodes=200,hash_fn='ketama')
	return hr



