import re
import traceback
from PyQt5 import QtWidgets, uic
import json


class TraderUi(QtWidgets.QMdiSubWindow):
    def __init__(self):
        super(TraderUi, self).__init__()
        uic.loadUi("trader.ui", self)
        accounts = json.load(open('trader.json'))
        self.list_type.clear()
        self.list_type.addItems(accounts.keys())
        self.list_type.currentTextChanged.connect(self.on_list_type_change)

        self.account_list.clear()
        key = self.list_type.currentText()
        value = accounts[key].keys()
        self.account_list.addItems(value)

    def on_list_type_change(self):
        self.account_list.clear()
        key = self.list_type.text()
        value = json.load(open('trader.json'))[key].keys()
        self.account_list.addItems(value)


class CounterpartyUi(QtWidgets.QMdiSubWindow):
    def __init__(self):
        super(CounterpartyUi, self).__init__()
        uic.loadUi("counterparty.ui", self)
        counterparty = json.load(open('counterparty.json'))
        self.counterparty_type.clear()
        self.counterparty_type.addItems(counterparty.keys())
        self.counterparty_type.currentTextChanged.connect(
            self.on_counterparty_type_change)

        self.counterparty_list.clear()
        key = self.counterparty_type.currentText()
        value = counterparty[key]
        self.counterparty_list.addItems(value)

    def on_counterparty_type_change(self):
        self.counterparty_list.clear()
        key = self.counterparty_type.currentText()
        value = json.load(open('counterparty.json'))[key]
        self.counterparty_list.addItems(value)


class BondInfoUi(QtWidgets.QMdiSubWindow):
    def __init__(self):
        super(BondInfoUi, self).__init__()
        uic.loadUi("bond_info.ui", self)

class Ui(QtWidgets.QMainWindow):
    def __init__(self):
        super(Ui, self).__init__()
        self.mdi = QtWidgets.QMdiArea()
        self.setCentralWidget(self.mdi)

        self.trader_ui = TraderUi()
        self.counterparty_ui = CounterpartyUi()
        self.bond_info_ui = BondInfoUi()
        self.mdi.addSubWindow(self.trader_ui)
        self.mdi.addSubWindow(self.counterparty_ui)
        self.mdi.addSubWindow(self.bond_info_ui)
