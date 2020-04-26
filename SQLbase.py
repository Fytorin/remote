# two status withdraw: transferred and processing
import sqlite3


class DB:
    conn = None
    cursor = None

    def __init__(self):
        pass

    @staticmethod
    def start():
        DB.conn = sqlite3.connect ("bot_base.db")
        DB.cursor = DB.conn.cursor ()

    @staticmethod
    def stop():
        DB.conn.commit ()
        DB.conn.close ()


class Create (DB):

    @staticmethod
    def drop_db():
        DB.cursor.executescript ("""
            DROP TABLE IF EXISTS Records;
            DROP TABLE IF EXISTS Exchanges;
            DROP TABLE IF EXISTS User;
            DROP TABLE IF EXISTS Withdraw
        """)

    @staticmethod
    def create_exchange():
        DB.cursor.execute ("""
            CREATE TABLE IF NOT EXISTS Exchanges (
                exchange_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                name_exchange TEXT
            );
        """)

    @staticmethod
    def create_user():
        DB.cursor.execute ("""
            CREATE TABLE IF NOT EXISTS User (
                telegram_id INTEGER PRIMARY KEY,
                id_inviter INTEGER,
                balance_rvb INTEGER,
                balance_satoshi REAL,
                received_hello_bonus INTEGER,
                username TEXT, 
                num_ref_with_hb INT,
                rvb_for_referrals INT
            );
        """)

    @staticmethod
    def create_record():
        DB.cursor.execute("""
            CREATE TABLE IF NOT EXISTS Records (
                record_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                telegram_id INTEGER,
                exchange_id INTEGER,
                email TEXT,
                api_key TEXT,
                api_secret TEXT,
                time_last_deal_bx TEXT,
                id_bitmex INTEGER,
                FOREIGN KEY (telegram_id) REFERENCES User(telegram_id),
                FOREIGN KEY (exchange_id) REFERENCES Exchanges(exchange_id)
            );
        """)

    @staticmethod
    def create_withdraw():
        DB.cursor.execute("""
            CREATE TABLE IF NOT EXISTS Withdraw (
                withdraw_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                telegram_id INTEGER,
                amount REAL,
                btc_wallet TEXT,
                username TEXT,
                type_withdraw TEXT,
                status TEXT,
                FOREIGN KEY (telegram_id) REFERENCES User(telegram_id)
            );
        """)


class Insert (DB):

    @staticmethod
    def add_exchange(ex_name):
        DB.cursor.execute ("INSERT INTO Exchanges VALUES (NULL, ?);", (ex_name,))

    @staticmethod
    def add_user(tg_id, id_inviter, rvb=0, balance_satoshi=0, received_hello_bn=0, username="-",
                 num_ref_with_hb=0, rvb_for_referrals=0):
        DB.cursor.execute ('''
            INSERT INTO User
            VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        ''', (tg_id, id_inviter, rvb, balance_satoshi, received_hello_bn, username, num_ref_with_hb, rvb_for_referrals))

    @staticmethod
    def add_record(tg_id, ex_id, email, api_key, api_secret, time_last_deal_bx, id_bitmex):
        DB.cursor.execute ('''
            INSERT INTO Records
            VALUES (NULL, ?, ?, ?, ?, ?, ?, ?);   
        ''', (tg_id, ex_id, email, api_key, api_secret, time_last_deal_bx, id_bitmex))

    @staticmethod
    def add_withdraw(tg_id, amount, type_withdraw, username="-", btc_wallet="", status="processing"):
        DB.cursor.execute ('''
                    INSERT INTO Withdraw
                    VALUES (NULL, ?, ?, ?, ?, ?, ?);   
                ''', (tg_id, amount, btc_wallet, username, type_withdraw, status))
        DB.cursor.execute ('SELECT MAX(withdraw_id) FROM Withdraw;')
        return DB.cursor.fetchone ()[0]


