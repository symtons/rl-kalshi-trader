import gymnasium as gym
from gymnasium import spaces
import numpy as np
import pandas as pd
from typing import Dict, Tuple, Any

# Handle both relative and absolute imports
try:
    from .features import FeatureEngineering
    from .market_simulator import KalshiMarketSimulator
except ImportError:
    from features import FeatureEngineering
    from market_simulator import KalshiMarketSimulator

class KalshiTradingEnv(gym.Env):
    '''Kalshi Bitcoin Trading Environment for RL'''
    metadata = {'render_modes': ['human']}
    
    def __init__(self, price_data: pd.DataFrame, initial_balance: float = 10000,
                 max_position_size: int = 100, trading_hours: Tuple[int, int] = (9, 24)):
        super().__init__()
        
        self.price_data = price_data
        self.initial_balance = initial_balance
        self.max_position_size = max_position_size
        self.trading_start_hour = trading_hours[0]
        self.trading_end_hour = trading_hours[1]
        
        self.feature_engineer = FeatureEngineering(lookback_window=24)
        self.market_sim = KalshiMarketSimulator()
        
        self.action_space = spaces.MultiDiscrete([5, 5])
        self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(50,), dtype=np.float32)
        
        self.current_step = 0
        self.balance = initial_balance
        self.positions = []
        self.trade_history = []
        self.portfolio_values = [initial_balance]
        self.max_portfolio_value = initial_balance
        
    def reset(self, seed=None, options=None) -> Tuple[np.ndarray, Dict]:
        super().reset(seed=seed)
        
        self.current_step = 24
        self.balance = self.initial_balance
        self.positions = []
        self.trade_history = []
        self.portfolio_values = [self.initial_balance]
        self.max_portfolio_value = self.initial_balance
        
        observation = self._get_observation()
        info = self._get_info()
        
        return observation, info
    
    def step(self, action: np.ndarray) -> Tuple[np.ndarray, float, bool, bool, Dict]:
        decision, size_idx = action
        position_size = [0, 10, 25, 50, 100][size_idx]
        
        reward = self._execute_trade(decision, position_size)
        self._update_positions()
        self.current_step += 1
        
        portfolio_value = self._calculate_portfolio_value()
        self.portfolio_values.append(portfolio_value)
        self.max_portfolio_value = max(self.max_portfolio_value, portfolio_value)
        
        terminated = (self.current_step >= len(self.price_data) - 1 or
                     portfolio_value <= 0.3 * self.initial_balance)
        truncated = False
        
        observation = self._get_observation()
        info = self._get_info()
        
        return observation, reward, terminated, truncated, info
    
    def _get_observation(self) -> np.ndarray:
        prices = self.price_data['close'].values
        price_features = self.feature_engineer.extract_features(prices, self.current_step)
        
        current_time = self.price_data.iloc[self.current_step]['datetime']
        hour = current_time.hour if hasattr(current_time, 'hour') else 12
        
        time_features = {
            'hour_of_day': hour, 'time_to_expiry': 1.0, 'is_near_expiry': 0,
            'implied_probability': 0.5, 'bid_ask_spread': 0.02
        }
        
        position_features = {
            'num_positions': len(self.positions),
            'total_exposure': sum(p['size'] * p['entry_price'] for p in self.positions),
            'unrealized_pnl': self._calculate_unrealized_pnl(),
            'portfolio_value': self._calculate_portfolio_value(),
            'win_rate': self._calculate_win_rate()
        }
        
        state = self.feature_engineer.create_state_vector(
            price_features, time_features, position_features
        )
        
        return state
    
    def _execute_trade(self, decision: int, position_size: int) -> float:
        if decision == 0 or position_size == 0:
            return 0.0
        
        current_price = self.price_data.iloc[self.current_step]['close']
        threshold = self.market_sim.generate_threshold(current_price)
        
        volatility = self.feature_engineer.calculate_volatility(
            self.price_data['close'].values[:self.current_step]
        )
        
        bid, ask, mid = self.market_sim.get_contract_prices(
            current_price, threshold, time_to_expiry_hours=1.0,
            historical_volatility=volatility
        )
        
        if decision == 1:
            position_type = 'YES'
            entry_price = ask
        elif decision == 2:
            position_type = 'NO'
            entry_price = ask
        elif decision == 3:
            position_type = 'YES_SHORT'
            entry_price = bid
        elif decision == 4:
            position_type = 'NO_SHORT'
            entry_price = bid
        else:
            return 0.0
        
        cost = entry_price * position_size
        if cost > self.balance:
            return -1.0
        
        self.balance -= cost
        
        position = {
            'type': position_type, 'size': position_size, 'entry_price': entry_price,
            'entry_step': self.current_step, 'threshold': threshold,
            'expiry_step': self.current_step + 1
        }
        
        self.positions.append(position)
        return -0.05
    
    def _update_positions(self):
        current_price = self.price_data.iloc[self.current_step]['close']
        positions_to_remove = []
        
        for i, pos in enumerate(self.positions):
            if self.current_step >= pos['expiry_step']:
                contract_resolved = self.market_sim.resolve_contract(
                    current_price, pos['threshold']
                )
                
                pnl = self.market_sim.calculate_pnl(
                    pos['type'], pos['size'], pos['entry_price'], contract_resolved
                )
                
                self.balance += (pos['entry_price'] * pos['size'] + pnl)
                
                self.trade_history.append({
                    'step': self.current_step, 'type': pos['type'],
                    'size': pos['size'], 'pnl': pnl
                })
                
                positions_to_remove.append(i)
        
        for i in reversed(positions_to_remove):
            self.positions.pop(i)
    
    def _calculate_portfolio_value(self) -> float:
        return self.balance + self._calculate_unrealized_pnl()
    
    def _calculate_unrealized_pnl(self) -> float:
        if len(self.positions) == 0:
            return 0.0
        
        unrealized = 0.0
        for pos in self.positions:
            time_left = pos['expiry_step'] - self.current_step
            if time_left > 0:
                unrealized += pos['size'] * pos['entry_price'] * 0.5
        
        return unrealized
    
    def _calculate_win_rate(self) -> float:
        if len(self.trade_history) == 0:
            return 0.5
        
        wins = sum(1 for trade in self.trade_history if trade['pnl'] > 0)
        return wins / len(self.trade_history)
    
    def _get_info(self) -> Dict:
        return {
            'portfolio_value': self._calculate_portfolio_value(),
            'balance': self.balance,
            'num_positions': len(self.positions),
            'num_trades': len(self.trade_history),
            'win_rate': self._calculate_win_rate(),
            'pnl': self._calculate_portfolio_value() - self.initial_balance
        }
