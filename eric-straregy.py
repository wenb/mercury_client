#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
@author: wenbin
@filename: eric-straregy.py
@created date: 2016/11/16 17:11
@last modified: 2016/11/16 17:11
"""

import numpy as np

# 第一步：设置基本参数
start = '2016-08-01'
end = '2016-11-11'
benchmark = 'HS300'
capital_base = 2000000
freq = 'd'
refresh_rate = 3

# 第二步：选择因子(分析师评级、速动比率)，设置股票池
universe = StockScreener(
    Factor.REC.value_range(2, None) & Factor.QuickRatio.value_range(2.5, None) & Factor.MA5.value_range(20, None)) + [
               '000610.XSHE', '000755.XSHE', '600149.XSHG', '600228.XSHG', '000507.XSHE', '002438.XSHE', '000609.XSHE',
               '002113.XSHE', '002148.XSHE', '002248.XSHE', '000779.XSHE', '000502.XSHE', '000586.XSHE', '600689.XSHG',
               '600671.XSHG', '601018.XSHG']


def initialize(account):
    account.i = 0
    account.daily_trigger_time = "14:45"
    account.init_universe = ['000610.XSHE', '000755.XSHE', '600149.XSHG', '000507.XSHE', '002438.XSHE', '000609.XSHE',
                             '002113.XSHE', '002148.XSHE', '002248.XSHE', '000779.XSHE', '000502.XSHE', '000586.XSHE',
                             '600689.XSHG', '600671.XSHG', ]


def handle_data(account):
    log.info("init universe:" + str(account.init_universe))
    if account.i == 0 or len(account.security_position.keys()) <= 6 or len(account.security_position.keys()) >= 20:
        last_date = account.previous_date.strftime("%Y-%m-%d")
        last_screener = universe.preview(last_date)

        log.info(last_screener)

        buylist = [sec for sec in last_screener if sec in account.init_universe]
        v = account.referencePortfolioValue
        d = len(buylist)

        # 卖出不在买入列表中的股票，估计持仓价值
        for stock in account.valid_secpos:
            if stock not in buylist:
                if stock in account.universe:
                    order_to(stock, 0)
                else:
                    v -= account.valid_secpos[stock] * account.referencePrice[stock]

        # 获得调仓数量
        change = {}
        for stock in buylist:
            p = account.referencePrice[stock]
            if p and not np.isnan(p):
                change[stock] = int(v / d / p) - account.valid_secpos.get(stock, 0)

        # 按先卖后买的顺序发出指令
        for stock in sorted(change, key=change.get):
            if change[stock] <= -100 or change[stock] >= 100:
                order(stock, change[stock])
    else:
        # 从stockscreener中读取符合筛选条件的n只买入股票
        last_date = account.previous_date.strftime("%Y-%m-%d")
        last_screener = universe.preview(last_date)

        log.info("last_screener:" + str(last_screener))

        open_last_screener = [i for i in last_screener if
                              DataAPI.MktEqudGet(tradeDate=account.previous_date, secID=i, field=u"isOpen",
                                                 pandas="1").loc[0, 'isOpen'] == 1]

        log.info("buy_universe:" + str(open_last_screener))

        buy_list = [stk for stk in open_last_screener if
                    stk not in account.security_position.keys() and stk not in account.init_universe]

        # 生成业绩最好和最差的1只股票的卖出列表
        sell_dict = sorted(account.reference_return.items(), key=lambda d: d[1])
        sell_list = []
        for value in sell_dict:
            stk, _ = value
            sell_list.append(stk)

        log.info("sorted account.reference_return:" + str(sell_dict))
        log.info("account.valid_secpos.keys:" + str(account.avail_security_position.keys()))
        to_sell_list = [i for i in sell_list if i in account.avail_security_position.keys()]
        # available_sell_list = to_sell_list[0:len(to_sell_list):len(to_sell_list)-1]
        available_sell_list = to_sell_list[0:2]
        log.info("sell_list:" + str(sell_list))
        log.info("available to sell universe:" + str(available_sell_list))

        # 获取卖出股票的持仓权重
        value_sell = []
        for i in available_sell_list:
            "{index}to sell value {value}:".format(index=i,
                                                   value=account.avail_security_position[i] * account.referencePrice[i])
            value_sell.append(
                account.avail_security_position[i] * account.referencePrice[i] / account.referencePortfolioValue)

        len_buy_list = 2 if len(buy_list) > 2 else len(buy_list)

        to_buy_list = [buy_list[i] for i in range(len_buy_list)]

        log.info("weight of universe:" + str(value_sell))
        log.info("len of weights" + str(len(value_sell)))
        log.info("len of buy_list:" + str(len_buy_list))

        buy_dict = dict(zip(to_buy_list, value_sell))
        log.info("buy_dict:" + str(buy_dict))
        for s in available_sell_list:
            order_to(s, 0)
        log.info("sell success")
        for key in buy_dict:
            order_pct(key, buy_dict[key])
        log.info("order completed")
    account.i += 1
    log.info(str(account.i))
