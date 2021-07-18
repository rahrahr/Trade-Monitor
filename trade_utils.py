from trade import Trade
import xlwings as xw
import pandas as pd
import json

_xlsx_path = json.load(
    open('settings.json'), encoding='utf-8')["Trade Monitor Path"]
trade_record_sheet = xw.Book(_xlsx_path).sheets[2]


def create_last_trade() -> Trade:
    last_trade = trade_record_sheet.range(
        'A1').expand().options(pd.DataFrame).value.iloc[-1, :]
    bond_code = last_trade.loc["债券代码"]
    amount = float(last_trade.loc['交易金额（元）'])
    par_amount = float(last_trade.loc['券面金额（元）'])
    volume = int(last_trade.loc['交易量（张）'])

    trade_time = last_trade.loc['交易时间']
    settlement_date = last_trade.loc['结算日期']
    direction = last_trade.loc['交易方向']

    is_inside_trade = (last_trade.loc['交易账户'] == "内部账户") and (
        last_trade.loc['交易对手'] == "内部账户")

    return Trade(bond_code, amount,
                 par_amount, volume,
                 trade_time, settlement_date,
                 direction, is_inside_trade)
