from dataclasses import dataclass


@dataclass
class Trade:
    '''
    记录一笔交易的基本信息
    '''
    bond_code: str = ''
    amount: float = 0
    par_amount: float = 10
    volume: int = 10

    trade_time: str = '2021-07-01'
    settlement_date: str = '2021-07-01'
    direction: str = '买入'

    is_inside_trade: bool = False