class Queries (DB):

    @staticmethod
    def get_current_num_referrals(tg_id):
        DB.cursor.execute ('''
            SELECT COUNT(*)
            FROM User
            WHERE id_inviter = ?
        ''', (tg_id,))
        return DB.cursor.fetchone ()[0]

    @staticmethod
    def get_current_num_referrals_with_hello_bonus(tg_id):
        DB.cursor.execute ('''
            SELECT COUNT(*)
            FROM User
            WHERE id_inviter = ? AND received_hello_bonus > 0
        ''', (tg_id,))
        return DB.cursor.fetchone ()[0]

    @staticmethod
    def get_balance_satoshi(tg_id):
        DB.cursor.execute ('''
            SELECT balance_satoshi
            FROM User
            WHERE telegram_id = ?
        ''', (tg_id,))
        return DB.cursor.fetchone ()[0]

    @staticmethod
    def get_balance_rvb(tg_id):
        DB.cursor.execute ('''
            SELECT balance_rvb
            FROM User
            WHERE telegram_id = ?
        ''', (tg_id,))
        return DB.cursor.fetchone ()[0]

    @staticmethod
    def get_num_referrals_from_db(tg_id):
        DB.cursor.execute ('''
            SELECT num_ref_with_hb
            FROM User
            WHERE telegram_id = ?
        ''', (tg_id,))
        return DB.cursor.fetchone ()[0]

    @staticmethod
    def get_balance_rvb_for_referrals(tg_id):
        DB.cursor.execute ('''
            SELECT rvb_for_referrals
            FROM User
            WHERE telegram_id = ?
        ''', (tg_id,))
        return DB.cursor.fetchone ()[0]

    @staticmethod
    def user_exist(tg_id):
        DB.cursor.execute ('''
            SELECT COUNT(*)
            FROM User
            WHERE telegram_id = ?
        ''', (tg_id,))
        return DB.cursor.fetchone ()[0]

    @staticmethod
    def print_withdraws():
        DB.cursor.execute ('''
            SELECT *
            FROM Withdraw
            ORDER BY withdraw_id DESC
        ''')
        return DB.cursor.fetchall ()

    @staticmethod
    def amount_withdraw(withdraw_id):
        DB.cursor.execute ('''
            SELECT amount
            FROM Withdraw
            WHERE withdraw_id = ?
        ''', (withdraw_id,))
        return DB.cursor.fetchone ()[0]

    @staticmethod
    def sum_active_cashouts(tg_id):
        DB.cursor.execute ('''
            SELECT SUM(amount)
            FROM Withdraw
            WHERE telegram_id = ? AND status = "processing"
        ''', (tg_id,))
        return DB.cursor.fetchone ()[0]

    @staticmethod
    def get_sum_all_cashouts(tg_id):
        DB.cursor.execute ('''
            SELECT SUM(amount)
            FROM Withdraw
            WHERE telegram_id = ?
        ''', (tg_id,))
        return DB.cursor.fetchone ()[0]

    @staticmethod
    def user_from_withdraw(withdraw_id):
        DB.cursor.execute ('SELECT telegram_id FROM Withdraw WHERE withdraw_id = ?', (withdraw_id,))
        return DB.cursor.fetchone ()[0]

    @staticmethod
    def received_hello_bonus(tg_id):
        DB.cursor.execute ('SELECT received_hello_bonus FROM User WHERE telegram_id = ?', (tg_id,))
        return DB.cursor.fetchone ()[0]

    @staticmethod
    def get_balance_rvb(tg_id):
        DB.cursor.execute ('SELECT balance_rvb FROM User WHERE telegram_id = ?', (tg_id,))
        return DB.cursor.fetchone ()[0]

    @staticmethod
    def get_time_start(api_key):
        DB.cursor.execute ('SELECT time_last_deal_bx FROM Records WHERE api_key = ?', (api_key,))
        return DB.cursor.fetchone ()[0]

    @staticmethod
    def get_tg_id(api_key):
        DB.cursor.execute ('SELECT telegram_id FROM Records WHERE api_key = ?', (api_key,))
        return DB.cursor.fetchone ()[0]

    @staticmethod
    def get_bitmex_records():
        DB.cursor.execute ('SELECT api_key, api_secret FROM Records WHERE exchange_id = 1')
        return DB.cursor.fetchall ()

    @staticmethod
    def check_id_bitmex(id_bitmex):
        DB.cursor.execute ('SELECT COUNT(*) FROM Records WHERE id_bitmex = ?', (id_bitmex,))
        return DB.cursor.fetchone ()[0]

    @staticmethod
    def get_bitmex_exchange_id():
        DB.cursor.execute ('SELECT exchange_id FROM Exchanges WHERE name_exchange = "bitmex"')
        return DB.cursor.fetchone ()[0]

    @staticmethod
    def get_username(tg_id):
        DB.cursor.execute ('SELECT username FROM User WHERE telegram_id = ?', (tg_id,))
        return DB.cursor.fetchone ()[0]

    @staticmethod
    def get_list_all_cashouts(tg_id):
        DB.cursor.execute ('''
            SELECT type_withdraw, amount, status
            FROM Withdraw
            WHERE telegram_id = ?
        ''', (tg_id,))
        return DB.cursor.fetchall ()

    @staticmethod
    def get_id_last_withdraw_user(tg_id):
        DB.cursor.execute ('''
            SELECT MAX(withdraw_id)
            FROM Withdraw
            WHERE telegram_id = ?
        ''', (tg_id,))
        return DB.cursor.fetchone ()[0]


