import datetime
import json
import re
from copy import deepcopy
from PyQt5 import QtWidgets, uic, QtCore, QtGui
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
        self.bond_info_ui.save_log.clicked.connect(self.saveLog)
        self.bond_info_ui.parent = self

        self.transfer_ui.send_order.clicked.connect(self.sendTransferOrder)
        self.transfer_ui.is_last_trade.clicked.connect(self.updateTransfer)

        self.trader_ui.now_time_button.clicked.connect(self.changeNowtime)
        self.trader_ui.check_info.clicked.connect(self.checkTraderInfo)

        # create Portfolio instances for all accounts.
        self.portfolios = {}
        self.bond_info_ui.initial_portfolios = {}
        portflios = json.load(open('trader.json', encoding='utf-8'))
        for key_1 in portflios.keys():
            for key_2, item_2 in portflios[key_1].items():
                account = key_1 + key_2
                self.portfolios[key_1 + key_2] =\
                    portfolio_utils.create_portfolio(account)
                # Makes it easier to update json file
                self.portfolios[key_1 + key_2].key_1 = key_1
                self.portfolios[key_1 + key_2].key_2 = key_2

                self.bond_info_ui.initial_portfolios[key_1 + key_2] =\
                    portfolio_utils.create_portfolio(account)
                x = self.bond_info_ui.initial_portfolios[key_1 + key_2].bonds
                self.bond_info_ui.initial_portfolios[key_1 + key_2].init = True
                self.bond_info_ui.initial_portfolios[key_1 +
                                                     key_2].initial_value = x
                self.bond_info_ui.initial_portfolios[key_1 +
                                                     key_2].key_1 = key_1
                self.bond_info_ui.initial_portfolios[key_1 +
                                                     key_2].key_2 = key_2

    def getPosition(self):
        trader_position = json.load(open('trader.json', encoding='utf-8'))[
            self.trader_ui.list_type.currentText()]

        trader_id = self.trader_ui.account_list.currentText()
        code = self.bond_info_ui.code.text()

        bond_position = trader_position[trader_id]['position'].get(code, 0)
        cash_position = trader_position[trader_id]['cash']

        self.bond_info_ui.bond_position.setText(str(bond_position))
        self.bond_info_ui.cash_position.setText(str(cash_position))

    def changeNowtime(self):
        list_type = self.trader_ui.list_type.currentText()
        trader_id = self.trader_ui.account_list.currentText()
        key = list_type + trader_id

        date = self.trader_ui.now_time.text()
        self.portfolios[key].now_time = date
        QtWidgets.QMessageBox().about(self, '??????', '????????????????????????"{}"'.format(date))

    def checkTraderInfo(self):
        list_type = self.trader_ui.list_type.currentText()
        trader_id = self.trader_ui.account_list.currentText()
        key = list_type + trader_id
        portfolio = self.portfolios[key]

        popup = QtWidgets.QMainWindow(parent=self)
        mainlayout = QtWidgets.QVBoxLayout()
        widget = QtWidgets.QWidget()
        widget.setLayout(mainlayout)
        popup.setCentralWidget(widget)

        trader_info = '''
        ????????????:{}
        ????????????:{}
        ????????????:{}
        ????????????:{}
        '''.format(portfolio.account, portfolio.now_time, portfolio.cash, portfolio.free_cash)
        msg = QtWidgets.QTextBrowser()
        msg.setText(trader_info)
        mainlayout.addWidget(msg)

        df_ = displayDataFrame(portfolio.bonds, key, self)
        mainlayout.addWidget(df_)

        df_2 = displayDataFrame(portfolio.all_trade, key, self)
        mainlayout.addWidget(df_)

        msg_2 = QtWidgets.QMessageBox()
        msg_2.setStandardButtons(QtWidgets.QMessageBox.Ok)
        mainlayout.addWidget(msg_2)
        popup.resize(600, 600)
        popup.show()
        msg_2.exec_()
        popup.close()

    def _export_trader_info(self):
        excel_utils._export_trader_info(self)

    def sendOrder(self):
        self.bond_info_ui._export_info()
        self._export_trader_info()
        x = compliance.check_spot_order()
        if ('??????' in x) or ('?????????' in x) or ('?????????' in x):
            error_message = '??????????????????????????????\n'+'!\n'.join(x.split('???'))
            QtWidgets.QMessageBox().about(self, '????????????', error_message)
            return False

        elif '??????' in x:
            error_message = '???????????????\n'+'!\n'.join(x.split('???'))
            QtWidgets.QMessageBox().about(self, '??????', error_message)

        try:
            trade = trade_utils.create_spot_trade()
            print(trade.trade_time, type(trade.trade_time))
            print(trade.settlement_date, type(trade.settlement_date))

        except:
            QtWidgets.QMessageBox().about(self, '????????????', traceback.format_exc())
            return False

        # ??????Portfolio??????
        try:
            account = trade.inside_id
            self.portfolios[account].append_waiting_trade(trade)
            self.portfolios[account].portfolio_update_t0(trade)
            print(self.portfolios[account].all_trade)
            print(self.portfolios[account].now_time)
            # print(self.portfolios[account].now_time, type(self.portfolios[account].now_time))
            # print(type(self.portfolios[account].all_trade.iloc[0, 1]))

            if trade.is_inside_trade:
                account = trade.other_inside_id
                self.portfolios[account].append_waiting_trade(
                    trade.reversed())
                self.portfolios[account].portfolio_update_t0(
                    trade.reversed())

        except:
            QtWidgets.QMessageBox().about(
                self, '????????????', traceback.format_exc())
            return False

        # ??????Excel???json??????
        if not trade.is_inside_trade:
            self.portfolios[trade.inside_id].to_excel()
            self.portfolios[trade.inside_id].to_json()
        else:
            self.portfolios[trade.inside_id].to_excel()
            self.portfolios[trade.other_inside_id].to_excel()

            self.portfolios[trade.inside_id].to_json()
            portfolio_utils.to_json(self.portfolios[trade.other_inside_id])

        QtWidgets.QMessageBox().about(self, '', '????????????')

    def sendTransferOrder(self):
        # self.transfer_ui._export_transfer_info()
        x = compliance.check_transfer_order()
        if x != '????????????':
            error_message = '???????????????????????????????????????\n'+'!\n'.join(x.split('???'))
            QtWidgets.QMessageBox().about(self, '????????????', error_message)
            return False

        try:
            trade = trade_utils.create_transfer_trade()
            trade_ = deepcopy(trade)
            print(trade.settlement_date)
            trade.settlement_date = trade.trade_time
            print(trade_.settlement_date)
        except:
            QtWidgets.QMessageBox().about(self, '????????????', traceback.format_exc())
            return False

        # ??????Portfolio??????
        try:
            trade.settlement_days == 'T+1'
            account = trade.inside_id
            self.portfolios[account].append_waiting_trade(trade)
            self.portfolios[account].portfolio_update_t0(trade)

            account = trade.other_inside_id
            self.portfolios[account].append_waiting_trade(
                trade_.reversed())
            self.portfolios[account].portfolio_update_t0(trade_.reversed())

        except:
            QtWidgets.QMessageBox().about(
                self, '????????????', traceback.format_exc())
            return False

        # ??????Excel???json??????
        if not trade.is_inside_trade:
            portfolio_utils.to_excel(self.portfolios[trade.inside_id])
            portfolio_utils.to_json(self.portfolios[trade.inside_id])
        else:
            portfolio_utils.to_excel(self.portfolios[trade.inside_id])
            portfolio_utils.to_excel(self.portfolios[trade.other_inside_id])

            portfolio_utils.to_json(self.portfolios[trade.inside_id])
            portfolio_utils.to_json(self.portfolios[trade.other_inside_id])

        QtWidgets.QMessageBox().about(self, '', '????????????')

    def sendSettlement(self):
        # ??????????????????????????????
        list_type = self.trader_ui.list_type.currentText()
        trader_id = self.trader_ui.account_list.currentText()
        key = list_type + trader_id

        self.portfolios[key].settle()
        self.portfolios[key].to_json()
        self.portfolios[key].to_excel()

        self.hintFailures()

    def checkSufficiency(self):
        prompt_msg = []
        popup = QtWidgets.QMainWindow(parent=self)
        mainlayout = QtWidgets.QVBoxLayout()
        widget = QtWidgets.QWidget()
        widget.setLayout(mainlayout)
        popup.setCentralWidget(widget)

        for key in self.portfolios:
            temp_portfolio = deepcopy(self.portfolios[key])
            temp_portfolio.settle()
            bonds_not_enough = temp_portfolio.bonds[temp_portfolio.bonds['par_amount'] < 0]
            if not bonds_not_enough.empty:
                x = bonds_not_enough['bond_code'].to_list()
                msg = ['{}-{}??????????????????'.format(key, i) for i in x]
                prompt_msg.extend(msg)
            # display current positions
            df_ = displayDataFrame(temp_portfolio.bonds, key, self)
            mainlayout.addWidget(df_)

        msg = QtWidgets.QMessageBox()
        text = "??????????????????????????????????????????????????????????????????????????????????????????"
        msg.setText(text)
        msg.setWindowTitle("?????????")
        msg.setStandardButtons(
            QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Yes)
        mainlayout.addWidget(msg)
        popup.resize(600, 600)
        popup.show()
        retval = msg.exec_()
        popup.close()
        return prompt_msg, retval

    def updateTplus1(self):
        # ?????????????????????T+1??????????????????now_time???+1
        # ??????????????????????????????????????????
        prompt_msg, retval = self.checkSufficiency()
        if retval == QtWidgets.QMessageBox.No:
            # ?????????????????????
            return

        if prompt_msg:
            msg = QtWidgets.QMessageBox()
            text = "????????????????????????????????????????????????????????????????????????????????????\n" + '\n'.join(prompt_msg)
            msg.setText(text)
            msg.setWindowTitle("??????????????????")
            msg.setStandardButtons(
                QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Yes)
            retval = msg.exec_()

            # ?????????Yes?????????????????????????????????????????????
            if retval == QtWidgets.QMessageBox.Yes:
                self.autoTransfer()
                QtWidgets.QMessageBox().about(self, '????????????', '?????????????????????????????????????????????????????????????????????')
                return
            # ??????????????????????????????T+1??????

        # ??????T+1
        cal = China(China.IB)
        for key in self.portfolios:
            date = self.portfolios[key].now_time
            if isinstance(date, datetime.datetime):
                date = date.date().isoformat().replace('-', '/')
            x = date.split('/')
            ql_date = Date(int(x[2]), int(x[1]), int(x[0]))
            next_trading_day = cal.advance(
                ql_date, Period('1D')).ISO().split('-')
            next_trading_day = ql_date.ISO().replace('-', '/')
            self.portfolios[key].now_time = next_trading_day
            self.portfolios[key].portfolio_update_t1()
            self.portfolios[key].now_time = date

            self.portfolios[key].to_excel()
            self.portfolios[key].to_json()
            self.portfolios[key].save_position()
            self.portfolios[key].log()

        QtWidgets.QMessageBox().about(self, '', '????????????')

    def updateTransfer(self):
        # ????????????????????????????????????????????????now_time???+1
        cal = China(China.IB)
        for key in self.portfolios:
            date = self.portfolios[key].now_time
            if isinstance(date, datetime.datetime):
                date = date.date().isoformat().replace('-', '/')
            x = date.split('/')
            ql_date = Date(int(x[2]), int(x[1]), int(x[0]))
            next_trading_day = cal.advance(
                ql_date, Period('1D')).ISO().replace('-', '/')
            self.portfolios[key].now_time = next_trading_day
            other_portfolios = [self.portfolios[i]
                                for i in self.portfolios if i != key]
            self.portfolios[key].portfolio_update_transfer(direction='in',
                                                           other_portfolios=other_portfolios)
            self.portfolios[key].now_time = date

            self.portfolios[key].to_excel()
            self.portfolios[key].to_json()
            self.portfolios[key].save_position()
            self.portfolios[key].log()

        QtWidgets.QMessageBox().about(self, '', '????????????')

    def autoTransfer(self):
        # ????????????????????????????????????????????????????????????
        # ??????????????????????????????
        temp_portfolios = {}
        for key in self.portfolios:
            temp_portfolios[key] = deepcopy(self.portfolios[key])
            temp_portfolios[key].settle()
            bonds_not_enough = temp_portfolios[key].bonds[temp_portfolios.bonds['par_amount'] < 0]
            temp_portfolios[key].unfilled = bonds_not_enough

    def hintFailures(self):
        popup = QtWidgets.QMainWindow(parent=self)
        mainlayout = QtWidgets.QVBoxLayout()
        widget = QtWidgets.QWidget()
        widget.setLayout(mainlayout)
        popup.setCentralWidget(widget)

        msg = QtWidgets.QMessageBox()
        msg.setText("????????????????????????????????????Trade??????Failed Trade")
        mainlayout.addWidget(msg)

        list_type = self.trader_ui.list_type.currentText()
        trader_id = self.trader_ui.account_list.currentText()
        key = list_type + trader_id
        df = self.portfolios[key].failed_trade
        df = displayDataFrame(df, key, self)

        mainlayout.addWidget(df)
        popup.resize(600, 600)
        popup.show()
        msg.exec_()
        popup.close()

    def saveLog(self):
        for x in self.portfolios.values():
            x.log()


class PandasModel(QtCore.QAbstractTableModel):

    def __init__(self, data):
        QtCore.QAbstractTableModel.__init__(self)
        self._data = data

    def rowCount(self, parent=None):
        return self._data.shape[0]

    def columnCount(self, parnet=None):
        return self._data.shape[1]

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if index.isValid():
            if role == QtCore.Qt.DisplayRole:
                return str(self._data.iloc[index.row(), index.column()])
        return None

    def headerData(self, col, orientation, role):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self._data.columns[col]
        return None


def displayDataFrame(df, title='', parent=None):
    popup = QtWidgets.QMainWindow(parent=parent)
    popup.setWindowTitle(title)
    popup.view = QtWidgets.QTableView()
    model = PandasModel(df)
    popup.view.setModel(model)
    popup.view.resize(800, 400)
    popup.setCentralWidget(popup.view)
    return popup
