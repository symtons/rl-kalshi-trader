from flask import Flask, jsonify
from flask_cors import CORS
import json
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Allow React to connect

# Store trading data in memory (or use database later)
trading_data = {
    'portfolio': {
        'balance': 10000.0,
        'pnl': 0.0,
        'total_trades': 0,
        'win_rate': 0.0
    },
    'trades': [],
    'portfolio_history': [],
    'latest_decision': None,
    'markets': []
}

# Load from log file if exists
LOG_FILE = 'logs/trading_data.json'

def load_data():
    global trading_data
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, 'r') as f:
                trading_data = json.load(f)
        except:
            pass

def save_data():
    os.makedirs('logs', exist_ok=True)
    with open(LOG_FILE, 'w') as f:
        json.dump(trading_data, f)

@app.route('/api/portfolio', methods=['GET'])
def get_portfolio():
    load_data()
    return jsonify(trading_data['portfolio'])

@app.route('/api/trades', methods=['GET'])
def get_trades():
    load_data()
    # Return last 20 trades
    return jsonify(trading_data['trades'][-20:])

@app.route('/api/portfolio-history', methods=['GET'])
def get_portfolio_history():
    load_data()
    return jsonify(trading_data['portfolio_history'])

@app.route('/api/latest-decision', methods=['GET'])
def get_latest_decision():
    load_data()
    return jsonify(trading_data.get('latest_decision'))

@app.route('/api/markets', methods=['GET'])
def get_markets():
    load_data()
    return jsonify(trading_data.get('markets', []))

@app.route('/api/update', methods=['POST'])
def update_data():
    # This will be called by trading bot to update data
    from flask import request
    data = request.json
    
    if 'portfolio' in data:
        trading_data['portfolio'] = data['portfolio']
    if 'trade' in data:
        trading_data['trades'].append(data['trade'])
    if 'portfolio_value' in data:
        trading_data['portfolio_history'].append(data['portfolio_value'])
    if 'decision' in data:
        trading_data['latest_decision'] = data['decision']
    if 'markets' in data:
        trading_data['markets'] = data['markets']
    
    save_data()
    return jsonify({'status': 'success'})

if __name__ == '__main__':
    load_data()
    print('🚀 Starting Flask API server...')
    print('📡 Dashboard can connect at: http://localhost:5000')
    app.run(debug=True, port=5000)
