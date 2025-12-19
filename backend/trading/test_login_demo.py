import requests
import json
import time

print('Testing Kalshi Demo Login Authentication')
print('=' * 60)

# Your Kalshi demo credentials
DEMO_EMAIL = 'schinomb@mail.yu.edu'
DEMO_PASSWORD = '97072066Sc@2026'

# Demo API base
BASE_URL = 'https://demo-api.kalshi.co/trade-api/v2'

# Step 1: Login
print('Step 1: Logging in...')
login_response = requests.post(
    f'{BASE_URL}/login',
    json={'email': DEMO_EMAIL, 'password': DEMO_PASSWORD}
)

print(f'Login status: {login_response.status_code}')

if login_response.status_code == 200:
    login_data = login_response.json()
    token = login_data.get('token')
    member_id = login_data.get('member_id')
    
    print(f'✅ Login successful!')
    print(f'Token: {token[:50]}...')
    print(f'Member ID: {member_id}')
    print()
    
    # Step 2: Get balance with token
    print('Step 2: Getting balance with token...')
    headers = {'Authorization': f'Bearer {token}'}
    
    balance_response = requests.get(f'{BASE_URL}/portfolio/balance', headers=headers)
    print(f'Balance status: {balance_response.status_code}')
    
    if balance_response.status_code == 200:
        balance_data = balance_response.json()
        print(f'✅ Balance: {balance_data}')
    else:
        print(f'❌ Balance failed: {balance_response.text}')
    
    print()
    
    # Step 3: Get markets
    print('Step 3: Getting BTC markets...')
    markets_response = requests.get(
        f'{BASE_URL}/markets',
        headers=headers,
        params={'limit': 1, 'status': 'open', 'series_ticker': 'KXBTC'}
    )
    
    if markets_response.status_code == 200:
        markets = markets_response.json().get('markets', [])
        print(f'✅ Found {len(markets)} markets')
        
        if markets:
            market = markets[0]
            ticker = market['ticker']
            yes_ask = market.get('yes_ask', 50)
            
            print(f'\nMarket: {ticker}')
            print(f'YES ask: {yes_ask} cents')
            print()
            
            # Step 4: Try to place order
            print('Step 4: Attempting to place order...')
            print('⚠️  This will place a REAL order on demo account')
            
            response = input('Type YES to continue: ')
            if response.upper() == 'YES':
                order_data = {
                    'ticker': ticker,
                    'side': 'yes',
                    'action': 'buy',
                    'count': 1,
                    'type': 'limit',
                    'yes_price': yes_ask,
                    'client_order_id': f'test_{int(time.time())}'
                }
                
                order_response = requests.post(
                    f'{BASE_URL}/portfolio/orders',
                    headers=headers,
                    json=order_data
                )
                
                print(f'\nOrder status: {order_response.status_code}')
                
                if order_response.status_code in [200, 201]:
                    print(f'✅ ORDER PLACED!')
                    print(json.dumps(order_response.json(), indent=2))
                else:
                    print(f'❌ Order failed: {order_response.text}')
            else:
                print('Order cancelled')
    else:
        print(f'❌ Markets failed: {markets_response.text}')
        
else:
    print(f'❌ Login failed!')
    print(f'Response: {login_response.text}')

print()
print('=' * 60)
