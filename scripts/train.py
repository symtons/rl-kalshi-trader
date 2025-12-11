import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import pandas as pd
import numpy as np
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import CheckpointCallback, EvalCallback, CallbackList, BaseCallback
from stable_baselines3.common.monitor import Monitor

from environment import KalshiTradingEnv

class TradingMetricsCallback(BaseCallback):
    '''Custom callback to log trading-specific metrics'''
    def __init__(self, verbose=0):
        super().__init__(verbose)
        self.episode_rewards = []
        self.episode_pnls = []
        
    def _on_step(self) -> bool:
        # Log metrics from info dict if episode ended
        if len(self.model.ep_info_buffer) > 0:
            for info in self.model.ep_info_buffer:
                if 'episode' in info:
                    # Standard episode info
                    self.logger.record('episode/reward', info['episode']['r'])
                    self.logger.record('episode/length', info['episode']['l'])
        return True

print('🚀 Training PPO Agent - 15 Minute Data with Improved Rewards')
print('=' * 60)

# Configuration
CONFIG = {
    'learning_rate': 3e-4,
    'n_steps': 2048,
    'batch_size': 64,
    'n_epochs': 10,
    'gamma': 0.99,
    'gae_lambda': 0.95,
    'clip_range': 0.2,
    'ent_coef': 0.05,  # Higher entropy for more exploration
    'vf_coef': 0.5,
    'max_grad_norm': 0.5,
    'total_timesteps': 1000000,  # 1M timesteps for more data
    'initial_balance': 10000
}

print('Configuration:')
for key, value in CONFIG.items():
    print(f'  {key}: {value}')
print()

# Load 15-minute data
print('Loading 15-minute data...')
data_path = os.path.join('..', '..', 'data', 'raw', 'btc_15m_6months.csv')

try:
    df = pd.read_csv(data_path)
    df['datetime'] = pd.to_datetime(df['datetime'])
    print(f'✓ Loaded {len(df):,} rows (15-min candles)')
except FileNotFoundError:
    print(f'❌ Error: File not found at {data_path}')
    print('Please run download_data.py first to download 15-minute data')
    sys.exit(1)

# Split data: 80% train, 10% validation, 10% test
train_size = int(len(df) * 0.8)
val_size = int(len(df) * 0.1)

train_df = df[:train_size].reset_index(drop=True)
val_df = df[train_size:train_size+val_size].reset_index(drop=True)
test_df = df[train_size+val_size:].reset_index(drop=True)

print(f'✓ Train: {len(train_df):,} rows ({len(train_df)//96:.1f} days)')
print(f'✓ Validation: {len(val_df):,} rows ({len(val_df)//96:.1f} days)')
print(f'✓ Test: {len(test_df):,} rows ({len(test_df)//96:.1f} days)')
print()

# Create environments
print('Creating environments...')
train_env = Monitor(KalshiTradingEnv(train_df, initial_balance=CONFIG['initial_balance']))
val_env = Monitor(KalshiTradingEnv(val_df, initial_balance=CONFIG['initial_balance']))
print('✓ Environments created')
print()

# Create directories
os.makedirs('../../models/checkpoints_15m', exist_ok=True)
os.makedirs('../../models/best_15m', exist_ok=True)
os.makedirs('../../logs/tensorboard_15m', exist_ok=True)
os.makedirs('../../logs/eval_15m', exist_ok=True)

print('📁 Output directories:')
print(f'  Checkpoints: models/checkpoints_15m/')
print(f'  Best model: models/best_15m/')
print(f'  TensorBoard: logs/tensorboard_15m/')
print()

# Setup callbacks
print('Setting up callbacks...')

# Save checkpoints every 10k steps
checkpoint_callback = CheckpointCallback(
    save_freq=10000,
    save_path='../../models/checkpoints_15m/',
    name_prefix='ppo_kalshi_15m',
    verbose=1
)

