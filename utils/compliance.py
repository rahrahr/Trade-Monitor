from PyQt5 import QtWidgets
from trade import Trade
import re
import xlwings as xw
import pandas as pd
import json

compliance_xlsx_path = json.load(
    open('settings.json'), encoding='utf-8')["Trade Monitor Path"]
book = xw.Book(compliance_xlsx_path)
spot_compliance_sheet = book.sheets['现券交易-债券要素']
transfer_compliance_sheet = book.sheets['转托管-债券要素']

def check_spot_order() -> str:
    book.app.calculation = 'manual'
    book.app.calculate
    book.app.calculation = 'automatic'
    return spot_compliance_sheet.range('H3').value

def check_transfer_order() -> bool:
    book.app.calculation = 'manual'
    book.app.calculate
    book.app.calculation = 'automatic'
    return transfer_compliance_sheet.range('G3').value
