# Requirements

- python3
- flask and portalock: install with python3 -m pip install flask portalock


# Running

start controller
``` bash
$ ./controller.py <port>
```

start worker
``` bash
$ ./worker.py <port> <controller-ip:port>
```

reister an app
``` bash
>> add <app-name> test.c
```

run an app
``` bash
>> run <app-name> 10 20
input file name [ENTER for none]: <ENTER>
```

output will be saved to task\_<n>.stdout
