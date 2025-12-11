import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from stable_baselines3 import PPO
from environment import KalshiTradingEnv

print('📊 Evaluating Trained PPO Agent')
print('=' * 60)

# Load data
print('Loading data...')
data_path = os.path.join('..', '..', 'data', 'raw', 'btc_1h_6months.csv')
df = pd.read_csv(data_path)
df['datetime'] = pd.to_datetime(df['datetime'])

# Use test set (last 10%)
test_size = int(len(df) * 0.1)
test_df = df[-test_size:].reset_index(drop=True)
print(f'✓ Test data: {len(test_df)} rows')

# Load trained model
print('Loading trained model...')
model = PPO.load('../../models/ppo_kalshi_final')
print('✓ Model loaded')
print()

# Create test environment
env = KalshiTradingEnv(test_df, initial_balance=10000)

# Run evaluation
print('Running evaluation...')
print('-' * 60)

obs, info = env.reset()
episode_reward = 0
done = False
step = 0

portfolio_history = [info['portfolio_value']]
pnl_history = [info['pnl']]
actions_taken = []

while not done:
    # Get action from trained agent
    action, _states = model.predict(obs, deterministic=True)
    
    # Take step
    obs, reward, terminated, truncated, info = env.step(action)
    done = terminated or truncated
    
    episode_reward += reward
    portfolio_history.append(info['portfolio_value'])
    pnl_history.append(info['pnl'])
    actions_taken.append(action)
    
    step += 1
    
    if step % 100 == 0:
        print(f'Step {step}: Portfolio=, P&L=, Trades={info["num_trades"]}')

print('-' * 60)
print()

# Final results
print('📈 Final Results:')
print('=' * 60)
print(f'Total Steps: {step}')
print(f'Total Reward: {episode_reward:.2f}')
print(f'Final Portfolio Value: ')
print(f'Total P&L: ')
print(f'Return: {(info["pnl"] / 10000 * 100):.2f}%')
print(f'Total Trades: {info["num_trades"]}')
print(f'Win Rate: {info["win_rate"]*100:.2f}%')
print()

# Calculate additional metrics
returns = np.diff(portfolio_history) / portfolio_history[:-1]
sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(len(test_df)) if np.std(returns) > 0 else 0
max_drawdown = np.min([(v - max(portfolio_history[:i+1])) / max(portfolio_history[:i+1]) for i, v in enumerate(portfolio_history)])

print('📊 Risk Metrics:')
print('=' * 60)
print(f'Sharpe Ratio: {sharpe_ratio:.2f}')
print(f'Max Drawdown: {max_drawdown*100:.2f}%')
print(f'Volatility: {np.std(returns)*100:.2f}%')
print()

# Action distribution
unique, counts = np.unique([a[0] for a in actions_taken], return_counts=True)
action_names = ['HOLD', 'BUY_YES', 'BUY_NO', 'SELL_YES', 'SELL_NO']
print('🎯 Action Distribution:')
print('=' * 60)
for act, count in zip(unique, counts):
    print(f'{action_names[act]}: {count} ({count/len(actions_taken)*100:.1f}%)')
print()

# Create visualization
print('Creating performance chart...')
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))

# Portfolio value over time
ax1.plot(portfolio_history, linewidth=2, color='blue')
ax1.axhline(y=10000, color='gray', linestyle='--', label='Initial Balance')
ax1.set_title('Portfolio Value Over Time', fontsize=14, fontweight='bold')
ax1.set_xlabel('Step')
ax1.set_ylabel('Portfolio Value ($)')
ax1.grid(True, alpha=0.3)
ax1.legend()

# P&L over time
ax2.plot(pnl_history, linewidth=2, color='green' if info['pnl'] > 0 else 'red')
ax2.axhline(y=0, color='gray', linestyle='--')
ax2.set_title('Cumulative P&L', fontsize=14, fontweight='bold')
ax2.set_xlabel('Step')
ax2.set_ylabel('P&L ($)')
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('../../logs/evaluation_results.png', dpi=300, bbox_inches='tight')
print('✓ Chart saved to logs/evaluation_results.png')

print('\n' + '=' * 60)
print('✅ Evaluation complete!')
