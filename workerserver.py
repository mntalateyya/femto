#!/usr/bin/python3

'''
file: worker.py
author: Mohammed Nurul Hoque <mntalateyya@live.com>
'''

import flask
import os, sys
import subprocess
import threading 
import requests
import json
import portalocker

app = flask.Flask(__name__)


'''
forks the actual task executable
posts results to origin after completion

This function is blocking so it has to be called asynchronously
'''
def run_child(origin, task_id, argv, stdin_text):
    output = subprocess.run(['./code'] + argv,
            capture_output=True, input=stdin_text)

    requests.post('http://%s/results' % origin,
        params={'task_id': task_id},
        files={
            'stdout': output.stdout,
            'stderr': output.stderr 
        })

'''
accept task from controller to run

format:
POST /run_task?origin=<task-origin>&task_id=<task-id>
post body: 3 files
    code: executable
    args: {'argv': list of argv (excluding exe name)}
    input: input to stdin
'''
@app.route('/run_task', methods=['POST'])
def run_task():
    origin = flask.request.args.get('origin', type=str)
    task_id = flask.request.args.get('task_id', type=int)

    # will only allow one app at a time
    flask.request.files['code'].save('code')
    args = json.loads(flask.request.files['args'].read())
    print(args)
    stdin = flask.request.files['input']

    os.chmod('./code', 0o0777)

    threading.Thread(target=run_child, 
        args=(origin, task_id, args['argv'], stdin.read())).start()

    return ('OK', 202)


'''
accept results from worker who ran the task
format:
POST /results?task_id=<task-id>
post body: 2 files
    stdout: output to stdout
    stderr: output to stderr
'''
@app.route('/results', methods=['POST'])
def results():
    task_id = flask.request.args.get('task_id', type=int)
    with open('task_{}.stdout'.format(task_id), 'wb') as f:
        f.write(flask.request.files['stdout'].read())
    with open('task_{}.stderr'.format(task_id), 'wb') as f:
        f.write(flask.request.files['stderr'].read())
    with portalocker.Lock('tasks.list', 'a') as f:
        f.write('{} complete'.format(task_id))


if __name__ == '__main__':
    app.run('0.0.0.0', int(sys.argv[1]))
