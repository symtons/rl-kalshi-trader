from kalshi_client_v2 import KalshiClient, Environment
import time

print('Testing Order Placement')
print('=' * 60)

# Initialize client
client = KalshiClient(
    base_url='https://demo-api.kalshi.co/trade-api/v2',
    key_id='b6dd7ed6-9f4d-4bca-99af-13b474ae8969',
    private_key_path='../kalshi_private_key.pem',
    environment=Environment.DEMO
)
print('Client created')
print()

# Get a market
print('Fetching markets...')
response = client._request('GET', '/markets', params={
    'limit': 1,
    'status': 'open',
    'series_ticker': 'KXBTC'
})

markets = response.get('markets', [])
if not markets:
    print('No markets available!')
    exit(1)

market = markets[0]
ticker = market['ticker']
print(f'Selected market: {ticker}')
print(f'Title: {market.get("title", "N/A")}')

yes_ask = market.get('yes_ask', 50)
print(f'YES ask price: {yes_ask / 100:.2f}')
print()

# PLACE ORDER
print('⚠️  WARNING: This will place a REAL order on your DEMO account!')
print(f'Order details:')
print(f'  Ticker: {ticker}')
print(f'  Side: YES')
print(f'  Action: BUY')
print(f'  Quantity: 1 contract')
print(f'  Price: {yes_ask / 100:.2f}')
print()

response = input('Type YES to confirm order placement: ')
if response.upper() != 'YES':
    print('Order cancelled')
    exit(0)

print()
print('Placing order...')
try:
    order = client.create_order(
        ticker=ticker,
        side='yes',
        action='buy',
        count=1,
        price=yes_ask / 100  # Convert cents to decimal
    )
    
    print('✅ ORDER PLACED SUCCESSFULLY!')
    print(f'Order response: {order}')
    
except Exception as e:
    print(f'❌ Order failed: {e}')
    import traceback
    traceback.print_exc()

print()
print('=' * 60)
