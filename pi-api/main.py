from flask import Flask, request, jsonify
from flask_cors import CORS
import datetime
from waitress import serve

PORT = 1337
MAX_HISTORY_LENGTH = 60

stats_history = []

app = Flask(__name__)
CORS(app)

@app.route('/stats', methods=['POST'])
def receive_stats():
    new_stats = request.json
    if not new_stats or 'timestamp' not in new_stats:
        return jsonify(message='Invalid data format. Timestamp is required.'), 400
    stats_history.insert(0, new_stats)
    if len(stats_history) > MAX_HISTORY_LENGTH:
        stats_history.pop()
    print(f"Received new stats at {new_stats.get('timestamp')}. History size: {len(stats_history)}")
    return jsonify(message='Stats received successfully.'), 201

@app.route('/stats/latest', methods=['GET'])
def get_latest_stats():
    if not stats_history:
        return jsonify(message='No stats available yet.'), 404
    latest_stats = stats_history[0]
    return jsonify(latest_stats), 200

@app.route('/stats/history', methods=['GET'])
def get_stats_history():
    return jsonify(stats_history), 200

if __name__ == '__main__':
    print(f"Server is running on http://localhost:{PORT} (using Waitress)")
    serve(app, host='0.0.0.0', port=PORT)