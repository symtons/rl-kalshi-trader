import sys
sys.path.append('..')

from trading.kalshi_client_v2 import KalshiClient, Environment

print('Testing NEW Kalshi API Keys')
print('=' * 60)

# YOUR NEW CREDENTIALS HERE
NEW_API_KEY_ID = '8400a198-5eaa-48b8-8687-d5ec71228257'  # Replace this
NEW_PRIVATE_KEY_PATH = '../kalshi_private_key.pem'  # Or new path

print('Creating client with DEMO API...')
try:
    client = KalshiClient(
        base_url='https://demo-api.kalshi.co/trade-api/v2',
        key_id=NEW_API_KEY_ID,
        private_key_path=NEW_PRIVATE_KEY_PATH,
        environment=Environment.DEMO
    )
    print('✅ Client created')
except Exception as e:
    print(f'❌ Error: {e}')
    exit(1)

print()

# Test 1: Get markets (public endpoint)
print('Test 1: Fetching BTC markets...')
try:
    response = client._request('GET', '/markets', params={
        'limit': 3,
        'status': 'open',
        'series_ticker': 'KXBTC'
    })
    
    markets = response.get('markets', [])
    print(f'✅ Found {len(markets)} markets')
    
    for market in markets:
        print(f"  {market['ticker']}: YES ask={market.get('yes_ask', 0)}c")
    
except Exception as e:
    print(f'❌ Error: {e}')

print()

# Test 2: Get balance (authenticated endpoint)
print('Test 2: Getting balance (authenticated)...')
try:
    response = client._request('GET', '/portfolio/balance')
    balance = response.get('balance', 0)
    print(f'✅ Balance: ')
    
    if balance > 0:
        print('\n🎉 YOU HAVE FUNDS! Ready to trade!')
    else:
        print('\n⚠️ Balance is  - need to add demo funds')
    
except Exception as e:
    error_msg = str(e)
    if '401' in error_msg:
        print(f'❌ 401 Authentication Error')
        print('   Possible issues:')
        print('   1. API key not valid for demo')
        print('   2. Private key doesnt match API key')
        print('   3. Demo API doesnt support this key')
    else:
        print(f'❌ Error: {e}')

print()
print('=' * 60)
