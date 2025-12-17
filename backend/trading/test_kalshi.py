import os
import time
from kalshi_python import KalshiClient

print('Testing Kalshi Demo API Connection')
print('=' * 60)

# Kalshi Demo API credentials
KALSHI_API_KEY = 'b6dd7ed6-9f4d-4bca-99af-13b474ae8969'
KALSHI_API_SECRET = 'MIIEowIBAAKCAQEAnJxsMrbJQ6pzH8P+ZkZC3uKvXxNcFDJnSp+ZV/sCwE/35mGcqtx/Iv1FAfqoB6V9T99Ye7Hv6Y0THLaY0UOQwaRrdA9X9JCUhmM6g/jbLcnwqOsUqxcDuGy2ZXqvcHak0CIiB4Y9ZvO0A4qTwGo0eiSldbl35pkNB6dmLxmOYjnm3G0eG39T0LkGZGkOKi/Jpw+kiu3zJ4sQJJPVhvyCgubTvvmKKrqc9x/q63mlznd+vM9fQvsY5DuVtw4VovEQ3yfVn8rfz7rjKyUlEIA7hSPWWrSnhnI1dvz7E4eAeT03mUwCipPWP8zNfwP1TW2VOwWYUV825DK97n4+9z3iXwIDAQABAoIBAEzoVgv7jk+/6yQc1Bf2hg09ZeC7OZsje2z+fkfh2OKHAtasdcrEWFze4l4L8Ss8HhM0u5eW9JmNMWcG1nnhg7tMWoZWqJtNytpJ7Wj0svHD+v6A3xf7x9Rv8oxYGMKSSPJ66JooVovxvqOEkHVL0nRu/aAX0eU4oNjy4G/dzXm3b7xQX4gvzUNvvrt6BjvUeUetg74de1jACASvG8h2S2XOhXk5HwqdJ7qalojQ9wDbhfvJmJ/qKBfPeFFidPZ26JT4bxODxA5v8dmHD+n1KswEMytAWJQdoGP41zGmbB9k74o6ombAUVD+Hmw4rps030CQMna/s6+QpzKr64os4XkCgYEAz0Xsubq10Sl6h2+D5CmmdIBjJ7/2qTN+L0LqDl8C3RksyUnxeRhANZyvkv+dhVGMTHoSaASXujRE7sKnkwmvLj2L+sJzXfyC2aHhUBdKtjx7sto15O048Qmm3VIYCJXXFgD8qrvz+2OUJP77BrVAx+abTN0RgLV85k0U/PRRuJkCgYEAwW2PN2EvqjuAe/K2sFtYl1uzCNlCGqqn+ZQB6rMj+f2+GnKPmGwSIH9dU89Gmg5nfSYV99cXG2ziNlyLhvA7TXrDcIfhkyfz9x43LU2EV7UrqbmCExLH7+cq/Hl6p2vR+CjEpjbkjGhasRSI1PtxI3beuxg0063e1ERnT7M9dbcCgYEAiyyTgD5bOP+V83ywXbKNvyo56gXedMxLjSZsDIxFWvo9dUb+KeZbruPvjE+wkEUqZGuPEmMLEg9ovbzcUkGta+oNpKmOV2xm3ATzShjppKXGFVip2XZjxo1JitBFrPYXvwGYpnefoovBfHntShrITbGNU7YYu4ihPe5CCntup/kCgYAV//4QEG+5bvcYIe0BdgJHhNiCIyPPoKVmT51AMove/StIGsuWTIRrSdE1nResogLHSzOocsBgECxSfogoGt7D2zirbekMMbkf3EHuVyi8SRDkRwMyZCp1cNeEy9RVgn/pN8nWFdw81AmspmdBwi+GFxkSMpifkuELR5RwjjRpVQKBgEprCRZBVZHcij6E5yAPzD/fbFfAb8TvlPCiHrms2K2lE+0oWbLrhGkNrZR4aHdkmT5oODTKzBYX8HF3wjT4IBGR+YvXP5PeAtSYKhpRsr1ddqoo766/8BKqjLEfBOUYy5qx08y75Z3goNLnLDHckOLz98gjjDd844dM5s0gzNMT'

# Initialize Kalshi client
print('Connecting to Kalshi Demo...')
try:
    kalshi = KalshiClient(
        key_id=KALSHI_API_KEY,
        private_key=KALSHI_API_SECRET,
        host='https://demo-api.kalshi.co'
    )
    print('Connected to Kalshi Demo')
except Exception as e:
    print(f'Connection failed: {e}')
    print('\nMake sure you:')
    print('  1. Created a Kalshi demo account')
    print('  2. Generated API keys')
    print('  3. Replaced credentials in script')
    exit(1)

print()

# Test 1: Get account balance
print('Test 1: Checking account balance...')
try:
    balance = kalshi.get_balance()
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
    
    market_list = markets.get('markets', [])
    print(f'Found {len(market_list)} BTC markets')
    
    if market_list:
        print('\nAvailable BTC Markets:')
        for market in market_list[:3]:
            ticker = market.get('ticker', 'N/A')
            title = market.get('title', 'N/A')
            yes_bid = market.get('yes_bid', 0) / 100
            yes_ask = market.get('yes_ask', 0) / 100
            print(f'  {ticker}: {title}')
            print(f'    YES: Bid={yes_bid:.2f}, Ask={yes_ask:.2f}')
    else:
        print('No BTC markets found')
        
except Exception as e:
    print(f'Error: {e}')

print()

# Test 3: Place test order
print('Test 3: Placing test order...')
print('WARNING: This will place a REAL order on your DEMO account')
response = input('Press Enter to continue or Ctrl+C to cancel...')

try:
    markets = kalshi.get_markets(limit=1, status='open', series_ticker='KXBTC')
    market_list = markets.get('markets', [])
    
    if not market_list:
        print('No markets available')
    else:
        market = market_list[0]
        ticker = market['ticker']
        yes_ask = market.get('yes_ask', 0)
        
        print(f'Placing order for: {ticker}')
        print(f'  Side: YES')
        print(f'  Quantity: 1 contract')
        print(f'  Price: {yes_ask / 100:.2f}')
        
        order = kalshi.create_order(
            ticker=ticker,
            client_order_id=f'test_{ticker}_{int(time.time())}',
            side='yes',
            action='buy',
            count=1,
            type='market'
        )
        
        print(f'Order placed successfully!')
        print(f'  Order ID: {order.get("order_id")}')
        print(f'  Status: {order.get("status")}')
        
except Exception as e:
    print(f'Error: {e}')

print()
print('=' * 60)
print('Kalshi API test complete!')
