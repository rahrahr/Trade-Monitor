from dataclasses import dataclass
from trade import *
import pandas as pd
import numpy as np
from utils import portfolio_utils


@dataclass
class Portfolio:
    # 记录投资组合
    def __init__(self,
                 account: str,
                 now_time: str,
                 cash: float,
                 bonds: pd.DataFrame):

        self.account = account
        self.now_time = now_time
        self.cash = cash
        self.freeze_cash = 0
        self.bonds = bonds
        self.all_trade = pd.DataFrame(None,
                                      columns=['bond_code', 'settlement_date',
                                               'direction', 'amount',
                                               'volume', 'par_amount', 'in_bond_code', 'is_settled'])
        self.failed_trade = pd.DataFrame(None,
                                         columns=['bond_code', 'settlement_date',
                                                  'direction', 'amount',
                                                  'volume', 'par_amount', 'in_bond_code', 'is_settled'])

    @property
    def waiting_trade(self):
        # 保存所有当日不进行结算的交易
        return self.all_trade[self.all_trade.settlement_date > self.now_time]

    @property
    def waiting_settlement(self):
        # 保存所有当日进行结算的交易
        return self.all_trade[(self.all_trade.settlement_date == self.now_time) & (~self.all_trade.is_settled)]

    @property
    def free_cash(self):
        return self.cash - self.freeze_cash

    def append_waiting_trade(self, trade: Trade):
        x = pd.DataFrame([[trade.bond_code, trade.settlement_date,
                           trade.direction, trade.amount,
                           trade.volume, trade.par_amount, trade.is_settled]],
                         columns=['bond_code', 'settlement_date',
                                  'direction', 'amount',
                                  'volume', 'par_amount', 'is_settled'],
                         index=[trade.id])

        if hasattr(trade, 'in_bond_code'):
            x = pd.DataFrame([[trade.bond_code, trade.settlement_date,
                               trade.direction, trade.amount,
                               trade.volume, trade.par_amount, trade.in_bond_code,
                               trade.is_settled]],
                             columns=['bond_code', 'settlement_date',
                                      'direction', 'amount',
                                      'volume', 'par_amount', 'in_bond_code',
                                      'is_settled'],
                             index=[trade.id])
        self.all_trade = self.all_trade.append(x)
        print(self.all_trade)

    def append_failed_trade(self, trade):
        x = pd.DataFrame([[trade.bond_code, trade.settlement_date,
                           trade.direction, trade.amount,
                           trade.volume, trade.par_amount, trade.is_settled]],
                         columns=['bond_code', 'settlement_date',
                                  'direction', 'amount',
                                  'volume', 'par_amount', 'is_settled'],
                         index=[trade.name])

        if hasattr(trade, 'in_bond_code'):
            x = pd.DataFrame([[trade.bond_code, trade.settlement_date,
                               trade.direction, trade.amount,
                               trade.volume, trade.par_amount, trade.in_bond_code,
                               trade.is_settled]],
                             columns=['bond_code', 'settlement_date',
                                      'direction', 'amount',
                                      'volume', 'par_amount', 'in_bond_code',
                                      'is_settled'],
                             index=[trade.name])
        self.failed_trade = self.failed_trade.append(x)

    def bonds_add(self, trade):
        # 债券记加
        if trade.bond_code in self.bonds.bond_code.to_list():
            self.bonds.loc[self.bonds.bond_code ==
                           trade.bond_code, "volume"] += trade.volume
            self.bonds.loc[self.bonds.bond_code ==
                           trade.bond_code, "par_amount"] += trade.par_amount
            self.bonds.loc[self.bonds.bond_code ==
                           trade.bond_code, "amount"] += trade.amount
        else:
            new_bond = pd.DataFrame([[self.bonds.shape[0] + 1, trade.bond_code, trade.par_amount, trade.volume, trade.amount]],
                                    columns=["number", "bond_code", "par_amount", "volume", "amount"])
            self.bonds = pd.concat([self.bonds, new_bond])

    def bonds_minus(self, trade):
        # 债券记减
        if trade.volume < max(self.bonds.loc[self.bonds.bond_code == trade.bond_code, "volume"].iloc[0], 1):
            self.bonds.loc[self.bonds.bond_code ==
                           trade.bond_code, "volume"] -= trade.volume
            self.bonds.loc[self.bonds.bond_code ==
                           trade.bond_code, "par_amount"] -= trade.par_amount
            self.bonds.loc[self.bonds.bond_code ==
                           trade.bond_code, "amount"] -= trade.amount
        else:
            self.bonds = self.bonds[self.bonds.bond_code != trade.bond_code]
            self.bonds.number = list(range(1, self.bonds.shape[0] + 1))

    def portfolio_update_t0(self, trade: Trade):
        # 更新现券交易的交易所T+1交易时的T+0的现券转移部分，资金转移放在T+1函数内结算
        # 买入 - 冻结资金增加； 卖出 - 冻结资金不变
        self.now_time = trade.trade_time
        if trade.bond_code[-2:] == "IB" or trade.direction == "转托管":
            return
        if trade.direction == "买入":
            self.freeze_cash += trade.amount
            self.bonds_add(trade)
        elif trade.direction == "卖出":
            self.bonds_minus(trade)

    def portfolio_update_t1(self):
        # 现券交易 - 交易所T+1 - 结算
        # Assumption: 一定结算成功
        trades = self.waiting_settlement[(self.waiting_settlement.bond_code.map(lambda x:x[-2:]) != "IB") &
                                         ((self.waiting_settlement.direction == "买入") | (self.waiting_settlement.direction == "卖出"))]
        if trades.shape[0] == 0:
            return
        for i in trades.index:
            each_trade = trades.loc[i, :]
            if each_trade.direction == "买入":
                self.cash -= each_trade.amount
                self.freeze_cash -= each_trade.amount
            elif each_trade.direction == "卖出":
                self.cash += each_trade.amount
            self.all_trade.loc[i, "is_settled"] = True

    def transfer_amount_adjust(self, trade):
        # 根据目前尚存的债券数量，对执行的转托管进行调整
        temp_ = self.bonds.loc[self.bonds.bond_code == trade.bond_code,
                               "par_amount"].iloc[0] if trade.bond_code in self.bonds.bond_code.to_list() else 0
        trade.par_amount = min(trade.par_amount, temp_)
        trade.volume = trade.par_amount / 100
        trade.amount = min(trade.amount, temp_ * trade.amount/trade.par_amount)

        self.all_trade.loc[(self.all_trade.index == trade.name) & (
            self.all_trade.direction == "转托管"), "par_amount"] = trade.par_amount
        self.all_trade.loc[(self.all_trade.index == trade.name) & (
            self.all_trade.direction == "转托管"), "volume"] = trade.volume
        self.all_trade.loc[(self.all_trade.index == trade.name) & (
            self.all_trade.direction == "转托管"), "amount"] = trade.amount
        self.all_trade.loc[(self.all_trade.index == trade.name) & (
            self.all_trade.direction == "转托管-转入"), "par_amount"] = trade.par_amount
        self.all_trade.loc[(self.all_trade.index == trade.name) & (
            self.all_trade.direction == "转托管-转入"), "volume"] = trade.volume
        self.all_trade.loc[(self.all_trade.index == trade.name) & (
            self.all_trade.direction == "转托管-转入"), "amount"] = trade.amount
        return trade

    def portfolio_update_transfer(self, direction="out", other_portfolios=[]):
        # 更新转托管的T+0的记减 - 转出账户
        if direction == "out":
            trades = self.waiting_settlement[self.waiting_settlement.direction == "转托管"]
            if trades.shape[0] == 0:
                return
            for i in trades.index:
                each_trade = trades.loc[i, :]
                each_trade = self.transfer_amount_adjust(
                    each_trade)  # 对转托管的量进行调整
                if each_trade.par_amount > 0:  # 只有当账户内还存在对应债券时，才会进行转托管
                    self.bonds_minus(each_trade)
                    self.all_trade.loc[(self.all_trade.index == i) & (
                        self.all_trade.direction == "转托管"), "is_settled"] = True
        # 更新转托管的T+1或T+2的记加 - 转入账户
        elif direction == "in":
            trades = self.waiting_settlement[self.waiting_settlement.direction == "转托管-转入"]
            if trades.shape[0] == 0:
                return
            for i in trades.index:
                for other_portfolio in other_portfolios:
                    reflective_trades = portfolio_utils.find_reflective_trades(
                        self, other_portfolio)
                    print(reflective_trades)
                    if reflective_trades[i]:
                        each_trade = trades.loc[i, :]
                        self.bonds_add(each_trade)
                        self.all_trade.loc[(self.all_trade.index == i) & (
                            self.all_trade.direction == "转托管-转入"), "is_settled"] = True

    def get_NIB_(self, code_trade):
        # 银行间交易单代码结算逻辑
        # 判断能否全部结算
        code = code_trade["bond_code"].iloc[0]
        sell_trade = code_trade.loc[code_trade.direction == "卖出"]
        buy_trade = code_trade.loc[code_trade.direction == "买入"]

        net_sell_bond = sell_trade["par_amount"].sum() - buy_trade["par_amount"].sum()
        net_cost_cash = buy_trade["amount"].sum() - sell_trade["amount"].sum()

        try:
            max_sell_bond = self.bonds.loc[self.bonds.bond_code == code, "par_amount"].iloc[0]
        except:
            max_sell_bond = 0

        if net_sell_bond <= max_sell_bond and net_cost_cash <= self.cash:
            for i in code_trade.index:
                self.all_trade.loc[i, "is_settled"] = True  # 所有交易均能结算
            self.cash -= net_cost_cash
            for i in buy_trade.index: # 购买全部结算
                self.bonds_add(buy_trade.loc[i,:])
            for i in sell_trade.index: # 卖出全部结算
                self.bonds_minus(sell_trade.loc[i,:])
        # 如果不能全部结算，则将不满足条件的去除，剩余的结算
        else:
            if net_sell_bond > max_sell_bond:
                # 卖多了，则从卖出的交易中去除
                a = sell_trade["par_amount"].to_list()
                self.b = np.zeros(len(a))
                self.get_nearst(a, begin=0, M=max_sell_bond)
                for i in range(len(self.b)):
                    each_trade = sell_trade.iloc[i, :]
                    if self.b[i]:
                        self.cash += each_trade.amount
                        self.bonds_minus(each_trade)
                        self.all_trade.loc[self.all_trade.index ==
                                           each_trade.name, "is_settled"] = True
                    else:
                        if each_trade.name not in self.failed_trade.index.to_list():
                            self.append_failed_trade(each_trade)
                # 买入的交易全部执行
                for i in buy_trade.index:
                    each_trade = buy_trade.loc[i, :]
                    self.cash -= each_trade.amount
                    self.bonds_add(each_trade)
                    self.all_trade.loc[self.all_trade.index ==
                                       i, "is_settled"] = True
            elif net_cost_cash > self.cash:
                # 买多了，则从买入的交易中去除
                max_buy_cash = self.cash
                a = buy_trade["amount"].to_list()
                self.b = np.zeros(len(a))
                self.get_nearst(a, begin=0, M=max_buy_cash)
                for i in range(len(self.b)):
                    each_trade = buy_trade.iloc[i, :]
                    if self.b[i]:
                        self.cash -= each_trade.amount
                        self.bonds_add(each_trade)
                        self.all_trade.loc[self.all_trade.index ==
                                           each_trade.name, "is_settled"] = True
                    else:
                        if each_trade.name not in self.failed_trade.index.to_list():
                            self.append_failed_trade(each_trade)
                # 卖出的交易全部执行
                for i in sell_trade.index:
                    each_trade = sell_trade.loc[i, :]
                    self.cash += each_trade.amount
                    self.bonds_minus(each_trade)
                    self.all_trade.loc[self.all_trade.index ==
                                       i, "is_settled"] = True

    def settle(self):
        # 单个账户结算
        # 交易所T+1的全部结算成功
        self.portfolio_update_t1()
        # 银行间T+1和T+0的结算排序结算
        print("waiting_settlement")
        print(self.waiting_settlement)
        trades = self.waiting_settlement[(self.waiting_settlement.bond_code.map(lambda x:x[-2:]) == "IB") &
                                         ((self.waiting_settlement.direction == "买入") | (self.waiting_settlement.direction == "卖出"))]
        print("trades")
        print(trades)
        trades = trades.sort_values(by=["direction", "par_amount"], ascending=(
            False, False))  # 先卖出后买入，票面金额从大到小排序
        code_sig = trades.drop_duplicates(
            subset=["bond_code"]).bond_code.to_list()
        for code in code_sig:
            code_trade = trades.loc[trades.bond_code == code]
            self.get_NIB_(code_trade)
        # 转托管结算
        self.portfolio_update_transfer(direction="out")
        # 将现券交易的failed_trade里的False变为True
        for i in self.failed_trade.index:
            if (self.all_trade.loc[i, "direction"] == "买入" or self.all_trade.loc[i, "direction"] == "卖出") and self.all_trade.loc[i, "is_settled"]:
                self.failed_trade.loc[i, "is_settled"] = True

    def to_excel(self):
        portfolio_utils.to_excel(self)

    def to_json(self):
        portfolio_utils.to_json(self)

    def save_position(self):
        file_name = 'historic_positions/position_{}_{}.csv'.format(
            self.account, self.now_time.replace('/', ''))
        cash_row = pd.Series([0, 'cash', self.cash, 0, 0], index=["number", "bond_code",
                                                                  "par_amount", "volume",
                                                                  "amount"])
        df = self.bonds.copy()
        df.loc['cash'] = cash_row
        df.to_csv(file_name)

    def log(self):
        log_name = 'logs/log_{}_{}.csv'.format(
            self.account, self.now_time.replace('/', ''))
        self.all_trade.to_csv(log_name)

    def get_nearst(self, a, begin, M):
        # 递归函数，找到一组数中间和最接近且小于M的组合
        if begin >= len(a):
            return M
        k1 = self.get_nearst(a, begin + 1, M - a[begin])
        k2 = self.get_nearst(a, begin + 1, M)
        if k1 >= 0 and k2 >= 0:
            if k1 <= k2:
                self.b[begin] = True
                return self.get_nearst(a, begin + 1, M - a[begin])
            else:
                self.b[begin] = False
                return self.get_nearst(a, begin + 1, M)
        if k1 >= 0 and k2 < 0:
            self.b[begin] = True
            return self.get_nearst(a, begin + 1, M - a[begin])
        if k1 < 0:
            self.b[begin] = False
            return self.get_nearst(a, begin + 1, M)
