from PyQt5 import QtWidgets
from trade import Trade
import re

def sanity_check_all(mainwindow, bond_code, sell_code, buy_clean_price, sell_clean_price) -> None:
    flag1 = re.match(r'^\d{6,}\.(IB|SZ|SH)$', bond_code) is not None
    flag2 = buy_clean_price.replace('.', '', 1).isdigit()
    flag3 = sell_clean_price.replace('.', '', 1).isdigit()
    flag4 = re.match(r'^\d{6,}\.(IB|SZ|SH)$', sell_code) is not None
    flags = (flag1, flag2, flag3, flag4)

    if not all(flags):
        error_messages = ('债券代码格式错误\n',
                          '买入净价不为浮点数\n',
                          '卖出净价不为浮点数\n',
                          '卖出代码格式错误')
        error_string = ''.join(
            (error_messages[i] for i in range(len(error_messages)) if not flags[i]))
        QtWidgets.QMessageBox().about(mainwindow, '错误信息', error_string)
        return False
    return True

def check_order(trade: Trade) -> bool:
    return True