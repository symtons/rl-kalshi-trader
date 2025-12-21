import sys
sys.path.append('..')

from trading.kalshi_client_v2 import KalshiClient, Environment

print('Testing NEW API Keys on PRODUCTION')
print('=' * 60)

# Get your credentials from the test file
import test_new_keys
NEW_API_KEY_ID = test_new_keys.NEW_API_KEY_ID
NEW_PRIVATE_KEY_PATH = test_new_keys.NEW_PRIVATE_KEY_PATH

print(f'API Key: {NEW_API_KEY_ID}')
print()

# Test PRODUCTION API (this is where authentication works)
print('Creating client with PRODUCTION API...')
try:
    client = KalshiClient(
        base_url='https://api.elections.kalshi.com/trade-api/v2',
        key_id=NEW_API_KEY_ID,
        private_key_path=NEW_PRIVATE_KEY_PATH,
        environment=Environment.PROD
    )
    print('✅ Client created')
except Exception as e:
    print(f'❌ Error: {e}')
    exit(1)

print()

# Test markets
print('Test 1: Fetching BTC markets...')
try:
    response = client._request('GET', '/markets', params={
        'limit': 3,
        'status': 'open',
        'series_ticker': 'KXBTC'
    })
    
    markets = response.get('markets', [])
    print(f'✅ Found {len(markets)} markets')
    
except Exception as e:
    print(f'❌ Error: {e}')

print()

# Test balance (the key test!)
print('Test 2: Getting balance (authenticated)...')
try:
    response = client._request('GET', '/portfolio/balance')
    balance = response.get('balance', 0)
    print(f'✅✅✅ AUTHENTICATION WORKS! ✅✅✅')
    print(f'Balance: ')
    
    if balance > 0:
        print('\n🎉🎉🎉 YOU HAVE FUNDS! READY TO TRADE! 🎉🎉🎉')
    else:
        print('\n⚠️ Balance is ')
        print('This is a production account with demo/test funds mode')
        print('Contact Kalshi support to add demo funds')
    
except Exception as e:
    error_msg = str(e)
    if '401' in error_msg:
        print(f'❌ Still 401 on production')
        print('Your new API key may not be activated yet')
    else:
        print(f'❌ Error: {e}')

print()

# Test order placement (if balance > 0)
if 'balance' in locals() and balance > 0:
    print('Test 3: Test order placement...')
    try:
        markets = client._request('GET', '/markets', params={
            'limit': 1, 'status': 'open', 'series_ticker': 'KXBTC'
        })['markets']
        
        if markets:
            market = markets[0]
            ticker = market['ticker']
            yes_ask = market.get('yes_ask', 50)
            
            print(f'Market: {ticker}')
            print(f'Order: BUY 1x YES @ {yes_ask}c (cost: )')
            print()
            
            confirm = input('Place test order? (yes/no): ')
            if confirm.lower() == 'yes':
                result = client.create_order(ticker, 'yes', 'buy', 1, yes_ask)
                
                if 'error' in result:
                    print(f'❌ Order failed: {result["error"]}')
                else:
                    print(f'✅✅✅ ORDER PLACED! ✅✅✅')
                    print(f'Order ID: {result.get("order_id")}')
    except Exception as e:
        print(f'Error: {e}')

print()
print('=' * 60)
