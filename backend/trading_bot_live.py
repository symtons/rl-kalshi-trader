import time
import logging
import os
import requests
from datetime import datetime
from typing import Dict, Any
import numpy as np
from stable_baselines3 import PPO
from trading.kalshi_client import KalshiClient
from rl.features import FeatureEngineering

os.makedirs('logs', exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/trading_bot.log'),
        logging.StreamHandler()
    ]
)

# Flask API endpoint
API_URL = 'http://localhost:5000/api/update'

class RLTradingBot:
    def __init__(self, model_path: str, api_key: str, private_key_path: str, paper_trading: bool = False):
        self.logger = logging.getLogger(__name__)
        self.paper_trading = paper_trading
        
        self.logger.info(f'Loading RL model from {model_path}')
        self.model = PPO.load(model_path)
        self.logger.info('Model loaded')
        
        self.kalshi = KalshiClient(api_key, private_key_path)
        self.logger.info('Kalshi client initialized')
        
        self.feature_engineer = FeatureEngineering(lookback_window=24)
        
        self.price_history = [106000.0] * 24  # Seed with initial prices
        self.positions = []
        self.trade_history = []
        self.balance = 10000 if paper_trading else 0
        self.initial_balance = self.balance
        self.portfolio_history = []
        self.step_count = 0
        
        if not paper_trading:
            balance_data = self.kalshi.get_balance()
            self.balance = balance_data.get('balance', 0) / 100
            self.initial_balance = self.balance
            self.logger.info(f'Account balance: ')
        
        # Initialize dashboard
        self._update_dashboard()
    
    def get_current_btc_price(self) -> float:
        import requests
        try:
            response = requests.get('https://api.coinbase.com/v2/prices/BTC-USD/spot', timeout=5)
            if response.status_code == 200:
                price = float(response.json()['data']['amount'])
                return price
        except:
            pass
        return self.price_history[-1] if self.price_history else 106000.0
    
    def get_available_markets(self) -> list:
        try:
            markets = self.kalshi.get_markets(series_ticker='KXBTC', limit=10)
            self.logger.info(f'Found {len(markets)} BTC markets')
            return markets
        except Exception as e:
            self.logger.error(f'Error fetching markets: {e}')
            return []
    
    def make_decision(self, market: Dict[str, Any]) -> tuple:
        current_price = self.get_current_btc_price()
        self.price_history.append(current_price)
        
        if len(self.price_history) > 1000:
            self.price_history = self.price_history[-1000:]
        
        price_array = np.array(self.price_history)
        price_features = self.feature_engineer.extract_features(price_array, len(price_array) - 1)
        
        hour = datetime.now().hour
        time_features = {
            'hour_of_day': hour,
            'time_to_expiry': 1.0,
            'is_near_expiry': 0,
            'implied_probability': market.get('yes_ask', 50) / 100,
            'bid_ask_spread': (market.get('yes_ask', 50) - market.get('yes_bid', 0)) / 100
        }
        
        position_features = {
            'num_positions': len(self.positions),
            'total_exposure': sum(p.get('size', 0) * p.get('entry_price', 0) for p in self.positions),
            'unrealized_pnl': 0,
            'portfolio_value': self.balance,
            'win_rate': self._calculate_win_rate()
        }
        
        state = self.feature_engineer.create_state_vector(price_features, time_features, position_features)
        
        action, _ = self.model.predict(state, deterministic=True)
        decision, size_idx = action
        position_size = [0, 10, 25, 50, 100][size_idx]
        
        action_names = ['HOLD', 'BUY_YES', 'BUY_NO', 'SELL_YES', 'SELL_NO']
        self.logger.info(f'Agent decision: {action_names[decision]} x{position_size}')
        
        # Send decision to dashboard
        self._send_decision(action_names[decision], position_size)
        
        return decision, position_size
    
    def execute_trade(self, market: Dict[str, Any], decision: int, size: int):
        if decision == 0 or size == 0:
            self.logger.info('Holding - no action')
            return
        
        ticker = market['ticker']
        yes_ask = market.get('yes_ask', 50)
        yes_bid = market.get('yes_bid', 0)
        
        if decision == 1:
            side, action, price = 'yes', 'buy', yes_ask
        elif decision == 2:
            side, action, price = 'no', 'buy', 100 - yes_bid
        elif decision == 3:
            side, action, price = 'yes', 'sell', yes_bid
        elif decision == 4:
            side, action, price = 'no', 'sell', 100 - yes_ask
        else:
            return
        
        cost = (price / 100) * size
        
        if cost > self.balance:
            self.logger.warning(f'Insufficient balance:  < ')
            return
        
        self.logger.info(f'{action.upper()} {size}x {side.upper()} @ {price}c')
        
        if self.paper_trading:
            self.logger.info('PAPER TRADING - Simulated')
            self.balance -= cost
        else:
            result = self.kalshi.create_order(ticker, side, action, size, price)
            if 'error' in result:
                self.logger.error(f'Order failed: {result["error"]}')
                return
            self.logger.info('Order placed')
            self.balance -= cost
        
        trade = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'ticker': ticker,
            'side': side,
            'action': action,
            'size': size,
            'price': price,
            'cost': cost
        }
        self.trade_history.append(trade)
        
        # Send trade to dashboard
        self._send_trade(trade)
    
    def _calculate_win_rate(self) -> float:
        if len(self.trade_history) == 0:
            return 0.0
        return 50.0  # Simplified
    
    def _update_dashboard(self):
        '''Send portfolio update to dashboard'''
        try:
            pnl = self.balance - self.initial_balance
            
            data = {
                'portfolio': {
                    'balance': self.balance,
                    'pnl': pnl,
                    'total_trades': len(self.trade_history),
                    'win_rate': self._calculate_win_rate()
                }
            }
            
            requests.post(API_URL, json=data, timeout=2)
        except Exception as e:
            self.logger.debug(f'Dashboard update failed: {e}')
    
    def _send_trade(self, trade: dict):
        '''Send trade to dashboard'''
        try:
            data = {'trade': trade}
            requests.post(API_URL, json=data, timeout=2)
        except Exception as e:
            self.logger.debug(f'Trade update failed: {e}')
    
    def _send_decision(self, action: str, size: int):
        '''Send agent decision to dashboard'''
        try:
            data = {
                'decision': {
                    'action': action,
                    'size': size,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            }
            requests.post(API_URL, json=data, timeout=2)
        except Exception as e:
            self.logger.debug(f'Decision update failed: {e}')
    
    def _send_portfolio_value(self):
        '''Send portfolio history point'''
        try:
            self.step_count += 1
            data = {
                'portfolio_value': {
                    'step': self.step_count,
                    'value': self.balance
                }
            }
            requests.post(API_URL, json=data, timeout=2)
        except Exception as e:
            self.logger.debug(f'Portfolio history update failed: {e}')
    
    def run(self, interval_seconds: int = 60, max_iterations: int = 100):
        self.logger.info('Starting RL Trading Bot')
        self.logger.info(f'Mode: {"PAPER" if self.paper_trading else "LIVE"}')
        self.logger.info(f'Balance: ')
        self.logger.info('=' * 60)
        
        iteration = 0
        
        try:
            while iteration < max_iterations:
                iteration += 1
                self.logger.info(f'\nIteration {iteration}/{max_iterations}')
                
                markets = self.get_available_markets()
                if not markets:
                    self.logger.warning('No markets')
                    time.sleep(interval_seconds)
                    continue
                
                market = markets[0]
                self.logger.info(f'{market["ticker"]}: YES {market.get("yes_ask")}c')
                
                decision, size = self.make_decision(market)
                self.execute_trade(market, decision, size)
                
                self.logger.info(f'Balance:  | Trades: {len(self.trade_history)}')
                
                # Update dashboard
                self._update_dashboard()
                self._send_portfolio_value()
                
                time.sleep(interval_seconds)
                
        except KeyboardInterrupt:
            self.logger.info('\nStopped by user')
        finally:
            self.logger.info(f'\nTotal Trades: {len(self.trade_history)}')
            self.logger.info(f'Final Balance: ')

if __name__ == '__main__':
    bot = RLTradingBot(
        model_path='../models/ppo_aggressive_final.zip',
        api_key='db025f14-ed64-4c19-940b-0ad3f336713f',
        private_key_path='kalshi_private_key_new.pem',
        paper_trading=True  # Set to False when you have real funds
    )
    
    bot.run(interval_seconds=10, max_iterations=50)
