import os
import time
from kalshi_python import ApiInstance

print('Testing Kalshi Demo API Connection')
print('=' * 60)

# Kalshi Demo credentials
KALSHI_EMAIL = 'schinomb@mail.yu.edu'  # Your Kalshi login email
KALSHI_PASSWORD = '97072066Sc@2026'        # Your Kalshi login password

print('Connecting to Kalshi Demo...')
try:
    # Use ApiInstance with email/password for demo
    kalshi = ApiInstance(
        email=KALSHI_EMAIL,
        password=KALSHI_PASSWORD,
        demo=True  # Use demo environment
    )
    print('Connected to Kalshi Demo')
except Exception as e:
    print(f'Connection failed: {e}')
    exit(1)

print()

# Test 1: Get account balance
print('Test 1: Checking account balance...')
try:
    balance = kalshi.get_balance()
    print(f'Balance: {balance}')
    print(f'Account Balance: {balance / 100:.2f} dollars')
except Exception as e:
    print(f'Error: {e}')

print()

# Test 2: Get available markets
print('Test 2: Fetching BTC markets...')
try:
    markets = kalshi.get_markets(
        limit=5,
        status='open',
        series_ticker='KXBTC'
    )
    
    print(f'Found {len(markets)} BTC markets')
    
    if markets:
        print('\nAvailable BTC Markets:')
        for market in markets[:3]:
            ticker = market.ticker
            title = market.title
            yes_bid = getattr(market, 'yes_bid', 0) / 100
            yes_ask = getattr(market, 'yes_ask', 0) / 100
            print(f'  {ticker}: {title}')
            print(f'    YES: Bid={yes_bid:.2f}, Ask={yes_ask:.2f}')
    else:
        print('No BTC markets found')
        
except Exception as e:
    print(f'Error: {e}')

print()

# Test 3: Place a small test order
print('Test 3: Placing test order...')
print('WARNING: This will place a REAL order on your DEMO account')
response = input('Press Enter to continue or Ctrl+C to cancel...')

try:
    markets = kalshi.get_markets(limit=1, status='open', series_ticker='KXBTC')
    
    if not markets:
        print('No markets available')
    else:
        market = markets[0]
        ticker = market.ticker
        yes_ask = getattr(market, 'yes_ask', 0)
        
        print(f'Placing order for: {ticker}')
        print(f'  Side: YES')
        print(f'  Quantity: 1 contract')
        print(f'  Price: {yes_ask / 100:.2f}')
        
        order = kalshi.create_order(
            ticker=ticker,
            client_order_id=f'test_{int(time.time())}',
            side='yes',
            action='buy',
            count=1,
            type='market'
        )
        
        print(f'Order placed successfully!')
        print(f'  Order: {order}')
        
except Exception as e:
    print(f'Error: {e}')

print()
print('=' * 60)
print('Kalshi API test complete!')
