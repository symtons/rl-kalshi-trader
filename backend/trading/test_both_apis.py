from kalshi_client_v2 import KalshiClient, Environment

print('Testing NEW Kalshi API Keys')
print('=' * 60)

# YOUR NEW CREDENTIALS (replace these!)
NEW_API_KEY_ID = 'db025f14-ed64-4c19-940b-0ad3f336713f'
NEW_PRIVATE_KEY_PATH = '../kalshi_private_key.pem'

print(f'API Key: {NEW_API_KEY_ID[:20]}...')
print()

# Test DEMO API
print('Test 1: DEMO API')
print('-' * 60)
try:
    client = KalshiClient(
        base_url='https://demo-api.kalshi.co/trade-api/v2',
        key_id=NEW_API_KEY_ID,
        private_key_path=NEW_PRIVATE_KEY_PATH,
        environment=Environment.DEMO
    )
    
    # Markets (public)
    markets = client._request('GET', '/markets', params={
        'limit': 1, 'status': 'open', 'series_ticker': 'KXBTC'
    })
    print(f'✅ Markets: {len(markets.get("markets", []))} found')
    
    # Balance (authenticated)
    try:
        balance = client._request('GET', '/portfolio/balance')
        print(f'✅ Balance: ')
    except Exception as e:
        print(f'❌ Balance failed: {e}')
        
except Exception as e:
    print(f'❌ DEMO failed: {e}')

print()

# Test PRODUCTION API  
print('Test 2: PRODUCTION API')
print('-' * 60)
try:
    client = KalshiClient(
        base_url='https://api.elections.kalshi.com/trade-api/v2',
        key_id=NEW_API_KEY_ID,
        private_key_path=NEW_PRIVATE_KEY_PATH,
        environment=Environment.PROD
    )
    
    # Markets
    markets = client._request('GET', '/markets', params={
        'limit': 1, 'status': 'open', 'series_ticker': 'KXBTC'
    })
    print(f'✅ Markets: {len(markets.get("markets", []))} found')
    
    # Balance
    balance_data = client._request('GET', '/portfolio/balance')
    balance = balance_data.get('balance', 0)
    print(f'✅ Balance: ')
    
    if balance > 0:
        print('\n🎉 YOU HAVE FUNDS! Ready to trade!')
    else:
        print('\n⚠️  balance - need demo funds from Kalshi')
        
except Exception as e:
    print(f'❌ PRODUCTION failed: {e}')

print()
print('=' * 60)
