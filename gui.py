import datetime
import json
import re
from PyQt5 import QtWidgets, uic
from QuantLib import Date, China, Period
import traceback

from ui import *
from utils import *
import trade


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
        self.bond_info_ui.send_settlement.clicked.connect(self.sendSettlement)

        self.transfer_ui.send_order.clicked.connect(self.sendTransferOrder)
        self.transfer_ui.is_last_trade.clicked.connect(self.updateTransfer)

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
        excel_utils._export_trader_info(self)

    def sendOrder(self):
        self.bond_info_ui._export_info()
        self._export_trader_info()
        x = compliance.check_spot_order()
        if ('失败' in x) or ('不合规' in x) or ('不达标' in x):
            error_message = '报单失败，失败原因：\n'+'!\n'.join(x.split('！'))
            QtWidgets.QMessageBox().about(self, '错误信息', error_message)
            return False

        elif '预警' in x:
            error_message = '交易预警：\n'+'!\n'.join(x.split('！'))
            QtWidgets.QMessageBox().about(self, '预警', error_message)

        try:
            trade = trade_utils.create_spot_trade()
        except:
            QtWidgets.QMessageBox().about(self, '错误信息', traceback.format_exc())
            return False

        # 更新Portfolio对象
        try:
            if trade.settlement_days == 'T+0':
                account = trade.inside_id
                self.portfolios[account].portfolio_update_t0(trade)
            elif trade.settlement_days == 'T+1':
                account = trade.inside_id
                if trade.bond_code[-2:] != "IB":
                    self.portfolios[account].portfolio_update_t0(trade)
                self.portfolios[account].append_waiting_trade(trade)

            if trade.is_inside_trade:
                if trade.settlement_days == 'T+0':
                    account = trade.other_inside_id
                    self.portfolios[account].portfolio_update_t0(
                        trade.reversed())
                elif trade.settlement_days == 'T+1':
                    account = trade.other_inside_id
                    if trade.bond_code[-2:] != "IB":
                        self.portfolios[account].portfolio_update_t0(
                            trade.reversed())
                    self.portfolios[account].append_waiting_trade(
                        trade.reversed())

        except:
            QtWidgets.QMessageBox().about(
                self, '错误信息', traceback.format_exc())
            return False

        # 写入Excel和json文件
        if not trade.is_inside_trade:
            self.portfolios[trade.inside_id].to_excel()
            self.portfolios[trade.inside_id].to_json()
        else:
            self.portfolios[trade.inside_id].to_excel()
            self.portfolios[trade.other_inside_id].to_excel()

            self.portfolios[trade.inside_id].to_json()
            portfolio_utils.to_json(self.portfolios[trade.other_inside_id])

        QtWidgets.QMessageBox().about(self, '', '报单完成')

    def sendTransferOrder(self):
        self.transfer_ui._export_transfer_info()
        x = compliance.check_transfer_order()
        if x != '交易成功':
            error_message = '转托管报单失败，失败原因：\n'+'!\n'.join(x.split('！'))
            QtWidgets.QMessageBox().about(self, '错误信息', error_message)
            return False

        try:
            trade = trade_utils.create_transfer_trade()
        except:
            QtWidgets.QMessageBox().about(self, '错误信息', traceback.format_exc())
            return False

        # 更新Portfolio对象
        try:
            trade.settlement_days == 'T+1'
            account = trade.inside_id
            self.portfolios[account].portfolio_update_t0(trade)

            if trade.is_inside_trade:
                account = trade.other_inside_id
                self.portfolios[account].portfolio_update_t0(trade.reversed())
                self.portfolios[account].append_waiting_trade(
                    trade.reversed())

        except:
            QtWidgets.QMessageBox().about(
                self, '错误信息', traceback.format_exc())
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

        QtWidgets.QMessageBox().about(self, '', '报单完成')

    def sendSettlement(self):
        #当前账户提交清算申请
        list_type = self.trader_ui.list_type.currentText()
        trader_id = self.trader_ui.account_list.currentText()
        key = list_type + trader_id
        
        self.portfolios[key].settle()
        QtWidgets.QMessageBox().about(self, '', '结算报单完成')

    def updateTplus1(self):
        cal = China(China.IB)
        for key in self.portfolios:
            date = self.portfolios[key].now_time
            if isinstance(date, datetime.datetime):
                date = date.date().isoformat()
                date = '/'.join([i.lstrip('0') for i in date.split('-')])
            x = date.split('/')
            ql_date = Date(int(x[2]), int(x[1]), int(x[0]))
            next_trading_day = cal.advance(
                ql_date, Period('1D')).ISO().split('-')
            next_trading_day = ql_date.ISO().split('-')
            next_trading_day = '/'.join([x.lstrip('0')
                                         for x in next_trading_day])
            self.portfolios[key].now_time = next_trading_day
            self.portfolios[key].portfolio_update_t1()

            portfolio_utils.to_excel(self.portfolios[key])
            portfolio_utils.to_json(self.portfolios[key])
            self.portfolios[key].log()

        QtWidgets.QMessageBox().about(self, '', '更新完成')

    def updateTransfer(self):
        cal = China(China.IB)
        for key in self.portfolios:
            date = self.portfolios[key].now_time
            if isinstance(date, datetime.datetime):
                date = date.date().isoformat()
                date = '/'.join([i.lstrip('0') for i in date.split('-')])
            x = date.split('/')
            ql_date = Date(int(x[2]), int(x[1]), int(x[0]))
            next_trading_day = cal.advance(
                ql_date, Period('1D')).ISO().split('-')
            next_trading_day = '/'.join([x.lstrip('0')
                                         for x in next_trading_day])
            self.portfolios[key].now_time = next_trading_day
            self.portfolios[key].portfolio_update_transfer()

            portfolio_utils.to_excel(self.portfolios[key])
            portfolio_utils.to_json(self.portfolios[key])
            self.portfolios[key].log()

        QtWidgets.QMessageBox().about(self, '', '更新完成')
