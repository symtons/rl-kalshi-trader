import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from stable_baselines3 import PPO
from environment import KalshiTradingEnv

print('📊 Evaluating Trained PPO Agent (15-min data)')
print('=' * 60)

# Load 15-minute data
print('Loading data...')
data_path = os.path.join('..', '..', 'data', 'raw', 'btc_15m_6months.csv')
df = pd.read_csv(data_path)
df['datetime'] = pd.to_datetime(df['datetime'])

# Use test set (last 10%)
test_size = int(len(df) * 0.1)
test_df = df[-test_size:].reset_index(drop=True)
print(f'✓ Test data: {len(test_df)} rows')

# Load the 15-minute trained model
print('Loading trained model...')
model_path = '../../models/ppo_kalshi_15m_final'
try:
    model = PPO.load(model_path)
    print(f'✓ Model loaded from: {model_path}')
except Exception as e:
    print(f'❌ Error loading model: {e}')
    print(f'\nTrying to find available models...')
    
    # Check what models exist
    import glob
    models = glob.glob('../../models/*.zip')
    print(f'Available models: {[os.path.basename(m) for m in models]}')
    sys.exit(1)

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
    action, _states = model.predict(obs, deterministic=True)
    obs, reward, terminated, truncated, info = env.step(action)
    done = terminated or truncated
    
    episode_reward += reward
    portfolio_history.append(info['portfolio_value'])
    pnl_history.append(info['pnl'])
    actions_taken.append(action)
    
    step += 1
    
    if step % 100 == 0:
        print(f'Step {step}: Portfolio={info["portfolio_value"]:.2f}, P&L={info["pnl"]:.2f}, Trades={info["num_trades"]}')

print('-' * 60)
print()

# Final results
print('📈 Final Results:')
print('=' * 60)
print(f'Total Steps: {step}')
print(f'Total Reward: {episode_reward:.2f}')
print(f'Final Portfolio Value: {info["portfolio_value"]:.2f}')
print(f'Total P&L: {info["pnl"]:.2f}')
print(f'Return: {(info["pnl"] / 10000 * 100):.2f}%')
print(f'Total Trades: {info["num_trades"]}')
print(f'Win Rate: {info["win_rate"]*100:.2f}%')
print()

# Risk metrics
if len(portfolio_history) > 1:
    returns = np.diff(portfolio_history) / np.array(portfolio_history[:-1])
    returns = returns[~np.isnan(returns)]  # Remove NaN values
    
    if len(returns) > 0 and np.std(returns) > 0:
        sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(len(test_df))
    else:
        sharpe_ratio = 0
    
    max_vals = [max(portfolio_history[:i+1]) for i in range(len(portfolio_history))]
    drawdowns = [(v - max_vals[i]) / max_vals[i] if max_vals[i] > 0 else 0 for i, v in enumerate(portfolio_history)]
    max_drawdown = min(drawdowns) if drawdowns else 0
    
    print('📊 Risk Metrics:')
    print('=' * 60)
    print(f'Sharpe Ratio: {sharpe_ratio:.2f}')
    print(f'Max Drawdown: {max_drawdown*100:.2f}%')
    print(f'Volatility: {np.std(returns)*100:.2f}%')
    print()

# Action distribution
if len(actions_taken) > 0:
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

ax1.plot(portfolio_history, linewidth=2, color='blue')
ax1.axhline(y=10000, color='gray', linestyle='--', label='Initial Balance')
ax1.set_title('Portfolio Value Over Time (15-min Model)', fontsize=14, fontweight='bold')
ax1.set_xlabel('Step')
ax1.set_ylabel('Portfolio Value')
ax1.grid(True, alpha=0.3)
ax1.legend()

color = 'green' if info['pnl'] > 0 else 'red'
ax2.plot(pnl_history, linewidth=2, color=color)
ax2.axhline(y=0, color='gray', linestyle='--')
ax2.set_title('Cumulative P&L', fontsize=14, fontweight='bold')
ax2.set_xlabel('Step')
ax2.set_ylabel('P&L')
ax2.grid(True, alpha=0.3)

plt.tight_layout()
os.makedirs('../../logs', exist_ok=True)
plt.savefig('../../logs/evaluation_results_15m.png', dpi=300, bbox_inches='tight')
print('✓ Chart saved to logs/evaluation_results_15m.png')

print('\n' + '=' * 60)
print('✅ Evaluation complete!')
