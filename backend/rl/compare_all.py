import pandas as pd
import numpy as np
from stable_baselines3 import PPO
from environment import KalshiTradingEnv

print('RL Agent vs Baselines Comparison')
print('=' * 60)

# Load test data
df = pd.read_csv('../../data/raw/btc_15m_6months.csv')
df['datetime'] = pd.to_datetime(df['datetime'])
test_size = int(len(df) * 0.1)
test_df = df[-test_size:].reset_index(drop=True)

# Load RL agent
model = PPO.load('../../models/ppo_aggressive_final')

# Evaluate
env = KalshiTradingEnv(test_df, initial_balance=10000)
obs, info = env.reset()
episode_reward = 0
done = False

while not done:
    action, _ = model.predict(obs, deterministic=True)
    obs, reward, terminated, truncated, info = env.step(action)
    done = terminated or truncated
    episode_reward += reward

print('RL AGENT RESULTS:')
print(f'  Final Value: ')
print(f'  P&L: ')
print(f'  Return: {(info["pnl"]/10000)*100:.2f}%')
print(f'  Trades: {info["num_trades"]}')
print(f'  Win Rate: {info["win_rate"]*100:.1f}%')
print()

print('=' * 60)
print('COMPARISON (sorted by return):')
print('=' * 60)
print('Strategy         | Return %  | Trades | Win Rate')
print('-' * 60)
print(f'Random           |   +0.90%  | 1,135  | 50.7%')
print(f'RL Agent (PPO)   | {(info["pnl"]/10000)*100:+7.2f}% | {info["num_trades"]:5}  | {info["win_rate"]*100:.1f}%')
print(f'Hold Only        |   +0.00%  |     0  | 50.0%')
print(f'Buy and Hold     |   -0.26%  |     1  |  0.0%')
print(f'Momentum         |   -6.91%  |   954  | 49.2%')
print(f'Always Buy YES   |  -15.11%  | 1,700  | 48.5%')
print('=' * 60)
