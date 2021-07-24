from trade import Trade
import xlwings as xw
import pandas as pd
import json
import datetime
import sys
sys.path.append("..")
from utils import *

_xlsx_path = json.load(
    open('settings.json'), encoding='utf-8')["Trade Monitor Path"]
trade_record_sheet = xw.Book(_xlsx_path).sheets['最终交易记录']
transfer_sheet = xw.Book(_xlsx_path).sheets['转托管-债券要素']


def create_spot_trade() -> Trade:
    last_trade = trade_record_sheet.range(
        'A1').expand().options(pd.DataFrame).value.loc[1, :]
    bond_code = last_trade.loc["债券代码"]
    amount = float(last_trade.loc['交易金额（元）'])
    par_amount = float(last_trade.loc['券面金额（元）'])
    volume = int(last_trade.loc['交易量（张）'])

    trade_time = last_trade.loc['交易时间']
    settlement_date = last_trade.loc['结算日期']
    if isinstance(trade_time, datetime.datetime):
        trade_time = trade_time.date().isoformat().replace('-', '/')

    if isinstance(settlement_date, datetime.datetime):
        settlement_date = settlement_date.date().isoformat().replace('-', '/')
    settlement_days = last_trade.loc['券清算速度']
    direction = last_trade.loc['交易方向']

    is_inside_trade = (last_trade.loc['账户组'] == "内部账户") and (
        last_trade.loc['交易对手组'] == "内部账户")

    inside_id = last_trade.loc['账户组'] + last_trade.loc['交易账户']
    other_inside_id = last_trade.loc['交易对手组'] + last_trade.loc['交易对手']

    return Trade(bond_code, amount,
                 par_amount, volume,
                 trade_time, settlement_date, settlement_days,
                 direction, is_inside_trade,
                 inside_id, other_inside_id)


def create_transfer_trade() -> Trade:
    last_trade = trade_record_sheet.range(
        'A1').expand().options(pd.DataFrame).value.loc[2, :]
    bond_code = last_trade.loc["债券代码"]
    in_bond_code = last_trade.loc["债券代码（转入）"]

    amount = float(last_trade.loc['交易金额（元）'])
    par_amount = float(last_trade.loc['券面金额（元）'])
    volume = int(last_trade.loc['交易量（张）'])

    trade_time = last_trade.loc['交易时间']
    settlement_date = last_trade.loc['结算日期']
    if isinstance(trade_time, datetime.datetime):
        trade_time = trade_time.date().isoformat().replace('-', '/')

    if isinstance(settlement_date, datetime.datetime):
        settlement_date = settlement_date.date().isoformat().replace('-', '/')
    settlement_days = last_trade.loc['券清算速度']
    direction = last_trade.loc['交易方向']

    is_inside_trade = (last_trade.loc['账户组'] == "内部账户") and (
        last_trade.loc['交易对手组'] == "内部账户")

    inside_id = last_trade.loc['账户组'] + last_trade.loc['交易账户']
    other_inside_id = last_trade.loc['交易对手组'] + last_trade.loc['交易对手']

    trade = Trade(bond_code, amount,
                 par_amount, volume,
                 trade_time, settlement_date, settlement_days,
                 direction, is_inside_trade,
                 inside_id, other_inside_id)
    trade.in_bond_code = in_bond_code
    return trade
