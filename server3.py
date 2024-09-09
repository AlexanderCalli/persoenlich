from flask import Flask, request, jsonify, session, Response, stream_with_context
from flask_cors import CORS
import subprocess
import json
import logging
import uuid
import time

app = Flask(__name__)
CORS(app)
app.secret_key = 'your_secret_key'  # Change this to a random secret key

# Set up logging
logging.basicConfig(level=logging.DEBUG)

LNCRAWL_PATH = '/home/alexxander29/lnproject/lncrawl-linux'

# Store for ongoing searches
searches = {}

def stream_output(search_id, novel_name):
    def generate():
        try:
            process = subprocess.Popen([LNCRAWL_PATH, '--search', novel_name], 
                                       stdout=subprocess.PIPE, 
                                       stderr=subprocess.STDOUT,
                                       text=True, 
                                       bufsize=1)
            
            for line in iter(process.stdout.readline, ''):
                yield f"data: {line}\n\n"
                time.sleep(0.1)  # Small delay to prevent overwhelming the client
            
            process.stdout.close()
            return_code = process.wait()
            
            if return_code == 0:
                yield f"data: SEARCH_COMPLETED\n\n"
            else:
                yield f"data: SEARCH_FAILED\n\n"
        except Exception as e:
            app.logger.error(f"Error during search for {novel_name}: {str(e)}")
            yield f"data: ERROR: {str(e)}\n\n"

    return Response(stream_with_context(generate()), mimetype='text/event-stream')

@app.route('/start', methods=['POST'])
def start_crawl():
    app.logger.info("Received request to start_crawl")
    novel_name = request.json.get('novel_name')
    
    if not novel_name:
        app.logger.error("No novel name provided")
        return jsonify({"error": "No novel name provided"}), 400

    search_id = str(uuid.uuid4())
    searches[search_id] = {'status': 'in_progress', 'result': None}
    
    return stream_output(search_id, novel_name)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)