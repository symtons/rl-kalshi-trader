import requests
import datetime
import base64
import time
from typing import Dict, Any, Optional
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend

class KalshiClient:
    '''Working Kalshi API Client'''
    
    def __init__(self, api_key_id: str, private_key_path: str):
        self.api_key_id = api_key_id
        self.base_url = 'https://api.elections.kalshi.com'
        
        with open(private_key_path, 'rb') as f:
            self.private_key = serialization.load_pem_private_key(
                f.read(), password=None, backend=default_backend()
            )
    
    def _sign(self, message: str) -> str:
        signature = self.private_key.sign(
            message.encode('utf-8'),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.DIGEST_LENGTH
            ),
            hashes.SHA256()
        )
        return base64.b64encode(signature).decode('utf-8')
    
    def _request(self, method: str, path: str, body: Optional[Dict] = None, 
                 params: Optional[Dict] = None) -> requests.Response:
        timestamp_ms = str(int(datetime.datetime.now().timestamp() * 1000))
        path_without_query = path.split('?')[0]
        
        msg_string = timestamp_ms + method + path_without_query
        signature = self._sign(msg_string)
        
        headers = {
            'Content-Type': 'application/json',
            'KALSHI-ACCESS-KEY': self.api_key_id,
            'KALSHI-ACCESS-SIGNATURE': signature,
            'KALSHI-ACCESS-TIMESTAMP': timestamp_ms
        }
        
        url = self.base_url + path
        
        if method == 'GET':
            return requests.get(url, headers=headers, params=params, timeout=10)
        elif method == 'POST':
            return requests.post(url, headers=headers, json=body, timeout=10)
        else:
            raise ValueError(f'Unsupported method: {method}')
    
    def get_balance(self) -> Dict:
        try:
            response = self._request('GET', '/trade-api/v2/portfolio/balance')
            if response.status_code == 200:
                return response.json()
            return {'balance': 0, 'error': response.text}
        except Exception as e:
            return {'balance': 0, 'error': str(e)}
    
    def get_markets(self, series_ticker='KXBTC', limit=10, status='open') -> list:
        try:
            response = self._request('GET', '/trade-api/v2/markets', params={
                'limit': limit, 'status': status, 'series_ticker': series_ticker
            })
            if response.status_code == 200:
                return response.json().get('markets', [])
            return []
        except Exception as e:
            print(f'Error getting markets: {e}')
            return []
    
    def create_order(self, ticker: str, side: str, action: str, 
                     count: int, price: int) -> Dict:
        try:
            body = {
                'ticker': ticker, 
                'side': side, 
                'action': action,
                'count': count, 
                'type': 'limit',
                'client_order_id': f'rl_{int(time.time())}_{ticker}'
            }
            
            if side == 'yes':
                body['yes_price'] = price
            else:
                body['no_price'] = price
            
            response = self._request('POST', '/trade-api/v2/portfolio/orders', body=body)
            
            if response.status_code in [200, 201]:
                return response.json()
            else:
                return {'error': response.text, 'status_code': response.status_code}
        except Exception as e:
            return {'error': str(e)}
