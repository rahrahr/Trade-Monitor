from dataclasses import dataclass
from itertools import count

@dataclass
class Trade:
    '''
    记录一笔交易的基本信息
    '''
    id = count()
    def __init__(self,
                 bond_code: str = '',
                 amount: float = 0,
                 par_amount: float = 10,
                 volume: int = 10,
                 trade_time: str = '2021-07-01',
                 settlement_date: str = '2021-07-01',
                 settlement_days: str = '2021-07-01',
                 direction: str = '买入',
                 is_inside_trade: bool = False,
                 inside_id: str = '',
                 other_inside_id: str = ''):

        self.id = next(Trade.id)
        self.bond_code: str = bond_code
        self.amount: float = amount
        self.par_amount: float = par_amount
        self.volume: int = volume

        self.trade_time: str = trade_time
        self.settlement_date: str = settlement_date
        self.settlement_days: str = settlement_days
        self.is_settled: bool = False
        self.direction: str = direction

        self.is_inside_trade: bool = is_inside_trade
        self.inside_id: str = inside_id
        if is_inside_trade:
            self.other_inside_id = other_inside_id

    def reversed(self):
        if hasattr(self, 'in_bond_code'):
            #转托管
            reversed_direction = '转托管-转入'
            trade = Trade(self.in_bond_code, self.amount,
                          self.par_amount, self.volume,
                          self.trade_time, self.settlement_date,
                          self.settlement_days, reversed_direction,
                          self.is_inside_trade, self.other_inside_id,
                          self.inside_id)
            trade.in_bond_code = self.bond_code
            trade.id = self.id
            return trade
            
        reversed_direction = "卖出" if self.direction == "买入" else "买入"
        return Trade(self.bond_code, self.amount,
                     self.par_amount, self.volume,
                     self.trade_time, self.settlement_date,
                     self.settlement_days, reversed_direction,
                     self.is_inside_trade, self.other_inside_id,
                     self.inside_id)
