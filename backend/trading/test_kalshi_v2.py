import sys
sys.path.append('..')

from trading.kalshi_client_v2 import KalshiClient, Environment

print('Testing Custom Kalshi Client')
print('=' * 60)

# Initialize client with explicit parameters
print('Creating client...')
try:
    client = KalshiClient(
        base_url='https://demo-api.kalshi.co',
        key_id='b6dd7ed6-9f4d-4bca-99af-13b474ae8969',
        private_key_path='C:\\Users\\simbe\\OneDrive\\Desktop\\RL\\rl-kalshi-trader\\backend\\kalshi_private_key.pem',
        environment=Environment.DEMO
    )
    print('Client created successfully')
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
    exit(1)

print()

# Test 1: Get markets
print('Test 1: Fetching BTC markets...')
try:
    response = client._request('GET', '/trade-api/v2/markets', params={
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
            yes_bid = market.get('yes_bid', 0)
            yes_ask = market.get('yes_ask', 0)
            if yes_bid or yes_ask:
                print(f"    YES bid/ask: {yes_bid/100:.2f} / {yes_ask/100:.2f}")
    
except Exception as e:
    print(f'Error: {e}')

print()

# Test 2: Get balance
print('Test 2: Getting balance...')
try:
    response = client._request('GET', '/trade-api/v2/portfolio/balance')
    balance = response.get('balance', 0)
    print(f'Balance: {balance / 100:.2f} dollars')
except Exception as e:
    print(f'Error: {e}')

print()
print('=' * 60)
print('Test complete!')
