from PyQt5 import QtWidgets
from trade import Trade
import re
import xlwings as xw
import pandas as pd

compliance_xlsx_path = '固收投资管理系统_0716.xlsx'
compliance_book = xw.Book(compliance_xlsx_path)


def _export_info(mainwindow):
    sheet = compliance_book.sheets[0]
    # clearing previous info
    df = sheet.range('A1:D9').options(pd.DataFrame).value
    df.iloc[:, [0, 2]] = None
    df.columns = [None, '交易方向', None]
    sheet.range('A1').value = df

    # write new info
    sheet.range('B1').value = mainwindow.code.text()
    sheet.range('B2').value = mainwindow.face_value.text()
    sheet.range('B3').value = mainwindow.clean_price.text()
    sheet.range('B4').value = mainwindow.ytm.text()
    sheet.range('B5').value = mainwindow.full_price.text()
    sheet.range('B6').value = mainwindow.settlement_method.currentText()
    sheet.range('B7').value = mainwindow.zhongzhai_clean_price.text()
    sheet.range('B8').value = mainwindow.qingsuansuo_clean_price.text()
    sheet.range('B9').value = mainwindow.zhongzheng_clean_price.text()

    sheet.range('D1').value = mainwindow.trade_direction.currentText()
    sheet.range('D2').value = mainwindow.settlement_days.currentText()
    sheet.range('D3').value = mainwindow.settlement_date.text()
    sheet.range('D4').value = mainwindow.accrued_interest.text()
    sheet.range('D5').value = mainwindow.settlement_amount.text()
    sheet.range(
        'D7').value = mainwindow.zhongzhai_clean_price_deviation_pct.text()
    sheet.range(
        'D8').value = mainwindow.qingsuansuo_clean_price_deviation_pct.text()
    sheet.range(
        'D9').value = mainwindow.zhongzheng_clean_price_deviation_pct.text()
    mainwindow.settlement_amount_capitalized.setText(
        str(sheet.range('D6').value))


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
