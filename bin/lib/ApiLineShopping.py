import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class ApiiLineShopping:
    def __init__(self, token, timeout=10, pool_connections=20, pool_maxsize=20):
        self.token = token
        self.timeout = timeout

        self.session = requests.Session()
        self.session.headers.update({
            'accept': 'application/json',
            'accept-language': 'en-US,en;q=0.9,th-TH;q=0.8,th;q=0.7',
            'authorization': f'Bearer {self.token}',
            'content-type': 'application/json',
            'origin': 'https://shop.line.me',
            'referer': 'https://shop.line.me/',
            'user-agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/145.0.0.0 Safari/537.36'
            ),
        })

        self.public_session = requests.Session()
        self.public_session.headers.update({
            'accept': 'application/json',
            'accept-language': 'en-US,en;q=0.9,th-TH;q=0.8,th;q=0.7',
            'origin': 'https://shop.line.me',
            'referer': 'https://shop.line.me/',
            'user-agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/145.0.0.0 Safari/537.36'
            ),
        })

        retry = Retry(
            total=0,
            connect=0,
            read=0,
            redirect=0,
            backoff_factor=0,
            allowed_methods=frozenset(['GET', 'POST']),
            raise_on_status=False,
        )

        adapter = HTTPAdapter(
            pool_connections=pool_connections,
            pool_maxsize=pool_maxsize,
            max_retries=retry,
        )

        self.session.mount('https://', adapter)
        self.session.mount('http://', adapter)
        self.public_session.mount('https://', adapter)
        self.public_session.mount('http://', adapter)

    def _json(self, response):
        response.raise_for_status()
        return response.json()

    def profile(self):
        response = self.session.get(
            'https://api.line.me/v2/profile',
            timeout=self.timeout,
        )
        return self._json(response)

    def info_product(self, shop_name, id_product):
        response = self.public_session.get(
            f'https://sc-oms-api.line-apps.com/api/v1/shopend/{shop_name}/product/{id_product}',
            timeout=self.timeout,
        )
        return self._json(response)

    def checkout(self, json_data):
        response = self.session.post(
            'https://customer-api.line-apps.com/cart/api/v2/cart/checkout',
            json=json_data,
            timeout=self.timeout,
        )
        return self._json(response)

    def place_order(self, name_shop, json_data, x_la_session_id='27410faa389540d3'):
        headers = {
            'authorization': self.token,
            'x-la-session-id': x_la_session_id,
        }
        response = self.session.post(
            f'https://sc-oms-api.line-apps.com/api/v6/shopend/{name_shop}/order/place-order-qr',
            headers=headers,
            json=json_data,
            timeout=self.timeout,
        )
        print(response.text)
        return self._json(response)

    def close(self):
        self.session.close()
        self.public_session.close()