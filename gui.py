import json
import re
import traceback
import pandas as pd
import xlwings as xw
from PyQt5 import QtWidgets, uic

import trade
import compliance
import utils
import trade_utils
import portfolio_utils


class TraderUi(QtWidgets.QMdiSubWindow):
    def __init__(self):
        super(TraderUi, self).__init__()
        uic.loadUi("trader.ui", self)
        accounts = json.load(open('trader.json', encoding='utf-8'))
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
        value = json.load(open('trader.json', encoding='utf-8'))[key].keys()
        self.account_list.addItems(value)


class CounterpartyUi(QtWidgets.QMdiSubWindow):
    def __init__(self):
        super(CounterpartyUi, self).__init__()
        uic.loadUi("counterparty.ui", self)
        counterparty = json.load(open('counterparty.json', encoding='utf-8'))
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
        value = json.load(open('counterparty.json', encoding='utf-8'))[key]
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

        quote = compliance.get_quote(code)
        self.zhongzhai_clean_price.setText(
            '{:.4f}'.format(quote['中债估值']['净价']))
        self.zhongzhai_ytm.setText(
            '{:.4f}'.format(quote['中债估值']['YTM']))

        self.qingsuansuo_clean_price.setText(
            '{:.4f}'.format(quote['清算所估值']['净价']))
        self.qingsuansuo_ytm.setText('{:.4f}'.format(quote['清算所估值']['YTM']))

        self.zhongzheng_clean_price.setText(
            '{:.4f}'.format(quote['中证估值']['净价']))
        self.zhongzheng_ytm.setText('{:.4f}'.format(quote['中证估值']['YTM']))

    def _export_info(self):
        compliance._export_info(self)

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
        numbers = utils.get_numbers(
            code, clean_price, settlement_date, settlement_days)
        self.full_price.setText('{:.4f}'.format(
            numbers['full price'] if numbers['full price'] else 0))
        self.ytm.setText('{:.4f}'.format(
            100 * numbers['ytm'] if numbers['ytm'] else 0))
        self.accrued_interest.setText('{:.4f}'.format(
            numbers['accrued interest'] if numbers['accrued interest'] else 0))
        self.settlement_amount.setText('{:.4f}'.format(
            numbers['full price'] * 100 * float(self.face_value)))
        # 净价偏离度
        utils.set_deviation(self, clean_price)


class TransferUi(QtWidgets.QMdiSubWindow):
    def __init__(self):
        super(TransferUi, self).__init__()
        uic.loadUi("transfer.ui", self)
        self.get_transfer_info.clicked.connect(self.getTransferInfo)
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
        target_exchange = self.target_exchange.text().upper()
        transfer_start_date = self.transfer_start_date.text()

        if re.match(r'^\d{6,}\.(IB|SZ|SH)$', code) is None:
            QtWidgets.QMessageBox().about(self, '错误信息', '债券代码格式错误')
            return False

        if target_exchange not in ('IB', 'SZ', 'SH'):
            QtWidgets.QMessageBox().about(self, '错误信息', "转入市场不属于('IB','SZ','SH')")
            return False


