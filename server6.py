from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
import pty
import os
import select
import subprocess
import threading
import time

app = Flask(__name__)
CORS(app)

LNCRAWL_PATH = '/home/alexxander29/lnproject/lncrawl-linux'

# Store for ongoing searches
searches = {}

def run_lncrawl(search_id):
    master, slave = pty.openpty()
    process = subprocess.Popen(
        LNCRAWL_PATH,
        stdin=slave,
        stdout=slave,
        stderr=slave,
        text=True
    )
    os.close(slave)

    searches[search_id] = {
        'process': process,
        'master': master,
        'output': [],
        'status': 'running'
    }

    while True:
        try:
            r, _, _ = select.select([master], [], [], 0.1)
            if r:
                data = os.read(master, 1024).decode()
                searches[search_id]['output'].append(data)
                yield data
        except OSError:
            break

    searches[search_id]['status'] = 'completed'

@app.route('/start', methods=['POST'])
def start_crawl():
    novel_name = request.json.get('novel_name')
    if not novel_name:
        return jsonify({"error": "No novel name provided"}), 400

    search_id = str(time.time())
    threading.Thread(target=run_lncrawl, args=(search_id,)).start()

    return jsonify({"search_id": search_id}), 202

@app.route('/status/<search_id>', methods=['GET'])
def get_status(search_id):
    if search_id not in searches:
        return jsonify({"error": "Invalid search ID"}), 404

    return jsonify({
        "status": searches[search_id]['status'],
        "output": ''.join(searches[search_id]['output'])
    })

@app.route('/input/<search_id>', methods=['POST'])
def send_input(search_id):
    if search_id not in searches:
        return jsonify({"error": "Invalid search ID"}), 404

    user_input = request.json.get('input')
    if not user_input:
        return jsonify({"error": "No input provided"}), 400

    os.write(searches[search_id]['master'], (user_input + '\n').encode())
    return jsonify({"status": "Input sent successfully"}), 200

@app.route('/stream/<search_id>')
def stream_output(search_id):
    if search_id not in searches:
        return jsonify({"error": "Invalid search ID"}), 404

    def generate():
        for data in run_lncrawl(search_id):
            yield f"data: {data}\n\n"

    return Response(stream_with_context(generate()), mimetype='text/event-stream')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)