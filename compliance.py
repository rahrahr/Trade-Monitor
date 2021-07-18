from PyQt5 import QtWidgets
from trade import Trade
import re
import xlwings as xw
import pandas as pd

compliance_xlsx_path = '固收投资管理系统_0717.xlsx'
compliance_sheet = xw.Book(compliance_xlsx_path).sheets[0]


def _export_info(mainwindow):
    sheet = compliance_sheet
    # clearing previous info
    df = sheet.range('B4:E12').options(pd.DataFrame).value
    df.iloc[:, [0, 2]] = None
    df.columns = [None, '交易方向', None]
    sheet.range('B4').value = df

    # write new info
    sheet.range('C4:C12').value = [mainwindow.code.text(),
                                   mainwindow.face_value.text(),
                                   mainwindow.clean_price.text(),
                                   mainwindow.ytm.text(),
                                   mainwindow.full_price.text(),
                                   mainwindow.settlement_method.currentText(),
                                   mainwindow.zhongzhai_clean_price.text(),
                                   mainwindow.qingsuansuo_clean_price.text(),
                                   mainwindow.zhongzheng_clean_price.text()]

    sheet.range('E4:E8').value = [mainwindow.trade_direction.currentText(),
                                  mainwindow.settlement_days.currentText(),
                                  mainwindow.settlement_date.text(),
                                  mainwindow.accrued_interest.text(),
                                  mainwindow.settlement_amount.text()]

    sheet.range('E10:E12').value = [
        mainwindow.zhongzhai_clean_price_deviation_pct.text(),
        mainwindow.qingsuansuo_clean_price_deviation_pct.text(),
        mainwindow.zhongzheng_clean_price_deviation_pct.text()]

    mainwindow.settlement_amount_capitalized.setText(
        str(sheet.range('E9').value))


def _export_trader_info(mainwindow):
    sheet = compliance_sheet
    current_value = sheet.range('B2:E2').value

    # write new info
    current_value[0] = mainwindow.trader_ui.list_type.currentText()
    current_value[1] = mainwindow.trader_ui.account_list.currentText()
    current_value[2] = mainwindow.counterparty_ui.counterparty_type.currentText()
    current_value[3] = mainwindow.counterparty_ui.counterparty_list.currentText()

    sheet.range('B2:E2').value = current_value


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


def check_order() -> bool:
    return compliance_sheet.range('G3').value == '交易完成'
