import xlwings as xw
import pandas as pd
import json
import sys
import datetime
from portfolio import Portfolio

_xlsx_path = json.load(
    open('settings.json'), encoding='utf-8')["Trade Monitor Path"]
book = xw.Book(_xlsx_path)


def create_portfolio(account: str) -> Portfolio:
    sheet = book.sheets[account]
    cash = float(sheet.range('D2').value)

    now_time = sheet.range('B2').value
    if isinstance(now_time, datetime.datetime):
        now_time = now_time.date().isoformat().replace('-', '/')

    bonds = sheet.range('A4').expand().options(pd.DataFrame, index=False).value

    bonds.columns = ["number", "bond_code",
                     "par_amount", "volume",
                     "amount"]
    bonds.loc[:, ["number", "volume"]] = bonds.loc[:,
                                                   ["number", "volume"]].astype(int)

    return Portfolio(account, now_time, cash, bonds)


def to_excel(portfolio: Portfolio):
    sheet = book.sheets[portfolio.account]
    sheet.range('B2').value = portfolio.now_time
    sheet.range('D2').value = portfolio.cash

    bonds = portfolio.bonds.set_index('number')
    bonds.columns = ['债券代码', '券面金额（元）', '持仓量（张）', '金额金额（元）']
    bonds.index.name = '编号'
    sheet.range('A4').value = bonds


def to_json(portfolio: Portfolio):
    json_ = json.load(open('trader.json', encoding='utf-8'))
    bonds = portfolio.bonds.loc[:, [
        'bond_code', 'par_amount']].set_index('bond_code')['par_amount'].to_dict()

    json_[portfolio.key_1][portfolio.key_2] = {}
    json_[portfolio.key_1][portfolio.key_2] = {"position": bonds}
    json_[portfolio.key_1][portfolio.key_2]["cash"] = portfolio.cash

    with open('trader.json', 'w') as f:
        json.dump(json_, f)

def find_reflective_trades(a:Portfolio, b: Portfolio):
    # Find whether transfer orders in b has been successfully settled in A.
    transfer_ids = set(a.all_trade.index) and set(b.all_trade.index)
    result = a.loc[transfer_ids, 'is_settled'].to_dict()
    return result
