#!/usr/bin/python3

'''
file: worker.py
author: Mohammed Nurul Hoque <mntalateyya@live.com>

spawns a worker server, registers with controller then loops for stdin commands

command forms:

    add <app-name> <code-file>

    run <app-name> <args>*
    input file name: <input-file to stdin>
'''

import sys
import os
import socket
import requests
import subprocess
import atexit
import json
import time

ALL_APPS = {}
ALL_TASKS = []

''' runs at exit '''
def killserver(workerserver):
    workerserver.kill()

def add_app(cmd):
    app_name = cmd[1]
    filename = cmd[2]
    if ALL_APPS.get(app_name):
        print('ERROR. Same app name exists. Chosse a different name.')
        return
    response = requests.post('http://'+ctlr+'/add_app',
            params={'origin': host_uri},
            files={'code': open(filename, 'rb')})
    app_id = int(response.text)
    ALL_APPS[app_name] = {'id': app_id, 'files': [filename]}
    print('Added app', app_name, 'with id', app_id)
    return response

def submit_task(cmd):
    app_name = cmd[1]
    args = cmd[2:]
    input_file_name = input('input file [ENTER for none]')
    response = requests.post('http://'+ctlr+'/submit_task',
            params={'app_id': ALL_APPS[app_name]['id'], 'origin': host_uri},
            files={'args': json.dumps({'argv': args}), 
                'input': open(input_file_name, 'rb') if input_file_name else ''})
    ALL_TASKS.append({'app': app_name, 'args': args, 'completed': False})
    return response

def query(cmd):
    query_type = cmd[1]
    if query_type == 'apps':
        if len(cmd) == 2:
            print('id\tname\tfiles')
            for name, info in ALL_APPS.items():
                print(info['id'], name, info['files'], sep='\t')
        else:
            name = cmd[2]
            print('id\tname\tfiles')
            print(ALL_APPS[name]['id'], name, ALL_APPS[name]['files'], sep='\t')
    if query_type == 'tasks':
        # check_tasks()
        if len(cmd) == 2:
            print('id\tapp\targs')
            for i, task in enumerate(ALL_TASKS):
                print(i, task['app'], task['args'], sep='\t')
        else:
            i = int(cmd[2])
            print('id\tapp\targs')
            print(i, ALL_TASKS[i]['app'], ALL_TASKS[i]['args'], sep='\t')
 
port = int(sys.argv[1])
host = socket.gethostbyname(socket.gethostname())
host_uri = host + ':' + str(port)

ctlr = sys.argv[2]
split = ctlr.split(':')
ctrl_addr = split[0]
ctrl_port = split[1]


workerserver = subprocess.Popen(['./workerserver.py', str(port)],
        stdout=open('workerserver.log', 'wb'), stderr=subprocess.STDOUT,
        env=dict(os.environ, **{'FLASK_APP':'workerserver.py'}))

atexit.register(killserver, workerserver=workerserver)

cmd_dict = {'add': add_app, 'run': submit_task}

rqst = requests.post('http://'+ctlr+'/register',
        json={'addr': host_uri, 'arch': 'x86-64', 'flags': 'sse'})

if rqst.ok:
    print('Successfully registered as worker', rqst.text)

while True:
    cmd = input('>>')
    if not cmd: continue
    cmd = cmd.split()
    # make it robust to malformed
    cmd_dict[cmd[0]](cmd)

time.sleep(3)
