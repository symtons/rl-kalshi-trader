import pandas as pd
import matplotlib.pyplot as plt

# Load data
df = pd.read_csv('data/raw/btc_1h_6months.csv')
df['datetime'] = pd.to_datetime(df['datetime'])

print('📊 Data Verification')
print('=' * 60)
print(f'Total rows: {len(df):,}')
print(f'Date range: {df["datetime"].min()} to {df["datetime"].max()}')
print(f'Missing values: {df.isnull().sum().sum()}')
print(f'\nColumns: {list(df.columns)}')
print(f'\nData types:\n{df.dtypes}')

# Check for any gaps in data
df['time_diff'] = df['datetime'].diff()
gaps = df[df['time_diff'] > pd.Timedelta(hours=1)]
if len(gaps) > 0:
    print(f'\n⚠️ Found {len(gaps)} time gaps:')
    print(gaps[['datetime', 'time_diff']].head())
else:
    print('\n✓ No time gaps found')

# Basic statistics
print('\n📈 Price Statistics:')
print(df[['open', 'high', 'low', 'close', 'volume']].describe())

print('\n✅ Data looks good!')
