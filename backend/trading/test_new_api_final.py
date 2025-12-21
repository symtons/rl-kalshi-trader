from kalshi_client_v2 import KalshiClient, Environment

print('Testing NEW Kalshi API Keys')
print('=' * 60)

NEW_API_KEY_ID = 'db025f14-ed64-4c19-940b-0ad3f336713f'
NEW_PRIVATE_KEY_PATH = '../kalshi_private_key_new.pem'

print(f'API Key: {NEW_API_KEY_ID}')
print()

# Test 1: DEMO API
print('Test 1: DEMO API (demo-api.kalshi.co)')
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
        'limit': 3, 'status': 'open', 'series_ticker': 'KXBTC'
    })
    print(f'✅ Markets: {len(markets.get("markets", []))} found')
    
    # Balance (authenticated)
    try:
        balance = client._request('GET', '/portfolio/balance')
        print(f'✅✅✅ DEMO BALANCE WORKS: ')
    except Exception as e:
        if '401' in str(e):
            print(f'❌ Balance: 401 auth error (demo API doesnt support this)')
        else:
            print(f'❌ Balance: {e}')
        
except Exception as e:
    print(f'❌ DEMO failed: {e}')

print()

# Test 2: PRODUCTION API  
print('Test 2: PRODUCTION API (api.elections.kalshi.com)')
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
        'limit': 3, 'status': 'open', 'series_ticker': 'KXBTC'
    })
    print(f'✅ Markets: {len(markets.get("markets", []))} found')
    for m in markets.get('markets', [])[:2]:
        print(f'   {m["ticker"]}: YES ask={m.get("yes_ask", 0)}c')
    
    # Balance
    balance_data = client._request('GET', '/portfolio/balance')
    balance = balance_data.get('balance', 0)
    print(f'✅ Balance: ')
    
    if balance > 0:
        print('\n🎉🎉🎉 YOU HAVE FUNDS! READY TO TRADE! 🎉🎉🎉')
        
        # Test order placement
        print('\nTest 3: Order Placement')
        print('-' * 60)
        market = markets['markets'][0]
        ticker = market['ticker']
        yes_ask = market.get('yes_ask', 50)
        
        print(f'Market: {ticker}')
        print(f'Order: BUY 1x YES @ {yes_ask}c (cost: )')
        
        confirm = input('\nPlace test order? (yes/no): ')
        if confirm.lower() == 'yes':
            try:
                result = client.create_order(ticker, 'yes', 'buy', 1, yes_ask)
                if 'error' in result:
                    print(f'❌ Order failed: {result["error"]}')
                else:
                    print(f'✅✅✅ ORDER PLACED SUCCESSFULLY! ✅✅✅')
                    print(f'Order ID: {result.get("order_id")}')
            except Exception as e:
                print(f'❌ Order error: {e}')
    else:
        print('\n⚠️ Balance: .00')
        print('Contact Kalshi support to add demo funds!')
        
except Exception as e:
    if '401' in str(e):
        print(f'❌ PRODUCTION: 401 auth error')
        print('   Your API key may not be activated yet')
    else:
        print(f'❌ PRODUCTION failed: {e}')

print()
print('=' * 60)
