import numpy as np
import pandas as pd
from typing import Dict, List

class FeatureEngineering:
    '''
    Extract features from BTC price data for RL state
    '''
    
    def __init__(self, lookback_window=20):
        self.lookback_window = lookback_window
    
    def calculate_returns(self, prices: np.ndarray) -> np.ndarray:
        '''Calculate percentage returns'''
        returns = np.diff(prices) / prices[:-1]
        return np.append([0], returns)
    
    def calculate_volatility(self, returns: np.ndarray, window: int = 20) -> float:
        '''Calculate rolling volatility'''
        if len(returns) < window:
            return 0.0
        return np.std(returns[-window:])
    
    def calculate_momentum(self, prices: np.ndarray, window: int = 10) -> float:
        '''Calculate price momentum'''
        if len(prices) < window:
            return 0.0
        return (prices[-1] - prices[-window]) / prices[-window]
    
    def calculate_rsi(self, prices: np.ndarray, period: int = 14) -> float:
        '''Calculate Relative Strength Index'''
        if len(prices) < period + 1:
            return 50.0
        
        deltas = np.diff(prices[-period-1:])
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains)
        avg_loss = np.mean(losses)
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def calculate_bollinger_position(self, prices: np.ndarray, window: int = 20) -> float:
        '''Calculate position relative to Bollinger Bands'''
        if len(prices) < window:
            return 0.5
        
        recent_prices = prices[-window:]
        mean = np.mean(recent_prices)
        std = np.std(recent_prices)
        
        if std == 0:
            return 0.5
        
        upper_band = mean + 2 * std
        lower_band = mean - 2 * std
        
        current = prices[-1]
        if upper_band == lower_band:
            return 0.5
        
        position = (current - lower_band) / (upper_band - lower_band)
        return np.clip(position, 0, 1)
    
    def extract_features(self, price_history: np.ndarray, current_step: int) -> Dict[str, float]:
        '''Extract all features for current state'''
        start_idx = max(0, current_step - self.lookback_window)
        prices = price_history[start_idx:current_step + 1]
        
        if len(prices) < 2:
            return {
                'current_price': price_history[current_step] if len(price_history) > current_step else 0,
                'returns_1h': 0, 'returns_4h': 0, 'returns_12h': 0,
                'volatility': 0, 'momentum': 0, 'rsi': 50,
                'bollinger_position': 0.5
            }
        
        returns = self.calculate_returns(prices)
        
        features = {
            'current_price': float(prices[-1]),
            'returns_1h': float(returns[-1]) if len(returns) > 0 else 0,
            'returns_4h': float(np.mean(returns[-4:])) if len(returns) >= 4 else 0,
            'returns_12h': float(np.mean(returns[-12:])) if len(returns) >= 12 else 0,
            'volatility': float(self.calculate_volatility(returns)),
            'momentum': float(self.calculate_momentum(prices)),
            'rsi': float(self.calculate_rsi(prices)),
            'bollinger_position': float(self.calculate_bollinger_position(prices))
        }
        
        return features
    
    def create_state_vector(self, 
                           price_features: Dict[str, float],
                           time_features: Dict[str, float],
                           position_features: Dict[str, float]) -> np.ndarray:
        '''Combine all features into state vector'''
        state = np.zeros(50, dtype=np.float32)
        
        # Price features (0-19)
        state[0] = price_features.get('current_price', 0) / 100000
        state[1] = price_features.get('returns_1h', 0) * 100
        state[2] = price_features.get('returns_4h', 0) * 100
        state[3] = price_features.get('returns_12h', 0) * 100
        state[4] = price_features.get('volatility', 0) * 100
        state[5] = price_features.get('momentum', 0) * 10
        state[6] = price_features.get('rsi', 50) / 100
        state[7] = price_features.get('bollinger_position', 0.5)
        
        # Position features (20-34)
        state[20] = position_features.get('num_positions', 0) / 10
        state[21] = position_features.get('total_exposure', 0) / 1000
        state[22] = position_features.get('unrealized_pnl', 0) / 1000
        state[23] = position_features.get('portfolio_value', 10000) / 10000
        state[24] = position_features.get('win_rate', 0.5)
        
        # Time features (35-39)
        state[35] = time_features.get('hour_of_day', 12) / 24
        state[36] = time_features.get('time_to_expiry', 1) / 24
        state[37] = time_features.get('is_near_expiry', 0)
        
        # Market features (40-49)
        state[40] = price_features.get('current_price', 0) / 100000
        state[41] = time_features.get('implied_probability', 0.5)
        state[42] = time_features.get('bid_ask_spread', 0.02)
        
        return state
