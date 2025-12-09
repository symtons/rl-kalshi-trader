import sys
sys.path.append('../backend')

import pandas as pd
import numpy as np
from rl.environment import KalshiTradingEnv
from gymnasium.utils.env_checker import check_env

print('🧪 Testing RL Environment')
print('=' * 60)

# Load data
print('Loading data...')
df = pd.read_csv('../data/raw/btc_1h_6months.csv')
df['datetime'] = pd.to_datetime(df['datetime'])
print(f'✓ Loaded {len(df)} rows')

# Create environment
print('\nCreating environment...')
env = KalshiTradingEnv(df, initial_balance=10000)
print('✓ Environment created')

# Check environment
print('\nChecking Gym API compliance...')
try:
    check_env(env, warn=True)
    print('✓ Environment passes Gym checks')
except Exception as e:
    print(f'⚠️ Warning: {e}')

# Test reset
print('\nTesting reset...')
obs, info = env.reset()
print(f'✓ Observation shape: {obs.shape}')
print(f'✓ Info: {info}')

# Test random actions
print('\nTesting random actions...')
for i in range(10):
    action = env.action_space.sample()
    obs, reward, terminated, truncated, info = env.step(action)
    
    print(f'Step {i+1}: Portfolio=${info["portfolio_value"]:.2f}, Reward={reward:.2f}')
    
    if terminated:
        print('Episode terminated')
        break

print('\n' + '=' * 60)
print('✅ Environment test complete!')