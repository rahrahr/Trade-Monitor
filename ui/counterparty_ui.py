import json
from PyQt5 import QtWidgets, uic
import traceback
import sys
sys.path.append("..")
from utils import *

class CounterpartyUi(QtWidgets.QMdiSubWindow):
    def __init__(self):
        super(CounterpartyUi, self).__init__()
        uic.loadUi("ui/counterparty.ui", self)
        counterparty = json.load(open('counterparty.json', encoding='utf-8'))
        self.counterparty_type.clear()
        self.counterparty_type.addItems(counterparty.keys())
        self.counterparty_type.currentTextChanged.connect(
            self.on_counterparty_type_change)

        self.counterparty_list.clear()
        key = self.counterparty_type.currentText()
        value = counterparty[key]
        self.counterparty_list.addItems(value)

    def on_counterparty_type_change(self):
        self.counterparty_list.clear()
        key = self.counterparty_type.currentText()
        value = json.load(open('counterparty.json', encoding='utf-8'))[key]
        self.counterparty_list.addItems(value)
