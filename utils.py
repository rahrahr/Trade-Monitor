def get_quote(code: str, date: str) -> dict:
    # 获取前一天的中债估值等数据
    result = {'中债估值': {'净价': 100, 'YTM': 4},
              '清算所估值': {'净价': 100, 'YTM': 4},
              '中证估值': {'净价': 100, 'YTM': 4}}
    return result
