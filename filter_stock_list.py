# -*- coding:utf-8 -*- 

#from kuanke.user_space_api import *
from rule import *
from util import *
import pandas as pd
import numpy as np
import datetime

'''==============================选股 stock_list过滤器基类=============================='''
class Filter_stock_list(Rule):
    __name__='Filter_stock_list'
    def before_trading_start(self, context):
        return None
    def filter(self,context,data,stock_list):
        return None

class Filter_gem(Filter_stock_list):
    __name__='Filter_gem'
    def before_trading_start(self, context):

        result_list = []

        for stock in context.stock_list:
            if stock[0:3] != '300':
                result_list.append(stock)
                pass

        context.stock_list = result_list

        print('Filter_gem count = ', len(context.stock_list))

        return None
    def filter(self,context,data,stock_list):
        return [stock for stock in stock_list if stock[0:3] != '300']
    def __str__(self):
        return '过滤创业板股票'

        
class Filter_paused_stock(Filter_stock_list):
    __name__='Filter_paused_stock'
    def before_trading_start(self, context):

        result_list = []

        for stock in context.stock_list:
            if not is_suspended(stock):
                result_list.append(stock)
                pass
                
        context.stock_list = result_list
        print('Filter_paused_stock count = ', len(context.stock_list))

        return None
    def filter(self,context,data,stock_list):
        return [stock for stock in stock_list
            if not is_suspended(stock)
            ]

    def __str__(self):
        return '过滤停牌股票'
    
class Filter_limitup(Filter_stock_list):
    __name__='Filter_limitup'
    def before_trading_start(self, context):
 
        #盘前过滤前日涨停
        result_list = []
 
        for stock in context.stock_list:
            h = history_bars(stock, 1, '1d', 'high')
            l = history_bars(stock, 1, '1d', 'low')

            if h[0] != l[0] and instruments(stock).days_from_listed() > 5:
                result_list.append(stock)

        context.stock_list = result_list

        print('Filter_limitup count = ', len(context.stock_list))

        return context.stock_list
    def filter(self,context,data,stock_list):
            #todo: 2月14日的数据有问题?
        return [stock for stock in stock_list if stock in context.portfolio.positions.keys()
            or data[stock].close < data[stock].limit_up or data[stock].high != data[stock].low]
    def __str__(self):
        return '过滤涨停股票,已持仓股不过滤'
'''
class Filter_drop_percentage(Filter_stock_list):
    __name__='Filter_drop_percentage'

    def __init__(self,params):
        self.drop_percent = params.get('drop_percent', -0.05)
    def update_params(self,context,params):
        self.drop_percent = params.get('drop_percent', drop_percent)

    def filter(self,context,data,stock_list):
        for stock in stock_list:
            if ((current_snapshot(stock).last - current_snapshot(stock).prev_close)/ current_snapshot(stock).prev_close) < self.drop_percent:
                print(stock, '过滤当日跌幅-5', current_snapshot(stock).last, current_snapshot(stock).prev_close)


        return [stock for stock in stock_list 
            if ((current_snapshot(stock).last - current_snapshot(stock).prev_close)/ current_snapshot(stock).prev_close) > self.drop_percent]

    def __str__(self):
        return '过滤当日跌幅5%的股票'
'''
'''     
class Filter_limitdown(Filter_stock_list):
    __name__='Filter_limitdown'
    def filter(self,context,data,stock_list):
        return [stock for stock in stock_list 
            if stock in context.portfolio.positions.keys()
            or data[stock].close > data[stock].limit_down]
    def __str__(self):
        return '过滤跌停股票,已持仓股不过滤' 
'''
'''
class Filter_growth_rate_stock(Filter_stock_list):
    __name__='Filter_growth_rate_stock'
    def __init__(self,params):
        self.gr_max = params.get('gr_max', 0.2)
        self.gr_min = params.get('gr_min', -0.05)
        self.period = params.get('period', 5)
    def before_trading_start(self, context):
        return context.stock_list
    def update_params(self,context,params):
        self.gr_max = params.get('gr_max',self.gr_max)
        self.gr_min = params.get('gr_min',self.gr_min)
        self.period = params.get('period',self.period)
    def filter(self,context,data,stock_list):
        return [stock for stock in stock_list 
            if get_growth_rate(stock, self.period) > self.gr_min and
            get_growth_rate(stock, self.period) < self.gr_max]
    def __str__(self):
        return '过滤n日涨幅为特定值的股票'
'''
class Filter_old_stock(Filter_stock_list):
    __name__='Filter_old_stock'
    def __init__(self,params):
        self.day_count_min = params.get('day_count_min', 5)
        self.day_count_max = params.get('day_count_max', 80)

    def before_trading_start(self, context):
        
        context.stock_list = [stock for stock in context.stock_list 
            if instruments(stock).days_from_listed() <= self.day_count_max and instruments(stock).days_from_listed() >= self.day_count_min]

        print('Filter_old_stock count = ', len(context.stock_list))

        return context.stock_list

    def update_params(self,context,params):
        self.day_count_min = params.get('day_count_min', self.day_count_min)
        self.day_count_max = params.get('day_count_max', self.day_count_max)
    def filter(self,context,data,stock_list):
        return [stock for stock in stock_list 
            if instruments(stock).days_from_listed() <= self.day_count_max and instruments(stock).days_from_listed() >= self.day_count_min]
    def __str__(self):
        return '过滤上市时间超过 %d 天的股票'%(self.day_count) 
