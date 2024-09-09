from flask import Flask, request, jsonify, session
from flask_cors import CORS
import subprocess
import json
import logging
import threading
import uuid

app = Flask(__name__)
CORS(app)
app.secret_key = 'your_secret_key'  # Change this to a random secret key

# Set up logging
logging.basicConfig(level=logging.DEBUG)

LNCRAWL_PATH = '/home/alexxander29/lnproject/lncrawl-linux'

# Store for ongoing searches
searches = {}

def run_search(search_id, novel_name):
    app.logger.info(f"Starting search for {novel_name} with ID {search_id}")
    try:
        result = subprocess.run([LNCRAWL_PATH, '--search', novel_name], capture_output=True, text=True, timeout=360)
        novels = parse_novels(result.stdout)
        searches[search_id] = {'status': 'completed', 'result': novels}
        app.logger.info(f"Search completed for {novel_name}")
    except subprocess.TimeoutExpired:
        searches[search_id] = {'status': 'timeout', 'result': None}
        app.logger.error(f"Search timed out for {novel_name}")
    except Exception as e:
        searches[search_id] = {'status': 'error', 'result': str(e)}
        app.logger.error(f"Error during search for {novel_name}: {str(e)}")

@app.route('/start', methods=['POST'])
def start_crawl():
    app.logger.info("Received request to start_crawl")
    novel_name = request.json.get('novel_name')
    
    if not novel_name:
        app.logger.error("No novel name provided")
        return jsonify({"error": "No novel name provided"}), 400

    search_id = str(uuid.uuid4())
    searches[search_id] = {'status': 'in_progress', 'result': None}
    
    threading.Thread(target=run_search, args=(search_id, novel_name)).start()
    
    return jsonify({"search_id": search_id}), 202

@app.route('/status/<search_id>', methods=['GET'])
def get_status(search_id):
    search = searches.get(search_id)
    if not search:
        return jsonify({"error": "Invalid search ID"}), 404
    
    if search['status'] == 'completed':
        return jsonify({"status": "completed", "result": search['result']})
    elif search['status'] == 'in_progress':
        return jsonify({"status": "in_progress"})
    else:
        return jsonify({"status": search['status'], "error": search['result']})

def parse_novels(output):
    novels = []
    lines = output.split('\n')
    for line in lines:
        if line.strip():  # Check if line is not empty
            novels.append(line.strip())
    return novels

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)