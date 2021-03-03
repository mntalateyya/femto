from flask import Flask, request, send_file
app = Flask(__name__)

@app.route('/', methods=['POST'])
def hello_world():
    for name in request.files:
        for f in request.files.getlist(name):
            # f.stream.seek(0)
            f.save(f.filename)
    return send_file('gamma.jpg', as_attachment=True)
