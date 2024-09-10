from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
import subprocess
import logging
import time
import threading

app = Flask(__name__)
CORS(app)
app.secret_key = 'your_secret_key'  # Change this to a random secret key

logging.basicConfig(level=logging.DEBUG)

LNCRAWL_PATH = '/home/alexxander29/lnproject/lncrawl-linux'

# Store for ongoing searches
searches = {}

def run_lncrawl(search_id, novel_name):
    process = subprocess.Popen([LNCRAWL_PATH],
                               stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT,
                               text=True,
                               bufsize=1)

    searches[search_id] = {
        'process': process,
        'output': [],
        'status': 'running',
        'novels_listed': False
    }

    # Send the novel name
    process.stdin.write(f"{novel_name}\n")
    process.stdin.flush()

    while True:
        line = process.stdout.readline()
        if not line:
            break
        searches[search_id]['output'].append(line)
        yield line

        if "Which one is your novel? (Use arrow keys)" in line:
            searches[search_id]['novels_listed'] = True
            yield "NOVELS_LISTED\n"

    searches[search_id]['status'] = 'completed'

@app.route('/start', methods=['POST'])
def start_crawl():
    novel_name = request.json.get('novel_name')
    if not novel_name:
        return jsonify({"error": "No novel name provided"}), 400

    search_id = str(time.time())
    threading.Thread(target=lambda: list(run_lncrawl(search_id, novel_name))).start()

    return jsonify({"search_id": search_id}), 202

@app.route('/select/<search_id>', methods=['POST'])
def select_novel(search_id):
    if search_id not in searches:
        return jsonify({"error": "Invalid search ID"}), 404

    if not searches[search_id]['novels_listed']:
        return jsonify({"error": "Novels not yet listed"}), 400

    option = request.json.get('option', '')
    searches[search_id]['process'].stdin.write(f"{option}\n")
    searches[search_id]['process'].stdin.flush()

    return jsonify({"status": "Selection sent"}), 200

@app.route('/stream/<search_id>')
def stream_output(search_id):
    if search_id not in searches:
        return jsonify({"error": "Invalid search ID"}), 404

    def generate():
        for line in run_lncrawl(search_id, searches[search_id]['novel_name']):
            yield f"data: {line}\n\n"

    return Response(stream_with_context(generate()), mimetype='text/event-stream')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)