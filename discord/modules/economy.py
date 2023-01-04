import random
import sqlite3
from functools import wraps
from typing import Tuple, List

from modules.qrld import qrlnode
from modules.qrl import wallet, qrl
from modules.helpers import *
import math
from decimal import Decimal
import threading
from time import sleep

Entry = Tuple[int, int, int]

class Economy:
    """A wrapper for the economy database"""
    def __init__(self):
        self.open()

    def open(self):
        """Initializes the database"""
        self.conn = sqlite3.connect('economy.db', check_same_thread=False)
        self.cur = self.conn.cursor()
        self.cur.execute("""CREATE TABLE IF NOT EXISTS economy (
            user_id INTEGER NOT NULL PRIMARY KEY,
            qrl INTEGER NOT NULL DEFAULT 0,
            qrl_addr TEXT NOT NULL DEFAULT "",
            createdDate TIMESTAMP NOT NULL DEFAULT (strftime('%s', 'now')),
            sync_in_progress INTEGER NOT NULL DEFAULT 0
        )""")

    def close(self):
        """Safely closes the database"""
        if self.conn:
            self.conn.commit()
            self.cur.close()
            self.conn.close()

    def _commit(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            result = func(self, *args, **kwargs)
            self.conn.commit()
            return result
        return wrapper

    def get_entry(self, user_id: int) -> Entry:
        self.cur.execute(
            "SELECT * FROM economy WHERE user_id=:user_id",
            {'user_id': user_id}
        )
        result = self.cur.fetchone()
        if result: return result
        return self.new_entry(user_id)

    @_commit
    def new_entry(self, user_id: int) -> Entry:
        try:
            qrl_node = qrlnode()
            addr = qrl_node.get_address()
            self.cur.execute(
                "INSERT INTO economy(user_id, qrl, qrl_addr) VALUES(?,?,?)",
                (user_id, 0, addr)
            )
            return self.get_entry(user_id)
        except sqlite3.IntegrityError:
            return self.get_entry(user_id)

    @_commit
    def remove_entry(self, user_id: int) -> None:
        self.cur.execute(
            "DELETE FROM economy WHERE user_id=:user_id",
            {'user_id': user_id}
        )

    @_commit
    def set_money(self, user_id: int, money: int) -> Entry:
        self.cur.execute(
            "UPDATE economy SET qrl=? WHERE user_id=?",
            (money, user_id)
        )
        return self.get_entry(user_id)

    @_commit
    def add_money(self, user_id: int, money_to_add: int) -> Entry:
        money = self.get_entry(user_id)[1]
        total = money + money_to_add
        if total < 0:
            total = 0
        self.set_money(user_id, total)
        return self.get_entry(user_id)

    @_commit
    def withdraw(self, user_id: int, payout_addr: str, money_to_transfer: int) -> Entry:
        money = self.get_entry(user_id)[1]              	
        total = money - money_to_transfer
       
        if total < 0:
            return "Not enough funds."
         
        else:
            aqrl_to_send = qrl.to_atomic(money_to_transfer) 
            res = wallet.transfer(QRL_ADDR, payout_addr, aqrl_to_send)
            if 'tx' in res:
                self.set_money(user_id, total)
                return(f'Sent QRL, Tx ID: {res["tx"]["transaction_hash"]}')
            elif 'error' in res:
                return(f'There was a problem sending QRL: {res["error"]}')
            else:
                return('Unable to send QRL')            

    @_commit
    def set_sync_in_progress(self, user_id: int, sync_in_progress: int) -> Entry:
        self.cur.execute(
            "UPDATE economy SET sync_in_progress=? WHERE user_id=?",
            (sync_in_progress, user_id)
        )
        return self.get_entry(user_id)
               
    @_commit
    def sync(self, user_id: int) -> Entry:
        sync_in_progress = self.get_entry(user_id)[4]
        if not sync_in_progress:
            self.set_sync_in_progress(user_id,1)
            user_qrl_addr = self.get_entry(user_id)[2]
            print(f"Get balance for {user_qrl_addr}")
            balances = Decimal(wallet.balances(user_qrl_addr))
            
            if balances > 0:
                print(f"{user_qrl_addr} contains {balances}. Transfer to {QRL_ADDR}")
                res = wallet.transfer(user_qrl_addr, QRL_ADDR, str(balances))
                if 'tx' in res:
                    qrl_amount = math.floor(qrl.from_atomic(balances))                                   
                    thread = threading.Thread(target=self.wait_for_transfer, args=(user_id, user_qrl_addr, qrl_amount, res))
                    thread.start()
                    #self.add_money(user_id, qrl_amount)
                    return(f'{qrl_amount} QRL will be added to your account soon.')             

                elif 'error' in res:
                    self.set_sync_in_progress(user_id,0)
                    return(f'There was a problem sending QRL: {res["error"]}')
                else:
                    self.set_sync_in_progress(user_id,0)
                    return('Unable to add QRL') 
            else:
                self.set_sync_in_progress(user_id,0)
                return(f'Account is empty. Please send QRL to this address: {user_qrl_addr}.') 
        else:
            return('Sync in progress, please try again later')


    def wait_for_transfer(self, user_id, user_qrl_addr, qrl_amount, res):
        notConfirm = True
        while notConfirm:
            nbConf = wallet.get_transaction(res["tx"]["transaction_hash"])["confirmations"]
            print(f"Sync nbConf: {nbConf}")
            if int(nbConf) > 0:
                notConfirm = False
                self.set_sync_in_progress(user_id,0)
                self.add_money(user_id, qrl_amount)
            else:
                sleep(10) 
        
                
    def random_entry(self) -> Entry:
        self.cur.execute("SELECT * FROM economy")
        return random.choice(self.cur.fetchall())

    def top_entries(self, n: int=0) -> List[Entry]:
        self.cur.execute(f"SELECT * FROM economy ORDER BY qrl DESC LIMIT {n}")
        return (self.cur.fetchall())
