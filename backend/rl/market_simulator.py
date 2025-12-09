import numpy as np
from scipy.stats import norm
from typing import Tuple

class KalshiMarketSimulator:
    '''Simulate Kalshi binary option pricing'''
    
    def __init__(self, base_spread=0.02, volatility_factor=0.3):
        self.base_spread = base_spread
        self.volatility_factor = volatility_factor
    
    def generate_threshold(self, current_price: float) -> float:
        '''Generate a threshold near current price'''
        offset_pct = np.random.uniform(-0.05, 0.05)
        threshold = current_price * (1 + offset_pct)
        threshold = round(threshold / 100) * 100
        return threshold
    
    def calculate_implied_probability(self,
                                     current_price: float,
                                     threshold: float,
                                     time_to_expiry_hours: float,
                                     historical_volatility: float) -> float:
        '''Calculate implied probability that BTC will be above threshold'''
        if time_to_expiry_hours <= 0:
            return 1.0 if current_price >= threshold else 0.0
        
        distance = (current_price - threshold) / threshold
        volatility = max(historical_volatility, 0.01)
        time_factor = np.sqrt(time_to_expiry_hours / 24)
        
        z_score = distance / (volatility * time_factor * self.volatility_factor)
        probability = norm.cdf(z_score)
        probability = np.clip(probability, 0.05, 0.95)
        
        return probability
    
    def get_contract_prices(self,
                           current_price: float,
                           threshold: float,
                           time_to_expiry_hours: float,
                           historical_volatility: float) -> Tuple[float, float, float]:
        '''Get bid, ask, and mid prices for YES contract'''
        mid = self.calculate_implied_probability(
            current_price, threshold, time_to_expiry_hours, historical_volatility
        )
        
        spread = self.base_spread
        uncertainty_factor = 1 - abs(mid - 0.5) * 2
        spread = spread * (1 + uncertainty_factor)
        
        bid = mid - spread / 2
        ask = mid + spread / 2
        
        bid = np.clip(bid, 0.01, 0.99)
        ask = np.clip(ask, 0.01, 0.99)
        mid = (bid + ask) / 2
        
        return bid, ask, mid
    
    def resolve_contract(self, final_price: float, threshold: float) -> bool:
        '''Resolve contract: did BTC end above threshold?'''
        return final_price >= threshold
    
    def calculate_pnl(self,
                     position_type: str,
                     position_size: int,
                     entry_price: float,
                     contract_resolved: bool) -> float:
        '''Calculate P&L for a position'''
        if position_type == 'YES':
            payout_per_contract = 1.0 if contract_resolved else 0.0
        else:
            payout_per_contract = 1.0 if not contract_resolved else 0.0
        
        pnl = (payout_per_contract - entry_price) * position_size
        return pnl
