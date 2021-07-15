import json
import re
import traceback

from compliance import *
from utils import *
from PyQt5 import QtWidgets, uic


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
        self.get_info.clicked.connect(self.getInfo)
        self.start_calculation.clicked.connect(self.calculate)

    def getInfo(self):
        code = self.code.text()
        settlment_date = self.settlement_date.text()

        if re.match(r'^\d{6,}\.(IB|SZ|SH)$', code) is None:
            QtWidgets.QMessageBox().about(self, '错误信息', '债券代码格式错误')
            return False

        quote = get_quote(code, settlment_date)
        self.zhongzhai_clean_price.setText(str(quote['中债估值']['净价']))
        self.zhongzhai_ytm.setText(str(quote['中债估值']['YTM']))

        self.qingsuansuo_clean_price.setText(str(quote['清算所估值']['净价']))
        self.qingsuansuo_ytm.setText(str(quote['清算所估值']['YTM']))

        self.zhongzheng_clean_price.setText(str(quote['中证估值']['净价']))
        self.zhongzheng_ytm.setText(str(quote['中证估值']['YTM']))

    def calculate(self):
        self.getInfo()
        code = self.code.text()
        face_value = self.face_value.text() if self.face_value.text() else '0'
        if not face_value.replace('.', '', 1).isdigit():
            QtWidgets.QMessageBox().about(self, '错误信息', '券面金额错误')
            return False
        clean_price = self.clean_price.text()
        if not clean_price.replace('.', '', 1).isdigit():
            QtWidgets.QMessageBox().about(self, '错误信息', '净价错误')
            return False
        settlement_date = self.settlement_date.text()
        settlement_days = self.settlement_days.currentText()

        # 计算到期收益率、应计利息、全价
        numbers = get_numbers(
            code, clean_price, settlement_date, settlement_days)
        self.full_price.setText(str(numbers['full price']))
        self.ytm.setText(str(numbers['ytm']))
        self.accrued_interest.setText(str(numbers['accrued interest']))

        # 净价偏离度
        get_deviation(self, clean_price)


class Ui(QtWidgets.QMainWindow):
    def __init__(self):
        super(Ui, self).__init__()
        self.resize(1500, 1000)
        layout_1 = QtWidgets.QHBoxLayout()
        layout_2 = QtWidgets.QHBoxLayout()

        self.trader_ui = TraderUi()
        self.counterparty_ui = CounterpartyUi()
        self.bond_info_ui = BondInfoUi()

        layout_1.addWidget(self.trader_ui)
        layout_1.addWidget(self.counterparty_ui)
        layout_2.addWidget(self.bond_info_ui)
        
        mainlayout = QtWidgets.QVBoxLayout()
        mainlayout.addLayout(layout_1, 10)
        mainlayout.addLayout(layout_2, 60)
        widget = QtWidgets.QWidget()
        widget.setLayout(mainlayout)
        self.setCentralWidget(widget)

        self.bond_info_ui.get_position.clicked.connect(self.getPosition)
        self.bond_info_ui.send_order.clicked.connect(self.sendOrder)

    def getPosition(self):
        trader_position = json.load(open('trader.json'))[
            self.trader_ui.list_type.currentText()]

        trader_id = self.trader_ui.account_list.currentText()
        code = self.bond_info_ui.code.text()

        bond_position = trader_position[trader_id].get(code, 0)
        cash_position = trader_position[trader_id]['cash']

        self.bond_info_ui.bond_position.setText(str(bond_position))
        self.bond_info_ui.cash_position.setText(str(cash_position))

    def sendOrder(self):
        check_order()
