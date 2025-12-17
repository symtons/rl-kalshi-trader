import gymnasium as gym
from gymnasium import spaces
import numpy as np
import pandas as pd
from typing import Dict, Tuple, Any

try:
    from .features import FeatureEngineering
    from .market_simulator import KalshiMarketSimulator
except ImportError:
    from features import FeatureEngineering
    from market_simulator import KalshiMarketSimulator

class KalshiTradingEnv(gym.Env):
    '''Kalshi Trading Environment V3 - AGGRESSIVE trading incentives'''
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
        
        # Action space: [decision, position_size]
        self.action_space = spaces.MultiDiscrete([5, 5])
        self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(50,), dtype=np.float32)
        
        self.current_step = 0
        self.balance = initial_balance
        self.positions = []
        self.trade_history = []
        self.portfolio_values = [initial_balance]
        self.max_portfolio_value = initial_balance
        self.steps_without_trade = 0
        
    def reset(self, seed=None, options=None) -> Tuple[np.ndarray, Dict]:
        super().reset(seed=seed)
        
        self.current_step = 24
        self.balance = self.initial_balance
        self.positions = []
        self.trade_history = []
        self.portfolio_values = [self.initial_balance]
        self.max_portfolio_value = self.initial_balance
        self.steps_without_trade = 0
        
        observation = self._get_observation()
        info = self._get_info()
        
        return observation, info
    
    def step(self, action: np.ndarray) -> Tuple[np.ndarray, float, bool, bool, Dict]:
        decision, size_idx = action
        position_size = [0, 10, 25, 50, 100][size_idx]
        
        # Track steps without trading
        if decision == 0:
            self.steps_without_trade += 1
        else:
            self.steps_without_trade = 0
        
        # Execute trade
        self._execute_trade(decision, position_size)
        
        # Update positions
        pnl_from_resolved = self._update_positions()
        
        # Move to next step
        self.current_step += 1
        
        # Calculate portfolio value
        prev_value = self.portfolio_values[-1]
        portfolio_value = self._calculate_portfolio_value()
        self.portfolio_values.append(portfolio_value)
        self.max_portfolio_value = max(self.max_portfolio_value, portfolio_value)
        
        # AGGRESSIVE REWARD CALCULATION
        reward = self._calculate_reward(prev_value, portfolio_value, pnl_from_resolved, decision)
        
        # Check if done
        terminated = (
            self.current_step >= len(self.price_data) - 1 or
            portfolio_value <= 0.2 * self.initial_balance  # Allow more drawdown
        )
        truncated = False
        
        observation = self._get_observation()
        info = self._get_info()
        
        return observation, reward, terminated, truncated, info
    
    def _calculate_reward(self, prev_value, current_value, pnl_from_resolved, decision):
        '''AGGRESSIVE reward that strongly encourages trading'''
        reward = 0.0
        
        # Main reward: P&L change (scaled aggressively)
        pnl_change = current_value - prev_value
        reward += pnl_change / 3  # Strong scaling
        
        # HUGE bonus for profitable resolved trades
        if pnl_from_resolved > 0:
            reward += 50.0  # Massive bonus
        elif pnl_from_resolved < 0:
            reward -= 5.0  # Small loss penalty
        
        # STRONG penalty for HOLD
        if decision == 0:
            reward -= 2.0  # Heavy penalty for holding
            
            # ESCALATING penalty for consecutive holds
            if self.steps_without_trade > 10:
                reward -= 5.0
            if self.steps_without_trade > 50:
                reward -= 10.0
        else:
            reward += 1.0  # BONUS for taking action
        
        # Bonus for having open positions
        if len(self.positions) > 0:
            reward += 0.5
        
        # Bonus for trading activity
        if len(self.trade_history) > 0:
            recent_trades = len([t for t in self.trade_history if t['step'] > self.current_step - 100])
            reward += 0.1 * recent_trades
        
        # Only penalize severe drawdowns
        drawdown = (self.max_portfolio_value - current_value) / self.max_portfolio_value
        if drawdown > 0.3:  # Only if > 30% drawdown
            reward -= 20.0 * drawdown
        
        return reward
    
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
            return 0.0  # Just skip if can't afford
        
        self.balance -= cost
        
        position = {
            'type': position_type, 'size': position_size, 'entry_price': entry_price,
            'entry_step': self.current_step, 'threshold': threshold,
            'expiry_step': self.current_step + 1
        }
        
        self.positions.append(position)
        return 0.0
    
    def _update_positions(self):
        current_price = self.price_data.iloc[self.current_step]['close']
        positions_to_remove = []
        total_pnl = 0.0
        
        for i, pos in enumerate(self.positions):
            if self.current_step >= pos['expiry_step']:
                contract_resolved = self.market_sim.resolve_contract(
                    current_price, pos['threshold']
                )
                
                pnl = self.market_sim.calculate_pnl(
                    pos['type'], pos['size'], pos['entry_price'], contract_resolved
                )
                
                self.balance += (pos['entry_price'] * pos['size'] + pnl)
                total_pnl += pnl
                
                self.trade_history.append({
                    'step': self.current_step, 'type': pos['type'],
                    'size': pos['size'], 'pnl': pnl
                })
                
                positions_to_remove.append(i)
        
        for i in reversed(positions_to_remove):
            self.positions.pop(i)
        
        return total_pnl
    
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
