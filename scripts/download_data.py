import ccxt
import pandas as pd
from datetime import datetime, timedelta
import os
import sys
import time

def download_btc_data(months=6, timeframe='1h'):
    '''
    Download historical BTC/USD data from Coinbase
    
    Args:
        months: Number of months of historical data
        timeframe: Candle timeframe ('1m', '5m', '15m', '1h', etc.)
    '''
    print(f'📊 Downloading {months} months of BTC data from Coinbase...')
    print('=' * 60)
    
    # Initialize Coinbase exchange
    try:
        exchange = ccxt.coinbase({
            'enableRateLimit': True,
        })
        print('✓ Connected to Coinbase')
    except Exception as e:
        print(f'❌ Error connecting to Coinbase: {e}')
        sys.exit(1)
    
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30*months)
    
    print(f'Date range: {start_date.date()} to {end_date.date()}')
    print(f'Timeframe: {timeframe}')
    
    # Convert to milliseconds timestamp
    since = int(start_date.timestamp() * 1000)
    
    # Fetch data
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
            since = ohlcv[-1][0] + 1  # Next timestamp
            batch_count += 1
            
            # Progress update
            current_date = datetime.fromtimestamp(ohlcv[-1][0] / 1000)
            print(f'  Batch {batch_count}: Fetched up to {current_date.date()} ({len(all_ohlcv):,} candles)', end='\r')
            
            # Stop if we've reached the end date
            if since > int(end_date.timestamp() * 1000):
                break
            
            # Small delay to respect rate limits
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
    
    # Convert to DataFrame
    df = pd.DataFrame(
        all_ohlcv,
        columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
    )
    
    # Convert timestamp to datetime
    df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
    
    # Reorder columns
    df = df[['datetime', 'timestamp', 'open', 'high', 'low', 'close', 'volume']]
    
    # Create data directory if it doesn't exist
    os.makedirs('data/raw', exist_ok=True)
    
    # Save to CSV
    output_file = f'data/raw/btc_{timeframe}_{months}months.csv'
    df.to_csv(output_file, index=False)
    
    print(f'\n✓ Data saved to: {output_file}')
    print(f'  Rows: {len(df):,}')
    print(f'  Date range: {df["datetime"].min()} to {df["datetime"].max()}')
    print(f'  File size: {os.path.getsize(output_file) / (1024*1024):.2f} MB')
    
    # Show statistics
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
    print('🚀 BTC Data Downloader (Coinbase)')
    print('=' * 60)
    
    # Download 6 months of 1-hour data (Coinbase works better with hourly)
    df = download_btc_data(months=6, timeframe='1h')
    
    print('\n' + '=' * 60)
    print('✅ Download complete!')
    print('=' * 60)
