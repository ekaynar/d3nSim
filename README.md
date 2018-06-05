# D3NSim: Event-Driven Simulation for D3N
FILE INVENTORY:
  * config.ini - Config File
  * simulator.py - Main simulator code which executes the simulator
  * multiRun.py - Run simulator with multiple configuration settings in parallel

USAGE:
  * Edit 'config.ini' for your environment (layers; cachesize; obj sizes ...)
  
  
PREREQUEST:
```
pip install simpy
pip install lru-dict
pip install clandestined
pip install uhashring
```

# Input Trace File Format
 * sample.input - Sample trace.
 
 Each line represents "4M" object requests. Simulator read the trace and start issuing these requests.
 
# Configuring Simulation For Your Enviroment 
  Edit 'config.ini' Certain variables must be configured for your test environment.
 
 
# Running Multiple Configuration Settings
 * Create input files per racks. You have to edit the 'inputParser.py'
 ```
 python inputParser.py test
 
 ```
 The program generates multiple files called test1,test2,test3...
 
 * Edit 'data' variable on multiRun.py. 
 
 ``` python multiRun.py```
 
 'multiRun.py' will create separate config files per test and store the log and result files of the test in seperate files.
 
 * Parsing Results
 The script parse result.txt_ files and display results in a single table.
 ```
 ./par.sh
 ```
 
