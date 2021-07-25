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
            print(trade.trade_time, type(trade.trade_time))
        except:
            QtWidgets.QMessageBox().about(self, '错误信息', traceback.format_exc())
            return False

        # 更新Portfolio对象
        try:
            account = trade.inside_id
            self.portfolios[account].append_waiting_trade(trade)
            self.portfolios[account].portfolio_update_t0(trade)
            print(self.portfolios[account].all_trade)
            print(self.portfolios[account].now_time, type(self.portfolios[account].now_time))
            print(type(self.portfolios[account].all_trade.iloc[0, 1]))

            if trade.is_inside_trade:
                account = trade.other_inside_id
                self.portfolios[account].append_waiting_trade(
                    trade.reversed())
                self.portfolios[account].portfolio_update_t0(
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
            trade_ = deepcopy(trade)
            trade.settlement_date = trade.trade_time
        except:
            QtWidgets.QMessageBox().about(self, '错误信息', traceback.format_exc())
            return False

        # 更新Portfolio对象
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
        # 当前账户提交清算申请
        list_type = self.trader_ui.list_type.currentText()
        trader_id = self.trader_ui.account_list.currentText()
        key = list_type + trader_id

        self.portfolios[key].settle()
        QtWidgets.QMessageBox().about(self, '', '结算报单完成')

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
                msg = ['{}-{}现券持仓不足'.format(key, i) for i in x]
                prompt_msg.extend(msg)
            # display current positions
            df_ = displayDataFrame(temp_portfolio.bonds, key, self)
            mainlayout.addWidget(df_)

        msg = QtWidgets.QMessageBox()
        text = "若不进行转托管操作，账户持仓如下，请选择是否进行接下去的操作"
        msg.setText(text)
        msg.setWindowTitle("请选择")
        msg.setStandardButtons(
            QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Yes)
        mainlayout.addWidget(msg)
        popup.resize(600, 600)
        popup.show()
        retval = msg.exec_()
        popup.close()
        return prompt_msg, retval

    def updateTplus1(self):
        # 更新明天到账的T+1交易，调用后now_time会+1
        # 首先检查是否存在需要弥补交易
        prompt_msg, retval = self.checkSufficiency()
        if retval == QtWidgets.QMessageBox.No:
            # 中止本函数运行
            return

        if prompt_msg:
            msg = QtWidgets.QMessageBox()
            text = "更新持仓中止，以下现券不足，请选择是否进行自动内部转托管\n" + '\n'.join(prompt_msg)
            msg.setText(text)
            msg.setWindowTitle("持仓不足警示")
            msg.setStandardButtons(
                QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Yes)
            retval = msg.exec_()

            # 若选择Yes，则进入此分支，进行自动转托管
            if retval == QtWidgets.QMessageBox.Yes:
                self.autoTransfer()
                QtWidgets.QMessageBox().about(self, '提示信息', '自动转托管完成，请再次点击“完成今日交易”按钮')
                return
            # 若不选择，则继续更新T+1持仓

        # 更新T+1
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

            self.portfolios[key].to_excel()
            self.portfolios[key].to_json()
            self.portfolios[key].log()

        QtWidgets.QMessageBox().about(self, '', '更新完成')

    def updateTransfer(self):
        # 更新明天到账的转托管交易，调用后now_time会+1
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
            self.portfolios[key].portfolio_update_transfer()

            self.portfolios[key].to_excel()
            self.portfolios[key].to_json()
            self.portfolios[key].log()

        QtWidgets.QMessageBox().about(self, '', '更新完成')

    def autoTransfer(self):
        # 判断各内部账户中是否存在互补，并进行提示
        # 转托管仍需要手动输入
        temp_portfolios = {}
        for key in self.portfolios:
            temp_portfolios[key] = deepcopy(self.portfolios[key])
            temp_portfolios[key].settle()
            bonds_not_enough = temp_portfolios[key].bonds[temp_portfolios.bonds['par_amount'] < 0]


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
