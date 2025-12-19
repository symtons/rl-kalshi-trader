from kalshi_python import Configuration, KalshiClient
import os

print('Testing Official Kalshi SDK')
print('=' * 60)

# Create configuration
print('Creating configuration...')
config = Configuration(
    host='https://api.elections.kalshi.com/trade-api/v2'
)

# Set API credentials
# The SDK might use different parameter names
print('Setting API key...')

# Try different approaches the SDK might accept
try:
    # Option 1: Set in config
    config.api_key = {
        'KALSHI-ACCESS-KEY': '8400a198-5eaa-48b8-8687-d5ec71228257'
    }
    
    # Create client
    client = KalshiClient(configuration=config)
    print('✅ Client created')
    
except Exception as e:
    print(f'❌ Config approach failed: {e}')
    print()
    print('Trying direct initialization...')
    
    try:
        # Option 2: Pass credentials directly
        client = KalshiClient(
            api_key='8400a198-5eaa-48b8-8687-d5ec71228257',
            private_key_path='../kalshi_private_key.pem',
            host='https://api.elections.kalshi.com/trade-api/v2'
        )
        print('✅ Client created')
    except Exception as e2:
        print(f'❌ Direct approach also failed: {e2}')
        print()
        print('Let me check SDK documentation...')
        import kalshi_python
        print(f'SDK version: {kalshi_python.__version__}')
        print(f'Available in kalshi_python: {dir(kalshi_python)}')
        exit(1)

print()

# Test balance
print('Testing balance...')
try:
    balance = client.get_balance()
    print(f'✅ Balance: {balance}')
except Exception as e:
    print(f'❌ Failed: {e}')

print()

# Test markets
print('Testing markets...')
try:
    markets = client.get_markets(limit=1, status='open', series_ticker='KXBTC')
    print(f'✅ Markets: {markets}')
except Exception as e:
    print(f'❌ Failed: {e}')

print()
print('=' * 60)