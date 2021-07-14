import xlwings as xw

calculator_path = 'project1_V4.xlsx'
calculator = xw.Book(calculator_path).sheets[0]


def get_quote(code: str, date: str) -> dict:
    # 获取前一天的中债估值等数据
    result = {'中债估值': {'净价': 100, 'YTM': 4},
              '清算所估值': {'净价': 100, 'YTM': 4},
              '中证估值': {'净价': 100, 'YTM': 4}}
    return result


def get_numbers(code: str, clean_price: str,
                settlement_date: str, settlement_days: str) -> dict:
    result = {}
    calculator.range('C3').value = code
    calculator.range('C4').value = settlement_date
    calculator.range('C5').value = clean_price
    calculator.range('C8').value = settlement_days

    result['ytm'] = calculator.range('C14').value
    result['accrued interest'] = calculator.range('C11').value
    result['full price'] = calculator.range('C12').value
    return result


def get_deviation(mainwindow, clean_price: float):
    zhongzhai_clean_price_deviation = float(clean_price) - \
        float(mainwindow.zhongzhai_clean_price.text())
    qingsuansuo_clean_price_deviation = float(clean_price) - \
        float(mainwindow.qingsuansuo_clean_price.text())
    zhongzheng_clean_price_deviation = float(clean_price) - \
        float(mainwindow.zhongzheng_clean_price.text())

    mainwindow.zhongzhai_clean_price_deviation_pct.setText(
        str(100*zhongzhai_clean_price_deviation/float(mainwindow.zhongzhai_clean_price.text())))
    mainwindow.zhongzhai_clean_price_deviation.setText(
        str(zhongzhai_clean_price_deviation))

    mainwindow.qingsuansuo_clean_price_deviation_pct.setText(
        str(100*qingsuansuo_clean_price_deviation/float(mainwindow.qingsuansuo_clean_price.text())))
    mainwindow.qingsuansuo_clean_price_deviation.setText(
        str(qingsuansuo_clean_price_deviation))

    mainwindow.zhongzheng_clean_price_deviation_pct.setText(
        str(100*zhongzheng_clean_price_deviation/float(mainwindow.zhongzheng_clean_price.text())))
    mainwindow.zhongzheng_clean_price_deviation.setText(
        str(zhongzheng_clean_price_deviation))