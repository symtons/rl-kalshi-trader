import sys
sys.path.append('..')

from trading.kalshi_client_v2 import KalshiClient, Environment
import time

print('Testing Custom Kalshi Client')
print('=' * 60)

# Initialize client
print('Creating client...')
try:
    client = KalshiClient(environment=Environment.DEMO)
    print('Client created successfully')
except Exception as e:
    print(f'Error: {e}')
    exit(1)

print()

# Test 1: Get markets
print('Test 1: Fetching BTC markets...')
try:
    response = client._request('GET', '/markets', params={
        'limit': 5,
        'status': 'open',
        'series_ticker': 'KXBTC'
    })
    
    markets = response.get('markets', [])
    print(f'Found {len(markets)} markets')
    
    if markets:
        print('\nAvailable markets:')
        for market in markets[:3]:
            print(f"  {market['ticker']}: {market.get('title', 'N/A')}")
            print(f"    YES bid/ask: {market.get('yes_bid', 0)/100:.2f} / {market.get('yes_ask', 0)/100:.2f}")
    
except Exception as e:
    print(f'Error: {e}')

print()

# Test 2: Get balance
print('Test 2: Getting balance...')
try:
    response = client._request('GET', '/portfolio/balance')
    balance = response.get('balance', 0)
    print(f'Balance: {balance / 100:.2f} dollars')
except Exception as e:
    print(f'Error: {e}')

print()

# Test 3: Place order (commented out for safety)
print('Test 3: Place order (skipped for now)')
print('Uncomment the code below to test order placement')

# print('Placing test order...')
# try:
#     order = client.create_order(
#         ticker='KXBTC-25DEC1717-B95500',  # Use an actual ticker from Test 1
#         side='yes',
#         action='buy',
#         count=1,
#         price=0.50,  # 50 cents
#         client_order_id=f'test_{int(time.time())}'
#     )
#     print(f'Order placed: {order}')
# except Exception as e:
#     print(f'Error: {e}')

print()
print('=' * 60)
print('Test complete!')
