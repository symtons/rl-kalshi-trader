import numpy as np
import pandas as pd
from environment import KalshiTradingEnv
from typing import Tuple

class BaselineStrategy:
    '''Base class for baseline strategies'''
    def __init__(self, name: str):
        self.name = name
    
    def get_action(self, obs: np.ndarray, info: dict) -> Tuple[int, int]:
        '''Return (decision, size_idx)'''
        raise NotImplementedError

class RandomStrategy(BaselineStrategy):
    '''Completely random actions'''
    def __init__(self):
        super().__init__('Random')
    
    def get_action(self, obs: np.ndarray, info: dict) -> Tuple[int, int]:
        decision = np.random.randint(0, 5)  # 0=HOLD, 1=BUY_YES, 2=BUY_NO, 3=SELL_YES, 4=SELL_NO
        size_idx = np.random.randint(0, 5)  # 0, 10, 25, 50, 100 contracts
        return decision, size_idx

class AlwaysBuyYesStrategy(BaselineStrategy):
    '''Always buy YES at market price'''
    def __init__(self):
        super().__init__('Always Buy YES')
    
    def get_action(self, obs: np.ndarray, info: dict) -> Tuple[int, int]:
        decision = 1  # BUY_YES
        size_idx = 2  # 25 contracts (medium size)
        return decision, size_idx

class BuyAndHoldStrategy(BaselineStrategy):
    '''Buy YES once at start, then hold'''
    def __init__(self):
        super().__init__('Buy and Hold')
        self.has_bought = False
    
    def get_action(self, obs: np.ndarray, info: dict) -> Tuple[int, int]:
        if not self.has_bought:
            self.has_bought = True
            return 1, 3  # BUY_YES, 50 contracts
        return 0, 0  # HOLD

class MomentumStrategy(BaselineStrategy):
    '''Buy YES if price increasing, NO if decreasing'''
    def __init__(self):
        super().__init__('Momentum')
        self.prev_price = None
    
    def get_action(self, obs: np.ndarray, info: dict) -> Tuple[int, int]:
        # Extract current price from observation (first feature)
        current_price = obs[0] if len(obs) > 0 else 0
        
        if self.prev_price is None:
            self.prev_price = current_price
            return 0, 0  # HOLD on first step
        
        # If price going up, buy YES; if down, buy NO
        if current_price > self.prev_price * 1.001:  # 0.1% threshold
            decision = 1  # BUY_YES
            size_idx = 2  # 25 contracts
        elif current_price < self.prev_price * 0.999:
            decision = 2  # BUY_NO
            size_idx = 2  # 25 contracts
        else:
            decision = 0  # HOLD
            size_idx = 0
        
        self.prev_price = current_price
        return decision, size_idx

class HoldOnlyStrategy(BaselineStrategy):
    '''Never trade - just hold cash'''
    def __init__(self):
        super().__init__('Hold Only')
    
    def get_action(self, obs: np.ndarray, info: dict) -> Tuple[int, int]:
        return 0, 0  # Always HOLD

def evaluate_baseline(strategy: BaselineStrategy, env: KalshiTradingEnv, episodes: int = 1):
    '''Evaluate a baseline strategy'''
    results = []
    
    for ep in range(episodes):
        obs, info = env.reset()
        episode_reward = 0
        done = False
        
        portfolio_history = [info['portfolio_value']]
        
        while not done:
            action = strategy.get_action(obs, info)
            obs, reward, terminated, truncated, info = env.step(action)
            done = terminated or truncated
            episode_reward += reward
            portfolio_history.append(info['portfolio_value'])
        
        results.append({
            'strategy': strategy.name,
            'episode': ep,
            'final_value': info['portfolio_value'],
            'pnl': info['pnl'],
            'return_pct': (info['pnl'] / 10000) * 100,
            'num_trades': info['num_trades'],
            'win_rate': info['win_rate'],
            'portfolio_history': portfolio_history
        })
    
    return results

if __name__ == '__main__':
    print('Testing Baseline Strategies')
    print('=' * 60)
    
    # Load test data
    data_path = '../../data/raw/btc_15m_6months.csv'
    df = pd.read_csv(data_path)
    df['datetime'] = pd.to_datetime(df['datetime'])
    
    # Use test set (last 10%)
    test_size = int(len(df) * 0.1)
    test_df = df[-test_size:].reset_index(drop=True)
    
    print(f'Test data: {len(test_df)} rows')
    print()
    
    # Test each baseline
    strategies = [
        HoldOnlyStrategy(),
        RandomStrategy(),
        AlwaysBuyYesStrategy(),
        BuyAndHoldStrategy(),
        MomentumStrategy()
    ]
    
    all_results = []
    
    for strategy in strategies:
        print(f'Testing {strategy.name}...')
        env = KalshiTradingEnv(test_df, initial_balance=10000)
        results = evaluate_baseline(strategy, env, episodes=1)
        all_results.extend(results)
        
        result = results[0]
        print(f'  Final Value: ')
        print(f'  P&L:  ({result["return_pct"]:.2f}%)')
        print(f'  Trades: {result["num_trades"]}')
        print(f'  Win Rate: {result["win_rate"]*100:.1f}%')
        print()
    
    # Summary comparison
    print('=' * 60)
    print('BASELINE COMPARISON')
    print('=' * 60)
    
    df_results = pd.DataFrame(all_results)
    summary = df_results.groupby('strategy').agg({
        'return_pct': 'mean',
        'num_trades': 'mean',
        'win_rate': 'mean'
    }).round(2)
    
    summary = summary.sort_values('return_pct', ascending=False)
    
    print(summary)
    print()
    print('Now compare this to your RL agent!')
    print('RL Agent from earlier: P&L=-, 6 trades, 50% win rate')
