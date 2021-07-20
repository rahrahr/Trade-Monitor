from PyQt5 import QtWidgets
from trade import Trade
import re
import xlwings as xw
import pandas as pd
import json

_xlsx_path = json.load(
    open('settings.json'), encoding='utf-8')["Trade Monitor Path"]
spot_sheet = xw.Book(_xlsx_path).sheets['现券交易-债券要素']
transfer_sheet = xw.Book(_xlsx_path).sheets['转托管-债券要素']


def get_quote(code: str) -> dict:
    # 获取前一天的中债估值等数据
    spot_sheet.range('C4').value = code
    result = {'中债估值': {'净价': spot_sheet.range('C10').value,
                       'YTM': spot_sheet.range('C13').value},
              '清算所估值': {'净价': spot_sheet.range('C11').value,
                        'YTM': spot_sheet.range('C14').value},
              '中证估值': {'净价': spot_sheet.range('C12').value,
                       'YTM': spot_sheet.range('C15').value}}
    return result


def _export_info(mainwindow):
    sheet = spot_sheet
    # clearing previous info
    sheet.range('C2:C9').value = 0
    sheet.range('E2:E8').value = 0

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
    # Not actually settlement date
    sheet.range('C3').value = mainwindow.trade_date.text()
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
    sheet = spot_sheet
    current_value = sheet.range('B2:E2').value

    # write new info
    current_value[0] = mainwindow.trader_ui.list_type.currentText()
    current_value[1] = mainwindow.trader_ui.account_list.currentText()
    current_value[2] = mainwindow.counterparty_ui.counterparty_type.currentText()
    current_value[3] = mainwindow.counterparty_ui.counterparty_list.currentText()

    sheet.range('B2:E2').value = current_value


def _export_transfer_info(mainwindow):
    sheet = transfer_sheet
    out_account_key_1 = mainwindow.list_type.currentText()
    out_account_key_2 = mainwindow.account_list.currentText()

    in_account_key_1 = mainwindow.list_type_2.currentText()
    in_account_key_2 = mainwindow.account_list_2.currentText()

    out_code = mainwindow.code.text()
    target_exchange = mainwindow.target_exchange.text()
    transfer_start_date = mainwindow.transfer_start_date.text()
    transfer_amount = mainwindow.lineEdit.text()

    sheet.range('C2').value = out_account_key_2
    sheet.range('E2').value = in_account_key_2
    sheet.range('C4').value = out_code
    sheet.range('C6').value = target_exchange
    sheet.range('C7').value = transfer_start_date
    sheet.range('C8').value = transfer_amount

    mainwindow.in_code.setText(str(sheet.range('E6').value))
    mainwindow.transfer_finish_date.setText(str(sheet.range('E7').value))
    mainwindow.transfer_amount.setText(str(sheet.range('E8').value))