class Ui(QtWidgets.QMainWindow):
    def __init__(self):
        super(Ui, self).__init__()
        self.resize(1500, 1000)
        layout_1 = QtWidgets.QHBoxLayout()
        layout_2 = QtWidgets.QHBoxLayout()

        self.trader_ui = TraderUi()
        self.counterparty_ui = CounterpartyUi()
        self.bond_info_ui = BondInfoUi()
        self.transfer_ui = TransferUi()

        layout_1.addWidget(self.trader_ui)
        layout_1.addWidget(self.counterparty_ui)
        layout_2.addWidget(self.bond_info_ui)
        layout_2.addWidget(self.transfer_ui)

        mainlayout = QtWidgets.QVBoxLayout()
        mainlayout.addLayout(layout_1, 10)
        mainlayout.addLayout(layout_2, 60)
        widget = QtWidgets.QWidget()
        widget.setLayout(mainlayout)
        self.setCentralWidget(widget)

        self.bond_info_ui.get_position.clicked.connect(self.getPosition)
        self.bond_info_ui.send_order.clicked.connect(self.sendOrder)
        self.bond_info_ui.is_last_trade.clicked.connect(self.updateTplus1)

        self.transfer_ui.get_position.clicked.connect(self.getPosition)
        self.transfer_ui.send_order.clicked.connect(self.sendTransferOrder)
        self.bond_info_ui.is_last_trade.clicked.connect(self.updateTransfer)

        # create Portfolio instances for all accounts.
        self.portfolios = {}
        portflios = json.load(open('trader.json', encoding='utf-8'))
        for key_1 in portflios.keys():
            for key_2, item_2 in portflios[key_1].items():
                account = key_1 + key_2
                self.portfolios[key_1 + key_2] =\
                    portfolio_utils.create_portfolio(account)
                # Makes it easier to update json file
                self.portfolios[key_1 + key_2].key_1 = key_1
                self.portfolios[key_1 + key_2].key_2 = key_2

    def getPosition(self):
        trader_position = json.load(open('trader.json', encoding='utf-8'))[
            self.trader_ui.list_type.currentText()]

        trader_id = self.trader_ui.account_list.currentText()
        code = self.bond_info_ui.code.text()

        bond_position = trader_position[trader_id]['position'].get(code, 0)
        cash_position = trader_position[trader_id]['cash']

        self.bond_info_ui.bond_position.setText(str(bond_position))
        self.bond_info_ui.cash_position.setText(str(cash_position))

    def _export_trader_info(self):
        compliance._export_trader_info(self)

    def sendOrder(self):
        self.bond_info_ui._export_info()
        self._export_trader_info()
        if not compliance.check_order():
            QtWidgets.QMessageBox().about(self, '错误信息', '交易未完成')
            return False

        try:
            trade = trade_utils.create_last_trade()
        except:
            QtWidgets.QMessageBox().about(self, '错误信息', '创建Trade对象出错，请检查“最终交易记录”Sheet是否存在缺失数值')
            return False

        # 更新Portfolio对象
        try:
            if trade.settlement_days == 'T+0':
                account = trade.inside_id
                self.portfolios[account].portfolio_update_t0(trade)
            elif trade.settlement_days == 'T+1':
                account = trade.inside_id
                self.portfolios[account].portfolio_update_t0(trade)
                self.portfolios[account].append_waiting_trade(trade)

            if trade.is_inside_trade:
                if trade.settlement_days == 'T+0':
                    account = trade.other_inside_id
                    self.portfolios[account].portfolio_update_t0(
                        trade.reversed())
                elif trade.settlement_days == 'T+1':
                    account = trade.other_inside_id
                    self.portfolios[account].portfolio_update_t0(trade)
                    self.portfolios[account].append_waiting_trade(
                        trade.reversed())

        except:
            QtWidgets.QMessageBox().about(
                self, '错误信息', '更新Portfolio对象出错，请检查“最终交易记录”Sheet是否存在缺失数值')
            return False

        # 写入Excel和json文件
        if not trade.is_inside_trade:
            portfolio_utils.to_excel(self.portfolios[trade.inside_id])
            portfolio_utils.to_json(self.portfolios[trade.inside_id])
        else:
            portfolio_utils.to_excel(self.portfolios[trade.inside_id])
            portfolio_utils.to_excel(self.portfolios[trade.other_inside_id])

            portfolio_utils.to_json(self.portfolios[trade.inside_id])
            portfolio_utils.to_json(self.portfolios[trade.other_inside_id])

    def sendTransferOrder(self):
        self.transfer_ui._export_info()
        self._export_trader_info()
        if not compliance.check_order():
            QtWidgets.QMessageBox().about(self, '错误信息', '交易未完成')
            return False

        try:
            trade = trade_utils.create_last_trade()
        except:
            QtWidgets.QMessageBox().about(self, '错误信息', '创建Trade对象出错，请检查“最终交易记录”Sheet是否存在缺失数值')
            return False

        # 更新Portfolio对象
        try:
            if trade.settlement_days == 'T+0':
                account = trade.inside_id
                self.portfolios[account].portfolio_update_t0(trade)
            elif trade.settlement_days == 'T+1':
                account = trade.inside_id
                self.portfolios[account].portfolio_update_t0(trade)
                self.portfolios[account].append_waiting_trade(trade)

            if trade.is_inside_trade:
                if trade.settlement_days == 'T+0':
                    account = trade.other_inside_id
                    self.portfolios[account].portfolio_update_t0(
                        trade.reversed())
                elif trade.settlement_days == 'T+1':
                    account = trade.other_inside_id
                    self.portfolios[account].portfolio_update_t0(trade)
                    self.portfolios[account].append_waiting_trade(
                        trade.reversed())

        except:
            QtWidgets.QMessageBox().about(
                self, '错误信息', '更新Portfolio对象出错，请检查“最终交易记录”Sheet是否存在缺失数值')
            return False

        # 写入Excel和json文件
        if not trade.is_inside_trade:
            portfolio_utils.to_excel(self.portfolios[trade.inside_id])
            portfolio_utils.to_json(self.portfolios[trade.inside_id])
        else:
            portfolio_utils.to_excel(self.portfolios[trade.inside_id])
            portfolio_utils.to_excel(self.portfolios[trade.other_inside_id])

            portfolio_utils.to_json(self.portfolios[trade.inside_id])
            portfolio_utils.to_json(self.portfolios[trade.other_inside_id])

    def updateTplus1(self):
        for key in self.portfolios:
            self.portfolios[key].portfolio_update_t1()

    def updateTransfer(self):
        for key in self.portfolios:
            self.portfolios[key].portfolio_update_transfer()
