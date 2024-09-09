from flask import Flask, request, jsonify, session
from flask_cors import CORS
import subprocess
import json

app = Flask(__name__)
CORS(app)
app.secret_key = 'your_secret_key'  # Change this to a random secret key

@app.route('/start', methods=['POST'])
def start_crawl():
    url = request.json['url']
    session['url'] = url
    result = subprocess.run(['lncrawl', '-q', url], capture_output=True, text=True)
    novels = parse_novels(result.stdout)
    return jsonify(novels)

@app.route('/select_novel', methods=['POST'])
def select_novel():
    novel_index = request.json['novel_index']
    session['novel_index'] = novel_index
    result = subprocess.run(['lncrawl', '-q', session['url'], '--selection', str(novel_index)], capture_output=True, text=True)
    sources = parse_sources(result.stdout)
    return jsonify(sources)

@app.route('/select_source', methods=['POST'])
def select_source():
    source_index = request.json['source_index']
    session['source_index'] = source_index
    return jsonify({"status": "success"})

@app.route('/set_output', methods=['POST'])
def set_output():
    output_dir = request.json['output_dir']
    session['output_dir'] = output_dir
    return jsonify({"status": "success"})

@app.route('/select_chapters', methods=['POST'])
def select_chapters():
    chapters = request.json['chapters']
    session['chapters'] = chapters
    return jsonify({"status": "success"})

@app.route('/select_formats', methods=['POST'])
def select_formats():
    formats = request.json['formats']
    session['formats'] = formats
    return jsonify({"status": "success"})

@app.route('/crawl', methods=['POST'])
def crawl():
    command = [
        'lncrawl',
        '-q',
        session['url'],
        '--selection', str(session['novel_index']),
        '--source', str(session['source_index']),
        '--output', session['output_dir'],
        '--chapters', session['chapters'],
        '--format'
    ] + session['formats']
    
    result = subprocess.run(command, capture_output=True, text=True)
    return jsonify({"output": result.stdout})

def parse_novels(output):
    # Implement parsing logic to extract novel list from lncrawl output
    pass

def parse_sources(output):
    # Implement parsing logic to extract source list from lncrawl output
    pass

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)