'''
class Filter_turnover_rate_stock(Filter_stock_list):
    __name__='Filter_turnover_rate_stock'
    def __init__(self,params):
        self.turnover_rate_max = params.get('turnover_rate_max', 0.16)
        self.turnover_rate_min = params.get('turnover_rate_min', 0.03)
    def update_params(self,context,params):
        self.turnover_rate_max = params.get('turnover_rate_max',self.turnover_rate_max)
        self.turnover_rate_min = params.get('turnover_rate_min',self.turnover_rate_min)
    def filter(self,context,data,stock_list):
        return [stock for stock in stock_list 
            if get_turnover_rate(stock, count = 1).iloc[0, 0] >= self.turnover_rate_min 
            and self.turnover_rate_max >= get_turnover_rate(stock, count = 1).iloc[0, 0]
            ]
    def __str__(self):
        return '过滤换手率' 
'''
'''
class Filter_CS_stock(Filter_stock_list):
    __name__='Filter_cs_stock'
    def filter(self,context,data,stock_list):
        return [stock for stock in stock_list 
            if get_securities_margin(stock, count = 1)['margin_balance'][0] > 0]

    def __str__(self):
        return '过滤融资融券股票'
'''

class Filter_just_open_limit(Filter_stock_list):
    __name__='过滤新开板股票'
    def before_trading_start(self, context):
        for stock in context.stock_list:
            #两种可能，前一天如果是涨停则为开板，前一天不是涨停，就是跌入股票池
            history = history_bars(stock, 2, '1d', 'close')
            if len(history) == 2 and history[0]*1.099 > history[1]:
                result_list.append(stock)

        return context.stock_list
    def filter(self,context,data,stock_list):

        result_list = []

        if context.stock_list == None:
            context.stock_list = stock_list
            result_list = stock_list
        else:
            for stock in stock_list:
                if stock not in context.stock_list:
                    #两种可能，前一天如果是涨停则为开板，前一天不是涨停，就是跌入股票池
                    history = history_bars(stock, 2, '1d', 'close')
                    if len(history) == 2 and history[0]*1.099 > history[1]:
                        result_list.append(stock)
                else:
                    result_list.append(stock)

        return result_list
    def __str__(self):
        return '过滤新开板股票'

class Filter_st(Filter_stock_list):
    __name__='Filter_st'
    def filter(self,context,data,stock_list):
        current_data = get_current_data()
        return [stock for stock in stock_list
            if not is_st_stock(stock)
            ]
    def __str__(self):
        return '过滤ST股票'

