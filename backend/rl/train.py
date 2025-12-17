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

print('🚀 Training PPO Agent - AGGRESSIVE Rewards + GPU')
print('=' * 60)

# Configuration with higher entropy for exploration
CONFIG = {
    'learning_rate': 3e-4,
    'n_steps': 2048,
    'batch_size': 64,
    'n_epochs': 10,
    'gamma': 0.99,
    'gae_lambda': 0.95,
    'clip_range': 0.2,
    'ent_coef': 0.1,  # Even higher entropy for exploration
    'vf_coef': 0.5,
    'max_grad_norm': 0.5,
    'total_timesteps': 1000000,
    'initial_balance': 10000
}

print('Configuration:')
for key, value in CONFIG.items():
    print(f'  {key}: {value}')
print()

# Check GPU
import torch
print('🔥 GPU Check:')
print(f'  CUDA available: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'  GPU: {torch.cuda.get_device_name(0)}')
    print(f'  GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB')
else:
    print('  Using CPU (training will be slower)')
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
os.makedirs('../../models/checkpoints_aggressive', exist_ok=True)
os.makedirs('../../models/best_aggressive', exist_ok=True)
os.makedirs('../../logs/tensorboard_aggressive', exist_ok=True)
os.makedirs('../../logs/eval_aggressive', exist_ok=True)

print('📁 Output directories:')
print(f'  Checkpoints: models/checkpoints_aggressive/')
print(f'  Best model: models/best_aggressive/')
print(f'  TensorBoard: logs/tensorboard_aggressive/')
print()

# Setup callbacks
print('Setting up callbacks...')

checkpoint_callback = CheckpointCallback(
    save_freq=10000,
    save_path='../../models/checkpoints_aggressive/',
    name_prefix='ppo_aggressive',
    verbose=1
)

eval_callback = EvalCallback(
    val_env,
    best_model_save_path='../../models/best_aggressive/',
    log_path='../../logs/eval_aggressive/',
    eval_freq=5000,
    deterministic=True,
    n_eval_episodes=5,
    verbose=1
)

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
    tensorboard_log='../../logs/tensorboard_aggressive/',
    device='auto'  # Automatically uses GPU if available
)

print('✓ Model created')
print(f'  Policy: {model.policy.__class__.__name__}')
print(f'  Device: {model.device}')
print(f'  Total parameters: {sum(p.numel() for p in model.policy.parameters()):,}')
print()

# Display training info
print('🏋️ Starting AGGRESSIVE training...')
print('=' * 60)
print(f'Total timesteps: {CONFIG["total_timesteps"]:,}')
print(f'Expected episodes: ~{CONFIG["total_timesteps"] // len(train_df):,}')
print(f'Training data: ~{len(train_df)//96:.1f} days of 15-min candles')
print()
print('🔥 AGGRESSIVE Reward Improvements:')
print('  ✓ +50 reward for winning trades (was +5)')
print('  ✓ -2 reward for holding (was -0.1)')
print('  ✓ Escalating penalties for consecutive holds')
print('  ✓ +1 reward for ANY action (encourages trading)')
print('  ✓ Bonus for active trading')
print()

if torch.cuda.is_available():
    print(f'⚡ GPU Training - Expected time: 25-45 minutes')
else:
    print(f'⏰ CPU Training - Expected time: 2-3 hours')
    
print('Monitor progress at: http://localhost:6006')
print('=' * 60)
print()

# Train
try:
    model.learn(
        total_timesteps=CONFIG['total_timesteps'],
        callback=callbacks,
        progress_bar=True,
        tb_log_name='ppo_aggressive_run'
    )
    
    print('\n' + '=' * 60)
    print('✅ Training complete!')
    print('=' * 60)
    
    # Save final model
    final_model_path = '../../models/ppo_aggressive_final'
    model.save(final_model_path)
    print(f'✓ Final model saved to: {final_model_path}.zip')
    
    # Save configuration
    import json
    config_path = '../../models/ppo_aggressive_config.json'
    with open(config_path, 'w') as f:
        json.dump(CONFIG, f, indent=2)
    print(f'✓ Config saved to: {config_path}')
    
except KeyboardInterrupt:
    print('\n' + '=' * 60)
    print('⚠️ Training interrupted by user')
    print('=' * 60)
    
    interrupted_model_path = '../../models/ppo_aggressive_interrupted'
    model.save(interrupted_model_path)
    print(f'✓ Model saved to: {interrupted_model_path}.zip')

except Exception as e:
    print(f'\n❌ Error during training: {e}')
    import traceback
    traceback.print_exc()
    
    error_model_path = '../../models/ppo_aggressive_error'
    model.save(error_model_path)
    print(f'✓ Model saved to: {error_model_path}.zip')

print('\n' + '=' * 60)
print('Next steps:')
print('  1. Evaluate model: python evaluate.py')
print('  2. View TensorBoard: tensorboard --logdir=../../logs/tensorboard_aggressive')
print('  3. Check best model in: models/best_aggressive/')
print('=' * 60)
