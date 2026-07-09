import requests



class ApiiLineShopping():
    def __init__(self,token):
        self.token = token
        self.headers = {
            'accept': 'application/json',
            'accept-language': 'en-US,en;q=0.9,th-TH;q=0.8,th;q=0.7',
            'authorization': f'Bearer {self.token}',
            'content-type': 'application/json',
            'origin': 'https://shop.line.me',
            'priority': 'u=1, i',
            'referer': 'https://shop.line.me/',
            'sec-ch-ua': '"Not:A-Brand";v="99", "Google Chrome";v="145", "Chromium";v="145"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36',
        }

    def profile(self):
        response = requests.get('https://api.line.me/v2/profile', headers=self.headers)
        return response.json()

    def info_product(self,shop_name,id_product):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36',
            # 'Accept-Encoding': 'gzip, deflate, br, zstd',
            'sec-ch-ua-platform': '"Windows"',
            'sec-ch-ua': '"Not:A-Brand";v="99", "Google Chrome";v="145", "Chromium";v="145"',
            'sec-ch-ua-mobile': '?0',
            'Origin': 'https://shop.line.me',
            'Sec-Fetch-Site': 'cross-site',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Dest': 'empty',
            'Referer': 'https://shop.line.me/',
            'Accept-Language': 'en-US,en;q=0.9,th-TH;q=0.8,th;q=0.7',
        }

        response = requests.get(f'https://sc-oms-api.line-apps.com/api/v1/shopend/{shop_name}/product/{id_product}', headers=headers)
        return response.json()

    def checkout(self,json_data):
        response = requests.post('https://customer-api.line-apps.com/cart/api/v2/cart/checkout', headers=self.headers, json=json_data)
        return response.json()

    def place_order(self,name_shop,json_data):
        headers = {
            'Connection': 'keep-alive',
            'Origin': 'https://shop.line.me',
            'Referer': 'https://shop.line.me/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'cross-site',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36',
            'accept': 'application/json',
            'accept-language': 'en',
            'authorization': f'{self.token}',
            'content-type': 'application/json',
            'sec-ch-ua': '"Not:A-Brand";v="99", "Google Chrome";v="145", "Chromium";v="145"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'x-la-session-id': '27410faa389540d3',
        }
        response = requests.post(
            f'https://sc-oms-api.line-apps.com/api/v6/shopend/{name_shop}/order/place-order-qr',
            headers=headers,
            json=json_data,
        )
        return response.json()
