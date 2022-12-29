import requests
import six
import json
from decimal import Decimal
from requests import get as r_get

class Wallet(object):
    def __init__(self, ip='127.0.0.1', port='5359'):
        self.url = f'http://{ip}:{port}/api/'

    def make_wallet_get_request(self, method):
        url = self.url + method
        r = requests.get(url, timeout=8)
        r.raise_for_status()
        print(f'GET - {self.url} - {method}')
        if r.status_code != 200:
            print(f'ERROR GET - {self.url} - {method} - {r.status_code}')
            return ""
        else:
            if "error" in r.json():
                print(f'ERROR GET - {self.url} - {method}')
                print(r.json()['error'])
                return ""
            else:
                return r.json()

    def make_wallet_post_request(self, method, params={}, timeout=120):
        url = self.url + method
        print(f'Request to wallet: {url}')
        r = requests.post(
            url,
            timeout=timeout,   # Long timeout, but can take a lot of time to generate new addr
            data=json.dumps(params)
        )
        r.raise_for_status()
        print(f'POST - {self.url} - {method}')
        if r.status_code != 200:
            print(f'ERROR POST - {self.url} - {method} - {r.status_code}')
            return ""
        else:
            if "error" in r.json():
                print(f'ERROR POST - {self.url} - {method}')
                print(r.json()['error'])
                return ""
            else:
                print("POST request OK: " + str(r.json()))	
                return r.json()

    def height(self):
        return self.make_wallet_get_request('GetHeight')

    def new_address(self, height=None, hash_function=None):
        data = {}

        if height:
            data['height'] = height
        if hash_function:
            data['hash_function'] = hash_function

        _address = self.make_wallet_post_request('AddNewAddress',data, timeout=240)

        if 'address' in _address:
            return _address['address']
        else:
            return ""

    def new_account(self, label=None):
        return self.new_address()

    def balances(self, address, atomic=True):
        #_balance = self.make_wallet_get_request('GetTotalBalance')
        data = {'address': address}
        _balance = self.make_wallet_post_request('GetBalance', data)
        if atomic:
            if 'balance' in _balance:
                
                return _balance['balance']
        else:
            bal = qrl.from_atomic(_balance['balance'])
            return bal
        return ""

    def listAddresses(self):
        addresses = self.make_wallet_get_request('ListAddresses')

        if "addresses" in addresses:
            return addresses["addresses"]
        
        return []

    def getOTS(self, address):
        data = {'address': address}
        ots_info = self.make_wallet_post_request('GetOTS', data)
        return ots_info["next_unused_ots_index"]

    def transfer(self, addr_from, addr_to, amount, fee=0):
        #ost_index = self.getOTS(addr_from)
        data = {
            'addresses_to': [addr_to],
            'amounts': [amount],
            'fee': fee,
            'signer_address': addr_from
            #'ots_index': ost_index
        }
        transfer = self.make_wallet_post_request('RelayTransferTxn', data, timeout=200)
        return transfer

    def get_transfers(self, address):
        data = {'address': address}
        print(f'get_transfers - {address}')
        return self.make_wallet_post_request('GetTransactionsByAddress', data)

    def transfers(self, address):
        return self.get_transfers(address)

    def get_transaction(self, tx_hash):
        data = {'tx_hash': tx_hash}
        print(tx_hash)
        return self.make_wallet_post_request('GetTransaction', data)

    def accounts(self):
        return self.get_accounts()

    def get_accounts(self):
        return self.listAddresses()


    def get_balances(self, address):
        data = {'address': address}
        return self.make_wallet_post_request('GetBalance', data)

    def get_blockbynumber(self, block_number):
        data = {'block_number': block_number}
        return self.make_wallet_post_request('GetBlockByNumber', data)

    def sweep_all(self,account, dest_address):
        #TODO: see to transfer balance
        return False


class Coingecko(object):
    def __init__(self):
        pass
        
    def get_market_data(self, coin_name='quantum-resistant-ledger'):
        headers = {'accept': 'application/json'}
        url = f'https://api.coingecko.com/api/v3/coins/{coin_name}'
        print(f'GET - {url}')
        r = r_get(url, timeout=8, headers=headers)
        return r.json()

    def get_coin_price(self, cur='usd'):
        d = self.get_market_data()
        amt = d['market_data']['current_price'][cur]
        print(f'Coin price - {amt}')
        return amt
            
    def get_qrl_value(self, dollar_value, currency):
        price = self.get_coin_price(cur=currency.lower())
        if price is not None:
            try:
                float_value = float(dollar_value) / float(price)
                if not isinstance(float_value, float):
                    raise Exception("Dollar value should be a float.")
            except Exception as e:
                print(e)

            return float_value

        raise Exception("Failed to get dollar value.")
        
        
class CoinUtils(object):
    def __init__(self):
        pass

    def to_atomic(self, amount):
        if not isinstance(amount, (Decimal, float) + six.integer_types):
            raise ValueError("Amount does not have numeric type.")
        return int(amount * 10**self.decimal_points)

    def from_atomic(self, amount):
        fn = Decimal(amount) * self.full_notation
        return (fn).quantize(self.full_notation)

    def as_real(self, amount):
        real = Decimal(amount).quantize(self.full_notation)
        return float(real)


class QRL(CoinUtils):
    def __init__(self):
        self.decimal_points = 9
        self.full_notation = Decimal('0.000000001')


wallet = Wallet("localhost", "5359")

qrl = QRL()

coingecko = Coingecko()


