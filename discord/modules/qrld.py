import time
import uuid
import qrcode
import json

from modules.qrl import wallet


class qrlnode:
    def __init__(self):
        for i in range(5):
            try:
                print( "Attempting to connect to qrl wallet." )
                addresses = wallet.listAddresses()
                print(addresses)
                print("successfully contacted qrl wallet")
                break

            except Exception as e:
                print("Connection error: {}".format(e))
                print("Sleeping for {}s then attempting again... {}/{}...".format(15, i + 1, 5))
                time.sleep(15)
        else:
            raise Exception(
                "Could not connect to qrld. \
                Check your settings and try again."
            )

    def create_qr(self, uuid, address):
        #qr_str = "{}?amount={}&label={}".format(address.upper(), value, uuid)
        qr_str = "{}".format(address)

        img = qrcode.make(qr_str)
        img.save("{}.png".format(uuid))
        return

    def check_payment(self, address):
        try:
            transactions = wallet.get_transfers(address)
            print(transactions)

        except Exception as e:
            print(e)
            print(
                "Can't connect to wallet, pausing for a few seconds in case of high load."
            )
            time.sleep(5)
            return 0, 0, 0

        if "mini_transactions" not in transactions.keys():
            return 0, 0, 0
        else:
            transactions = transactions["mini_transactions"]

        conf_paid = 0
        unconf_paid = 0
        current_block_height = wallet.height()["height"]
        print("current_block_height: " + current_block_height)
        tx_ids=""
        for tx in transactions:
            print(tx)

            tx_details = wallet.get_transaction(tx["transaction_hash"])
            if "block_number" not in tx_details.keys():
                return 0, 0, 0
                
            if len(tx_ids) > 0:
            	tx_ids += ","
            	
            tx_ids += tx["transaction_hash"]
                         
            if (
                int(current_block_height) - int(tx_details["block_number"])
                >= 5
            ):
                conf_paid += int(tx["amount"]) / 10 ** 9
            else:
                unconf_paid += int(tx["amount"]) / 10 ** 9

        return conf_paid, unconf_paid, tx_ids

    def get_address(self):
        for i in range(5):
            try:
                address_data = wallet.new_address(height=8)
                print(address_data)
                return address_data

            except Exception as e:
                print(e)
                print(
                    "Attempting again... {}/{}...".format(
                        i + 1, 5
                    )
                )
            if 5 - i == 1:
                print("Reconnecting...")
                self.__init__()
        return None
