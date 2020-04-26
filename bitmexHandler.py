# во время парсинга базы будет почти невозможно зарегаться
# считается доход людям только от момента регистрации в боте
import bitmex
from datetime import timezone
from datetime import datetime
from datetime import timedelta
from dateutil.tz import tzutc
import pytz

from SQLbase import (DB, Upgrade, Queries)

from config import bitmex_id_admin
from config import commission_return_ratio


class BitmexRefChecker:

    def __init__(self, api_key, api_secret):
        self.api_key = api_key
        self.api_secret = api_secret

    def is_referral(self):
        try:
            if self.client.User.User_getAffiliateStatus ().result ()[0]['referrerAccount'] == bitmex_id_admin:
                return True
            else:
                return False
        except:
            return False

    def get_id(self):
        try:
            self.client = bitmex.bitmex (test=False,
                                         api_key=self.api_key,
                                         api_secret=self.api_secret)
            id = self.client.User.User_get ().result ()[0]['id']
            return id
        except:
            return None


class BitmexParser:

    def __init__(self, api_key, api_secret):
        self.api_key = api_key
        self.api_secret = api_secret

    def parse(self):
        while True:
            time_start = self._get_current_time_start ()
            time_end = self._get_current_time_end ()
            trade_history = self._get_trade_history (time_start, time_end)
            if len (trade_history) == 0:
                break
            self._bd_update_time_start (self._get_new_time_start (trade_history))
            self._bd_update_money (self._get_comm (trade_history) * commission_return_ratio)
            if len (trade_history) < 500:
                break

    # return from db Records->time_lat_rec_bx
    # for the first time will return the registration time
    def _get_current_time_start(self):
        DB.start ()
        old_time_string = Queries.get_time_start (self.api_key)
        old_time = self._convert_string_to_time (old_time_string)
        DB.stop ()
        # print("Start time", old_time)
        return old_time

    # return current time
    def _get_current_time_end(self):
        return datetime.now (tz=tzutc ())

    # time_end - current time
    def _get_trade_history(self, time_start, time_end):
        self.client = bitmex.bitmex (test=False,
                                     api_key=self.api_key,
                                     api_secret=self.api_secret)

        trade_history = self.client.Execution.Execution_getTradeHistory (filter='{"execType": ["Funding", "Trade"]}',
                                                                         count=500,
                                                                         reverse=False,
                                                                         startTime=time_start,
                                                                         endTime=time_end).result ()
        return trade_history[0]

    # get the oldest date from trade history
    def _get_new_time_start(self, trade_history):
        return trade_history[-1]['timestamp'] + timedelta (seconds=1)

    def _bd_update_time_start(self, new_time):
        DB.start ()
        Upgrade.set_time_last_deal_bitmex (self.api_key, str (new_time))
        DB.stop ()

    def _get_comm(self, trade_history):
        amount = 0
        for item in trade_history:
            i = item['execComm']
            if i > 0:
                amount += i
        # print(amount)
        return amount

    def _bd_update_money(self, amount):
        DB.start ()
        Upgrade.for_bitmex_increase_balance_satoshi (self.api_key, amount)
        DB.stop ()

    def _convert_string_to_time(self, date_string, timezone='GMT'):
        date_time_obj = datetime.strptime (date_string[:26], '%Y-%m-%d %H:%M:%S.%f')
        date_time_obj_timezone = pytz.timezone (timezone).localize (date_time_obj)
        return date_time_obj_timezone
