import json
from PyQt5 import QtWidgets, uic
import traceback
import sys
sys.path.append("..")
from utils import *

class TraderUi(QtWidgets.QMdiSubWindow):
    def __init__(self):
        super(TraderUi, self).__init__()
        uic.loadUi("ui/trader.ui", self)
        accounts = json.load(open('trader.json', encoding='utf-8'))
        self.list_type.clear()
        self.list_type.addItems(accounts.keys())
        self.list_type.currentTextChanged.connect(self.on_list_type_change)

        self.account_list.clear()
        key = self.list_type.currentText()
        value = accounts[key].keys()
        self.account_list.addItems(value)

    def on_list_type_change(self):
        self.account_list.clear()
        key = self.list_type.text()
        value = json.load(open('trader.json', encoding='utf-8'))[key].keys()
        self.account_list.addItems(value)
