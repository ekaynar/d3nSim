# D3NSim: Event-Driven Simulation for D3N

D3NSim is implemented using [simpy](https://simpy.readthedocs.io/en/latest/) which is a process-based discrete-event simulation based on Python.


# File Inventory:
  * config.ini - Config File
  * simulator.py - Main simulator code which executes the simulator
  * multiRun.py - Run simulator with multiple configuration settings in parallel

# Prerequisites:
Install all the required dependencies:
```
pip install simpy lru-dict clandestined uhashring numpy
```
or
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
 