class Filter_growth_is_down(Filter_stock_list):
    __name__='Filter_growth_is_down'
    def __init__(self,params):
        self.day_count = params.get('day_count', 20)
    
    def update_params(self,context,params):
        self.day_count = params.get('day_count', self.day_count)

    def filter(self,context,data,stock_list):
        return [stock for stock in stock_list if get_growth_rate(stock, self.day_count) > 0]
    
    def __str__(self):
        return '过滤n日增长率为负的股票'
 
class Filter_blacklist(Filter_stock_list):
    __name__='Index28_condition'
    def __get_blacklist(self):
        # 黑名单一览表，更新时间 2016.7.10 by 沙米
        # 科恒股份、太空板业，一旦2016年继续亏损，直接面临暂停上市风险
        blacklist = ["600656.XSHG", "300372.XSHE", "600403.XSHG", "600421.XSHG", "600733.XSHG", "300399.XSHE",
                     "600145.XSHG", "002679.XSHE", "000020.XSHE", "002330.XSHE", "300117.XSHE", "300135.XSHE",
                     "002566.XSHE", "002119.XSHE", "300208.XSHE", "002237.XSHE", "002608.XSHE", "000691.XSHE",
                     "002694.XSHE", "002715.XSHE", "002211.XSHE", "000788.XSHE", "300380.XSHE", "300028.XSHE",
                     "000668.XSHE", "300033.XSHE", "300126.XSHE", "300340.XSHE", "300344.XSHE", "002473.XSHE"]
        return blacklist
        
    def filter(self,context,data,stock_list):
        blacklist = self.__get_blacklist()
        return [stock for stock in stock_list if stock not in blacklist]
    def __str__(self):
        return '过滤黑名单股票'
        
class Filter_rank(Filter_stock_list):
    __name__='Filter_rank'
    def __init__(self,params):
        self.rank_stock_count = params.get('rank_stock_count',20)
    def update_params(self,context,params):
        self.rank_stock_count = params.get('self.rank_stock_count', self.rank_stock_count)

    def before_trading_start(self, context):

        stock_score(context)

        if len(context.stock_list) > self.rank_stock_count:
            context.stock_list = context.stock_list[:self.rank_stock_count]

        print('Filter_buy_count count = ', len(context.stock_list))

        return None

    def filter(self,context,data,stock_list):
        return None

    def after_trading_end(self, context):

        stock_score(context)

        return None
        
    def __str__(self):
        return '股票评分排序 [评分股数: %d ]'%(self.rank_stock_count)
'''
class Filter_low_structure(Filter_stock_list):
    __name__='Filter_low_structure'
    def __init__(self,params):
        self.period = params.get('period', '1d')
        self.back_days = params.get('back_days', 250)
        #self.bar_1 = {}
        #self.bar = {}
    def update_params(self,context,params):
        self.period = params.get('period',self.period)

    def before_trading_start(self, context):


    def filter(self,context,data,stock_list):
        return stock_list 
        
    def __str__(self):
        return '定量结构'
'''
        
class Filter_buy_count(Filter_stock_list):
    __name__='Filter_buy_count'
    def __init__(self,params):
        self.buy_count = params.get('buy_count',3)

    def update_params(self,context,params):
        self.buy_count = params.get('buy_count', self.buy_count)

    def before_trading_start(self, context):

        if len(context.stock_list) > self.buy_count:

            context.stock_list = context.stock_list[:self.buy_count]

        print('Filter_buy_count count = ', len(context.stock_list))

        return context.stock_list

    def filter(self,context,data,stock_list):

        if len(context.stock_list) > self.buy_count:

            context.stock_list = context.stock_list[:self.buy_count]

        print('Filter_buy_count count = ', len(context.stock_list))

        return context.stock_list
    def __str__(self):
        return '获取最终待购买股票数:[ %d ]'%(self.buy_count)