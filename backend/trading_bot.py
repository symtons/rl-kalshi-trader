import time
import logging
import os
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
        
        if not paper_trading:
            balance_data = self.kalshi.get_balance()
            self.balance = balance_data.get('balance', 0) / 100
            self.logger.info(f'Account balance: ${self.balance:.2f}')
    
    def get_current_btc_price(self) -> float:
        import requests
        try:
            response = requests.get('https://api.coinbase.com/v2/prices/BTC-USD/spot', timeout=5)
            if response.status_code == 200:
                price = float(response.json()['data']['amount'])
                self.logger.info(f'Current BTC price: ${price:,.2f}')
                return price
        except Exception as e:
            self.logger.warning(f'Failed to get BTC price: {e}')
        return 106000.0
    
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
        
        if len(self.price_history) < 24:
            self.logger.info(f'Building price history... ({len(self.price_history)}/24)')
            return 0, 0
        
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
            'win_rate': 0.5
        }
        
        state = self.feature_engineer.create_state_vector(price_features, time_features, position_features)
        
        action, _ = self.model.predict(state, deterministic=True)
        decision, size_idx = action
        position_size = [0, 10, 25, 50, 100][size_idx]
        
        action_names = ['HOLD', 'BUY_YES', 'BUY_NO', 'SELL_YES', 'SELL_NO']
        self.logger.info(f'*** AGENT DECISION: {action_names[decision]} x{position_size} contracts ***')
        
        return decision, position_size
    
    def execute_trade(self, market: Dict[str, Any], decision: int, size: int):
        if decision == 0 or size == 0:
            self.logger.info('HOLD - No action taken')
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
            self.logger.warning(f'INSUFFICIENT BALANCE: ${self.balance:.2f} < ${cost:.2f}')
            return
        
        self.logger.info(f'>>> EXECUTING: {action.upper()} {size}x {side.upper()} @ {price}c (cost: ${cost:.2f})')
        
        if self.paper_trading:
            self.logger.info('PAPER TRADE - Simulated execution')
            self.balance -= cost
            self.logger.info(f'New balance: ${self.balance:.2f}')
        else:
            result = self.kalshi.create_order(ticker, side, action, size, price)
            if 'error' in result:
                self.logger.error(f'ORDER FAILED: {result["error"]}')
                return
            self.logger.info(f'ORDER PLACED: {result}')
            self.balance -= cost
        
        self.trade_history.append({
            'timestamp': datetime.now(),
            'ticker': ticker,
            'side': side,
            'action': action,
            'size': size,
            'price': price,
            'cost': cost
        })
    
    def run(self, interval_seconds: int = 60, max_iterations: int = 10):
        self.logger.info('=' * 60)
        self.logger.info('STARTING RL TRADING BOT - TEST MODE')
        self.logger.info(f'Mode: {"PAPER TRADING" if self.paper_trading else "LIVE TRADING"}')
        self.logger.info(f'Initial Balance: ${self.balance:.2f}')
        self.logger.info(f'Max Iterations: {max_iterations}')
        self.logger.info('=' * 60)
        
        iteration = 0
        
        try:
            while iteration < max_iterations:
                iteration += 1
                self.logger.info(f'\n{"="*60}')
                self.logger.info(f'ITERATION {iteration}/{max_iterations}')
                self.logger.info(f'{"="*60}')
                
                # NO TIME CHECK - TRADE IMMEDIATELY FOR TESTING
                
                markets = self.get_available_markets()
                if not markets:
                    self.logger.warning('No markets available')
                    time.sleep(interval_seconds)
                    continue
                
                market = markets[0]
                self.logger.info(f'Market: {market["ticker"]}')
                self.logger.info(f'  YES: bid={market.get("yes_bid")}c ask={market.get("yes_ask")}c')
                self.logger.info(f'  NO:  bid={market.get("no_bid")}c ask={market.get("no_ask")}c')
                
                decision, size = self.make_decision(market)
                self.execute_trade(market, decision, size)
                
                self.logger.info(f'\nCurrent Status:')
                self.logger.info(f'  Balance: ${self.balance:.2f}')
                self.logger.info(f'  Total Trades: {len(self.trade_history)}')
                self.logger.info(f'  Open Positions: {len(self.positions)}')
                
                if iteration < max_iterations:
                    self.logger.info(f'\nSleeping {interval_seconds}s...')
                    time.sleep(interval_seconds)
                
        except KeyboardInterrupt:
            self.logger.info('\n*** STOPPED BY USER ***')
        finally:
            self.logger.info('\n' + '=' * 60)
            self.logger.info('FINAL SUMMARY')
            self.logger.info('=' * 60)
            self.logger.info(f'Total Iterations: {iteration}')
            self.logger.info(f'Total Trades Executed: {len(self.trade_history)}')
            self.logger.info(f'Starting Balance: $10000.00')
            self.logger.info(f'Final Balance: ${self.balance:.2f}')
            self.logger.info(f'P&L: ${self.balance - 10000:.2f}')
            self.logger.info('=' * 60)

if __name__ == '__main__':
    bot = RLTradingBot(
        model_path='../models/ppo_aggressive_final.zip',
        api_key='662e1c7e-55f3-4b92-87a5-a7c8d287d4f6',
        private_key_path='kalshi_private_key.pem',
        paper_trading=True
    )
    
    # Run 10 iterations for testing (about 10 minutes total)
    bot.run(interval_seconds=60, max_iterations=10)
