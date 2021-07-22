from dataclasses import dataclass
from trade import *
import pandas as pd


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

    @property
    def waiting_trade(self):
        # return all unsetlled T+1 trades
        return self.all_trade[self.all_trade.settlement_date > self.now_time]

    @property
    def waiting_settlement(self):
        # return all unsetlled trades that is settled today
        return self.all_trade[~self.all_trade.is_settled]

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
        # 更新现券交易的银行间T+0交易
        # 更新现券交易的交易所T+1交易时的T+0的现券转移部分，资金转移放在T+1函数内结算
        # 更新转托管T+0的记减 - 转出账户
        # 对于单个账户只会存在t+0的一笔交易
        self.now_time = trade.trade_time
        if trade.direction == "买入":
            self.cash = self.cash - \
                trade.amount if trade.bond_code[-2:] == "IB" else self.cash
            self.bonds_add(trade)
        elif trade.direction == "卖出":
            self.cash = self.cash + \
                trade.amount if trade.bond_code[-2:] == "IB" else self.cash
            self.bonds_minus(trade)
        elif trade.direction == "转托管":
            self.bonds_minus(trade)

    def portfolio_update_t1(self):
        # 更新现券交易的银行间T+1交易
        # 更新现券交易的交易所T+1交易
        # 当交易参数中：是今天的最后一笔交易时，才执行该函数
        # 找到所有挂起交易中今天可以结算的交易
        trades = self.all_trade[(self.all_trade.settlement_date == self.now_time) &
                                ((self.all_trade.direction == "买入") | (self.all_trade.direction == "卖出"))]
        if trades.shape[0] == 0:
            return
        for i in trades.index:
            each_trade = trades.loc[i, :]
            print(each_trade)
            if each_trade.direction == "买入":
                if self.cash >= each_trade.amount:  # 符合条件，扣减资金，不更新交易
                    self.cash -= each_trade.amount
                    if each_trade.bond_code[-2:] == "IB":
                        self.bonds_add(each_trade)
                else:  # 不符合条件，资金不变，冲销交易
                    if each_trade.bond_code[-2:] != "IB":
                        self.bonds_minus(each_trade)
            elif each_trade.direction == "卖出":
                # 作为卖方，默认对方不会违约
                self.cash += each_trade.amount
                if each_trade.bond_code[-2:] == "IB":
                    self.bonds_minus(each_trade)

    def portfolio_update_transfer(self):
        # 更新转托管的T+1或T+2的记加 - 转入账户
        trades = self.all_trade[(self.all_trade.settlement_date == self.now_time) & (
            self.all_trade.direction == "转托管")]
        if trades.shape[0] == 0:
            return
        for i in trades.index:
            each_trade = trades.loc[i, :]
            each_trade.bond_code = each_trade.in_bond_code
            self.bonds_add(each_trade)
