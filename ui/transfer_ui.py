import json
import re
from PyQt5 import QtWidgets, uic
import traceback
import sys
sys.path.append("..")
from utils import *

class TransferUi(QtWidgets.QMdiSubWindow):
    def __init__(self):
        super(TransferUi, self).__init__()
        uic.loadUi("ui/transfer.ui", self)
        self.get_transfer_info.clicked.connect(self.getTransferInfo)
        self.get_position.clicked.connect(self.getPosition)

        accounts = json.load(open('trader.json', encoding='utf-8'))
        self.list_type.clear()
        self.list_type.addItems(accounts.keys())
        self.list_type.currentTextChanged.connect(self.on_list_type_change)

        self.account_list.clear()
        key = self.list_type.currentText()
        value = accounts[key].keys()
        self.account_list.addItems(value)

        self.list_type_2.clear()
        self.list_type_2.addItems(accounts.keys())
        self.list_type_2.currentTextChanged.connect(self.on_list_type_change_2)

        self.account_list_2.clear()
        key = self.list_type_2.currentText()
        value = accounts[key].keys()
        self.account_list_2.addItems(value)

    def on_list_type_change(self):
        self.account_list.clear()
        key = self.list_type.text()
        value = json.load(open('trader.json', encoding='utf-8'))[key].keys()
        self.account_list.addItems(value)

    def on_list_type_change_2(self):
        self.account_list_2.clear()
        key = self.list_type_2.text()
        value = json.load(open('trader.json', encoding='utf-8'))[key].keys()
        self.account_list.addItems(value)

    def getTransferInfo(self):
        code = self.code.text()
        if re.match(r'^\d{6,}\.(IB|SZ|SH)$', code) is None:
            QtWidgets.QMessageBox().about(self, '错误信息', '债券代码格式错误')
            return False
        self._export_transfer_info()

    def getPosition(self):
        trader_position = json.load(open('trader.json', encoding='utf-8'))[
            self.list_type.currentText()]

        trader_id = self.account_list.currentText()
        code = self.code.text()

        bond_position = trader_position[trader_id]['position'].get(code, 0)
        cash_position = trader_position[trader_id]['cash']

        self.bond_position.setText(str(bond_position))
        self.cash_position.setText(str(cash_position))

    def _export_transfer_info(self):
        excel_utils._export_transfer_info(self)
