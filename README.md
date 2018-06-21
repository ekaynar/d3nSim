# D3NSim: Event-Driven Simulation for D3N

D3NSim is a multi-layer datacenter-scale cache architecture simulation for hierarchical network topologies. The simulation framework is implemented using [simpy](https://simpy.readthedocs.io/en/latest/) which is a process-based discrete-event simulation based on Python.


# File Inventory:
  * config.ini - Config File
  * simulator.py - Main simulator code which executes the simulator
  * multiRun.py - Run simulator with multiple configuration settings in parallel

# Prerequisites:
Install all the required dependencies:

```
pip install -r requirements.txt
```

# Configuring Simulation For Your Enviroment 
  Edit 'config.ini' for your environment. Certain variables must be configured for your test environment.
 
  
# Input Trace File Format
 * sample.input - Sample trace.
 
 Each line represents "4M" object requests. Simulator read the trace and start issuing these requests.
 

# Usage

```
python simulator.py -c <config_file>
```

# Documentation

Please refer to [D3NSim wiki](https://github.com/ekaynar/d3nSim/wiki) for details.

# Running Multiple Configuration Settings
 
* Edit 'data' variable on multiRun.py. 'multiRun.py' will create separate config file per test case and store the log and result of each run in a seperate file.
 
 ``` python multiRun.py```
 
 * Displayin Results
 The script parses result.txt_ files and displays results in a single table.
 ```
 ./par.sh
 ```
 
