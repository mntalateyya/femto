#!/usr/bin/python3

'''
file: controller.py
author: Mohammed Nurul Hoque <mntalateyya@live.com>
'''

import flask
import json
import subprocess
import sys
import requests
import threading

app = flask.Flask(__name__)

workers = []
w_lock = threading.Lock()
apps    = []
a_lock = threading.Lock()
tasks   = []
t_lock = threading.Lock()


'''
registers device 
returns device id

format:
POST /register
post body: dictionary of device info
    addr: host:port of worker
    arch: architecture
    flags: arch-dependent flags
'''
@app.route('/register', methods=['POST'])
def register_device():
    info = flask.request.get_json()

    # lock to avoid racing between deciding the id and appending to list
    w_lock.acquire()
    try:
        dev_id = len(workers)
        workers.append(info)
    finally:
        w_lock.release()

    return str(dev_id)


'''
add an application and start its compilation
return app id
returns without waiting for compilation to happen

format:
POST /add_app?origin=<worker-ip:port>
body: file named code
'''
@app.route('/add_app', methods=['POST'])
def add_app():

    # lock to avoid racing between deciding the id and appending to list
    a_lock.acquire()
    try:
        app_id = len(apps)
        apps.append({'origin': flask.request.args.get('origin')})
    finally:
        a_lock.release()

    filename = 'code_%d' % app_id
    flask.request.files['code'].save(filename+'.c')
    subprocess.Popen(['gcc', filename+'.c', '-o', filename],
            stderr=subprocess.DEVNULL)
    return (str(app_id), 202)


'''
accept a task for running
returns task id
returns before running the task

format:
POST /submit_task?app_id=<id of app to run>&origin=<worker-ip:port>
post body: 2 files
    args: {'argv': list of argv (excluding exe name)}
    input: input to stdin
'''
@app.route('/submit_task', methods=['POST'])
def submit_task():
    global tasks, workers

    app_id = flask.request.args.get('app_id', type=int)
    origin = flask.request.args.get('origin', type=str)

    # lock to avoid racing between deciding the id and appending to list
    t_lock.acquire()
    try:
        task_id = len(tasks)
        tasks.append({'origin': origin, 'app_id': app_id})
    finally:
        t_lock.release()

    sel_worker = 0 # selected worker to run task
    requests.post('http://%s/run_task' % workers[sel_worker]['addr'],
            params={'origin': origin, 'task_id': task_id},
            files={
                'code': open('code_%d' % app_id, 'rb'),
                'args':  flask.request.files['args'],
                'input': flask.request.files['input']
            })
    return (str(task_id), 202)


if __name__ == '__main__':
    app.run('0.0.0.0', int(sys.argv[1]))