# Evaluate on validation set every 5k steps
eval_callback = EvalCallback(
    val_env,
    best_model_save_path='../../models/best_15m/',
    log_path='../../logs/eval_15m/',
    eval_freq=5000,
    deterministic=True,
    n_eval_episodes=5,
    verbose=1
)

# Custom trading metrics callback
metrics_callback = TradingMetricsCallback()

callbacks = CallbackList([checkpoint_callback, eval_callback, metrics_callback])
print('✓ Callbacks configured')
print()

# Create PPO model
print('Creating PPO model...')
model = PPO(
    'MlpPolicy',
    train_env,
    learning_rate=CONFIG['learning_rate'],
    n_steps=CONFIG['n_steps'],
    batch_size=CONFIG['batch_size'],
    n_epochs=CONFIG['n_epochs'],
    gamma=CONFIG['gamma'],
    gae_lambda=CONFIG['gae_lambda'],
    clip_range=CONFIG['clip_range'],
    ent_coef=CONFIG['ent_coef'],
    vf_coef=CONFIG['vf_coef'],
    max_grad_norm=CONFIG['max_grad_norm'],
    verbose=1,
    tensorboard_log='../../logs/tensorboard_15m/',
    device='auto'
)

print('✓ Model created')
print(f'  Policy: {model.policy.__class__.__name__}')
print(f'  Device: {model.device}')
print(f'  Total parameters: {sum(p.numel() for p in model.policy.parameters()):,}')
print()

# Display training info
print('🏋️ Starting training...')
print('=' * 60)
print(f'Total timesteps: {CONFIG["total_timesteps"]:,}')
print(f'Expected episodes: ~{CONFIG["total_timesteps"] // len(train_df):,}')
print(f'Training data: ~{len(train_df)//96:.1f} days of 15-min candles')
print()
print('Key improvements in this version:')
print('  ✓ 4x more data (15-min vs 1-hour)')
print('  ✓ Reward for profitable trades')
print('  ✓ Penalty for holding (encourages action)')
print('  ✓ Higher entropy coefficient (more exploration)')
print('  ✓ Better reward shaping')
print()
print('Estimated training time: 2-3 hours')
print('Monitor progress at: http://localhost:6006')
print('=' * 60)
print()

# Train
try:
    model.learn(
        total_timesteps=CONFIG['total_timesteps'],
        callback=callbacks,
        progress_bar=True,
        tb_log_name='ppo_15m_run'
    )
    
    print('\n' + '=' * 60)
    print('✅ Training complete!')
    print('=' * 60)
    
    # Save final model
    final_model_path = '../../models/ppo_kalshi_15m_final'
    model.save(final_model_path)
    print(f'✓ Final model saved to: {final_model_path}.zip')
    
    # Save configuration
    import json
    config_path = '../../models/ppo_kalshi_15m_config.json'
    with open(config_path, 'w') as f:
        json.dump(CONFIG, f, indent=2)
    print(f'✓ Config saved to: {config_path}')
    
except KeyboardInterrupt:
    print('\n' + '=' * 60)
    print('⚠️ Training interrupted by user')
    print('=' * 60)
    
    interrupted_model_path = '../../models/ppo_kalshi_15m_interrupted'
    model.save(interrupted_model_path)
    print(f'✓ Model saved to: {interrupted_model_path}.zip')

except Exception as e:
    print(f'\n❌ Error during training: {e}')
    import traceback
    traceback.print_exc()
    
    error_model_path = '../../models/ppo_kalshi_15m_error'
    model.save(error_model_path)
    print(f'✓ Model saved to: {error_model_path}.zip')

print('\n' + '=' * 60)
print('Next steps:')
print('  1. Evaluate model: python evaluate.py')
print('  2. View TensorBoard: tensorboard --logdir=../../logs/tensorboard_15m')
print('  3. Check best model in: models/best_15m/')
print('=' * 60)
