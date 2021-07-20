import json
import re
from PyQt5 import QtWidgets, uic
import traceback
import sys
sys.path.append("..")
from utils import *

class BondInfoUi(QtWidgets.QMdiSubWindow):
    def __init__(self):
        super(BondInfoUi, self).__init__()
        uic.loadUi("ui/bond_info.ui", self)
        self.get_info.clicked.connect(self.getInfo)
        self.start_calculation.clicked.connect(self.calculate)

    def getInfo(self):
        code = self.code.text()
        clean_price = self.clean_price.text()
        # 如果不输入净价，则把净价当100
        clean_price = float(clean_price) if clean_price else 100
        trade_date = self.trade_date.text()
        if re.match(r'^\d{6,}\.(IB|SZ|SH)$', code) is None:
            QtWidgets.QMessageBox().about(self, '错误信息', '债券代码格式错误')
            return False

        try:
            quote = excel_utils.get_quote(code, trade_date)
            self.zhongzhai_clean_price.setText(
                '{:.4f}'.format(quote['中债估值']['净价']))
            self.zhongzhai_ytm.setText(
                '{:.4f}'.format(quote['中债估值']['YTM']))

            self.qingsuansuo_clean_price.setText(
                '{:.4f}'.format(quote['清算所估值']['净价']))
            self.qingsuansuo_ytm.setText(
                '{:.4f}'.format(quote['清算所估值']['YTM']))

            self.zhongzheng_clean_price.setText(
                '{:.4f}'.format(quote['中证估值']['净价']))
            self.zhongzheng_ytm.setText('{:.4f}'.format(quote['中证估值']['YTM']))
        except:
            QtWidgets.QMessageBox().about(self, '错误信息', '获取估值失败')
            return False

        utils.set_deviation(self, clean_price)
        self._export_info()

    def _export_info(self):
        excel_utils._export_info(self)

    def calculate(self):
        self.getInfo()
        code = self.code.text()
        face_value = self.face_value.text() if self.face_value.text() else '0'
        if not face_value.replace('.', '', 1).isdigit():
            QtWidgets.QMessageBox().about(self, '错误信息', '券面金额错误')
            return False
        clean_price = self.clean_price.text()
        if not clean_price.replace('.', '', 1).isdigit():
            QtWidgets.QMessageBox().about(self, '错误信息', '净价错误')
            return False
        settlement_date = self.trade_date.text()
        settlement_days = self.settlement_days.currentText()

        # 计算到期收益率、应计利息、全价
        try:
            numbers = utils.get_numbers(
                code, clean_price, settlement_date, settlement_days)
            self.full_price.setText('{:.4f}'.format(
                numbers['full price'] if numbers['full price'] else 0))
            self.ytm.setText('{:.4f}'.format(
                100 * numbers['ytm'] if numbers['ytm'] else 0))
            self.accrued_interest.setText('{:.4f}'.format(
                numbers['accrued interest'] if numbers['accrued interest'] else 0))
            self.settlement_amount.setText('{:.4f}'.format(
                numbers['full price'] * 100 * float(self.face_value.text())))
        except:
            QtWidgets.QMessageBox().about(self, '错误信息', '计算Yield、全价时出错')
            return False
        self._export_info()
