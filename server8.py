from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
import subprocess
import logging
import time

app = Flask(__name__)
CORS(app)
app.secret_key = 'your_secret_key'  # Change this to a random secret key

logging.basicConfig(level=logging.DEBUG)

LNCRAWL_PATH = '/home/alexxander29/lnproject/lncrawl-linux'

def stream_output(novel_name):
    def generate():
        try:
            process = subprocess.Popen([LNCRAWL_PATH],
                                       stdin=subprocess.PIPE,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.STDOUT,
                                       text=True,
                                       bufsize=1)
            
            # Wait for the initial prompt and send the novel name
            while True:
                line = process.stdout.readline()
                yield f"data: {line}\n\n".encode('utf-8')
                if "Enter novel page url or query novel:" in line:
                    process.stdin.write(f"{novel_name}\n")
                    process.stdin.flush()
                    break

            # Read and yield the list of novels
            novels_listed = False
            while True:
                line = process.stdout.readline()
                yield f"data: {line}\n\n".encode('utf-8')
                if "Which one is your novel? (Use arrow keys)" in line:
                    novels_listed = True
                elif novels_listed and line.strip():  # Check for non-empty lines after the prompt
                    yield b"data: NOVELS_LISTED\n\n"
                    break

            # Wait for the option selection from the client
            option = yield
            process.stdin.write(f"{option}\n")
            process.stdin.flush()

            # Continue reading output
            for line in iter(process.stdout.readline, ''):
                yield f"data: {line}\n\n".encode('utf-8')
                time.sleep(0.1)  # Small delay to prevent overwhelming the client

            process.stdout.close()
            return_code = process.wait()
            
            if return_code == 0:
                yield b"data: SEARCH_COMPLETED\n\n"
            else:
                yield b"data: SEARCH_FAILED\n\n"
        except Exception as e:
            app.logger.error(f"Error during search for {novel_name}: {str(e)}")
            yield f"data: ERROR: {str(e)}\n\n".encode('utf-8')

    return Response(stream_with_context(generate()), mimetype='text/event-stream')

@app.route('/start', methods=['POST'])
def start_crawl():
    app.logger.info("Received request to start_crawl")
    novel_name = request.json.get('novel_name')
    
    if not novel_name:
        app.logger.error("No novel name provided")
        return jsonify({"error": "No novel name provided"}), 400

    return stream_output(novel_name)

@app.route('/select', methods=['POST'])
def select_option():
    option = request.json.get('option')
    if option is None:
        return jsonify({"error": "No option provided"}), 400
    
    # Here you would typically use the option to continue the process
    # For now, we'll just return a success message
    return jsonify({"status": "option received"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)