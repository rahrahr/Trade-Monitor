from PyQt5 import QtWidgets
from trade import Trade
import re
import xlwings as xw
import pandas as pd
import json

compliance_xlsx_path = json.load(
    open('settings.json'), encoding='utf-8')["Trade Monitor Path"]
spot_compliance_sheet = xw.Book(compliance_xlsx_path).sheets['现券交易-债券要素']
transfer_compliance_sheet = xw.Book(compliance_xlsx_path).sheets['转托管-债券要素']

def check_spot_order() -> str:
    return spot_compliance_sheet.range('H3').value

def check_transfer_order() -> bool:
    return transfer_compliance_sheet.range('G3').value
