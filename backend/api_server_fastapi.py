from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import json
import os

app = FastAPI(
    title='RL Trading Bot API',
    description='Real-time API for monitoring RL trading bot performance',
    version='1.0.0'
)

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:3000'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

# Pydantic models for request/response validation
class Portfolio(BaseModel):
    balance: float
    pnl: float
    total_trades: int
    win_rate: float

class Trade(BaseModel):
    timestamp: str
    ticker: str
    side: str
    action: str
    size: int
    price: float
    cost: float

class PortfolioValue(BaseModel):
    step: int
    value: float

class Decision(BaseModel):
    action: str
    size: int
    timestamp: str

class UpdateRequest(BaseModel):
    portfolio: Optional[Portfolio] = None
    trade: Optional[Trade] = None
    portfolio_value: Optional[PortfolioValue] = None
    decision: Optional[Decision] = None

# In-memory data store
trading_data = {
    'portfolio': {
        'balance': 10000.0,
        'pnl': 0.0,
        'total_trades': 0,
        'win_rate': 0.0
    },
    'trades': [],
    'portfolio_history': [],
    'latest_decision': None
}

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
        json.dump(trading_data, f, indent=2)

# Load data on startup
load_data()

@app.get('/')
def root():
    return {
        'message': 'RL Trading Bot API',
        'version': '1.0.0',
        'docs': '/docs',
        'redoc': '/redoc'
    }

@app.get('/api/portfolio', response_model=Portfolio, tags=['Trading'])
def get_portfolio():
    load_data()
    return trading_data['portfolio']

@app.get('/api/trades', response_model=List[Trade], tags=['Trading'])
def get_trades():
    load_data()
    return trading_data['trades'][-20:]

@app.get('/api/portfolio-history', tags=['Analytics'])
def get_portfolio_history():
    load_data()
    return trading_data['portfolio_history']

@app.get('/api/latest-decision', response_model=Optional[Decision], tags=['Agent'])
def get_latest_decision():
    load_data()
    return trading_data.get('latest_decision')

@app.post('/api/update', tags=['Trading'])
def update_data(update: UpdateRequest):
    if update.portfolio:
        trading_data['portfolio'] = update.portfolio.dict()
    
    if update.trade:
        trading_data['trades'].append(update.trade.dict())
    
    if update.portfolio_value:
        trading_data['portfolio_history'].append(update.portfolio_value.dict())
    
    if update.decision:
        trading_data['latest_decision'] = update.decision.dict()
    
    save_data()
    return {'status': 'success', 'message': 'Data updated successfully'}

@app.get('/api/stats', tags=['Analytics'])
def get_stats():
    load_data()
    
    return {
        'total_trades': len(trading_data['trades']),
        'current_balance': trading_data['portfolio']['balance'],
        'total_pnl': trading_data['portfolio']['pnl'],
        'win_rate': trading_data['portfolio']['win_rate'],
        'total_steps': len(trading_data['portfolio_history'])
    }

if __name__ == '__main__':
    import uvicorn
    
    print('🚀 Starting FastAPI server with Swagger UI...')
    print('📡 API: http://localhost:5000')
    print('📚 Swagger UI: http://localhost:5000/docs')
    print('📖 ReDoc: http://localhost:5000/redoc')
    print('📄 OpenAPI JSON: http://localhost:5000/openapi.json')
    print('')
    
    # Fixed: removed reload=True to avoid the warning
    uvicorn.run(app, host='0.0.0.0', port=5000)
