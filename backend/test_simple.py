from flask import Flask, jsonify
from datetime import datetime

app = Flask(__name__)

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "message": "Simple API is running", "timestamp": datetime.now().isoformat()})

if __name__ == '__main__':
    app.run(debug = True, port = 5000)