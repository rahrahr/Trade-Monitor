from PyQt5 import QtWidgets
from trade import Trade
import re
import xlwings as xw
import pandas as pd
import json

compliance_xlsx_path = json.load(
    open('settings.json'), encoding='utf-8')["Trade Monitor Path"]
compliance_sheet = xw.Book(compliance_xlsx_path).sheets[0]


def get_quote(code: str) -> dict:
    # 获取前一天的中债估值等数据
    compliance_sheet.range('C4').value = code
    result = {'中债估值': {'净价': compliance_sheet.range('C10').value,
                       'YTM': compliance_sheet.range('C13').value},
              '清算所估值': {'净价': compliance_sheet.range('C11').value,
                        'YTM': compliance_sheet.range('C14').value},
              '中证估值': {'净价': compliance_sheet.range('C12').value,
                       'YTM': compliance_sheet.range('C15').value}}
    return result


def _export_info(mainwindow):
    sheet = compliance_sheet
    # clearing previous info
    df = sheet.range('B4:E12').options(pd.DataFrame).value
    df.iloc[:, [0, 2]] = None
    sheet.range('B4').value = df
    sheet.range('D4').value = '交易方向'

    # write new info
    sheet.range('C4').value = mainwindow.code.text()
    sheet.range('C5').value = mainwindow.face_value.text()
    sheet.range('C6').value = mainwindow.clean_price.text()
    sheet.range('C7').value = mainwindow.ytm.text()
    sheet.range('C8').value = mainwindow.full_price.text()
    sheet.range('C9').value = mainwindow.settlement_method.currentText()
    sheet.range('C10').value = mainwindow.zhongzhai_clean_price.text()
    sheet.range('C11').value = mainwindow.qingsuansuo_clean_price.text()
    sheet.range('C12').value = mainwindow.zhongzheng_clean_price.text()

    sheet.range('E4').value = mainwindow.trade_direction.currentText()
    sheet.range('E5').value = mainwindow.settlement_days.currentText()
    sheet.range('C3').value = mainwindow.settlement_date.currentText() # Not actually settlement date
    sheet.range('E7').value = mainwindow.accrued_interest.text()
    sheet.range('E8').value = mainwindow.settlement_amount.text()
    sheet.range(
        'E10').value = mainwindow.zhongzhai_clean_price_deviation_pct.text()
    sheet.range(
        'E11').value = mainwindow.qingsuansuo_clean_price_deviation_pct.text()
    sheet.range(
        'E12').value = mainwindow.zhongzheng_clean_price_deviation_pct.text()
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


def check_order() -> bool:
    return compliance_sheet.range('G3').value == '交易完成'