class Upgrade (DB):
    @staticmethod
    def add_btc_wallet_to_withdraw(withdraw_id, btc_wallet):
        DB.cursor.execute ('UPDATE Withdraw SET btc_wallet = ? WHERE withdraw_id = ?;', (btc_wallet, withdraw_id))

    @staticmethod
    def change_balance_satoshi(tg_id, new_balance):
        DB.cursor.execute ('UPDATE User SET balance_satoshi = ? WHERE telegram_id = ?;', (new_balance, tg_id))

    @staticmethod
    def set_to_true_received_hello_bonus(tg_id):
        DB.cursor.execute ('UPDATE User SET received_hello_bonus = 1 WHERE telegram_id = ?;', (tg_id,))

    @staticmethod
    def increase_balance_rvb(tg_id, add_num):
        new_balance_rvb = add_num + Queries.get_balance_rvb (tg_id)
        DB.cursor.execute ('''
            UPDATE User 
            SET balance_rvb = ? 
            WHERE telegram_id = ?;
        ''', (new_balance_rvb, tg_id))

    @staticmethod
    def increase_balance_rvb_for_referrals(tg_id, add_num):
        new_balance_rvb_for_referrals = add_num + Queries.get_balance_rvb_for_referrals (tg_id)
        DB.cursor.execute ('''
            UPDATE User 
            SET rvb_for_referrals = ? 
            WHERE telegram_id = ?;
        ''', (new_balance_rvb_for_referrals, tg_id))

    @staticmethod
    def rewrite_num_referrals(tg_id, new_num_ref):
        DB.cursor.execute ('''
            UPDATE User 
            SET num_ref_with_hb = ? 
            WHERE telegram_id = ?;
        ''', (new_num_ref, tg_id))

    @staticmethod
    def set_time_last_deal_bitmex(api_key, new_time):
        DB.cursor.execute ('''
            UPDATE Records 
            SET time_last_deal_bx = ? 
            WHERE api_key = ?;
        ''', (new_time, api_key))

    @staticmethod
    def for_bitmex_increase_balance_satoshi(api_key, amount):
        tg_id = Queries.get_tg_id (api_key)
        new_balance = amount + Queries.get_balance_satoshi (tg_id)
        DB.cursor.execute ('''
            UPDATE User 
            SET balance_satoshi = ? 
            WHERE telegram_id = ?;
        ''', (new_balance, tg_id))

    @staticmethod
    def change_status_withdraw_request(withdraw_id, status):
        DB.cursor.execute ('UPDATE Withdraw SET status = ? WHERE withdraw_id = ?;', (status, withdraw_id))


class Delete (DB):

    @staticmethod
    def del_last_withdraw_user(tg_id):
        withdraw_id = Queries.get_id_last_withdraw_user (tg_id)
        if withdraw_id == None:
            return
        DB.cursor.execute ('DELETE FROM Withdraw WHERE withdraw_id = ?', (withdraw_id,))


def clearing_db():
    Create.start ()
    Create.drop_db ()
    Create.create_exchange ()
    Create.create_user ()
    Create.create_record ()
    Create.create_withdraw ()
    Create.stop ()


if __name__ == "__main__":
    clearing_db ()
