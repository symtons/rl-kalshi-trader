import ccxt
import pandas as pd
from datetime import datetime, timedelta
import os
import sys
import time

def download_btc_data(months=6, timeframe='15m'):
    '''Download historical BTC/USD data from Coinbase'''
    print(f'📊 Downloading {months} months of BTC data from Coinbase...')
    print('=' * 60)
    
    try:
        exchange = ccxt.coinbase({'enableRateLimit': True})
        print('✓ Connected to Coinbase')
    except Exception as e:
        print(f'❌ Error connecting to Coinbase: {e}')
        sys.exit(1)
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30*months)
    
    print(f'Date range: {start_date.date()} to {end_date.date()}')
    print(f'Timeframe: {timeframe}')
    
    since = int(start_date.timestamp() * 1000)
    all_ohlcv = []
    symbol = 'BTC/USD'
    
    print(f'\nFetching {timeframe} candles for {symbol}...')
    
    batch_count = 0
    while True:
        try:
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since=since, limit=300)
            
            if not ohlcv or len(ohlcv) == 0:
                print('\nNo more data available')
                break
            
            all_ohlcv.extend(ohlcv)
            since = ohlcv[-1][0] + 1
            batch_count += 1
            
            current_date = datetime.fromtimestamp(ohlcv[-1][0] / 1000)
            print(f'  Batch {batch_count}: Fetched up to {current_date.date()} ({len(all_ohlcv):,} candles)', end='\r')
            
            if since > int(end_date.timestamp() * 1000):
                break
            
            time.sleep(0.1)
                
        except Exception as e:
            print(f'\n⚠️ Error: {e}')
            if len(all_ohlcv) > 0:
                print(f'Continuing with {len(all_ohlcv):,} candles fetched so far...')
                break
            else:
                print('❌ No data fetched')
                sys.exit(1)
    
    print(f'\n\n✓ Total candles fetched: {len(all_ohlcv):,}')
    
    if len(all_ohlcv) == 0:
        print('❌ No data fetched.')
        sys.exit(1)
    
    df = pd.DataFrame(
        all_ohlcv,
        columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
    )
    
    df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
    df = df[['datetime', 'timestamp', 'open', 'high', 'low', 'close', 'volume']]
    
    os.makedirs('../data/raw', exist_ok=True)
    
    output_file = f'../data/raw/btc_{timeframe}_{months}months.csv'
    df.to_csv(output_file, index=False)
    
    print(f'\n✓ Data saved to: {output_file}')
    print(f'  Rows: {len(df):,}')
    print(f'  Date range: {df["datetime"].min()} to {df["datetime"].max()}')
    print(f'  File size: {os.path.getsize(output_file) / (1024*1024):.2f} MB')
    
    print(f'\n📈 BTC Price Statistics:')
    print(f'  Min: {df["low"].min():,.2f}')
    print(f'  Max: {df["high"].max():,.2f}')
    print(f'  Mean: {df["close"].mean():,.2f}')
    print(f'  Current: {df["close"].iloc[-1]:,.2f}')
    
    print('\n📋 First 5 rows:')
    print(df.head().to_string())
    
    print('\n📋 Last 5 rows:')
    print(df.tail().to_string())
    
    return df

if __name__ == '__main__':
    print('🚀 BTC Data Downloader (Coinbase) - 15 Minute Candles')
    print('=' * 60)
    
    df = download_btc_data(months=6, timeframe='15m')
    
    print('\n' + '=' * 60)
    print('✅ Download complete!')
    print('=' * 60)
