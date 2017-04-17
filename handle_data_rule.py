# -*- coding:utf-8 -*- 

#from kuanke.user_space_api import *
from rule import *
from util import *
import pandas as pd

'''==============================选股 stock_list过滤器基类=============================='''
class Handle_data_rule(Rule):
    __name__='Handle_data_rule'
    def before_trading_start(self, context):
        return None
    def handle_data(self,context,data):
        return None

class Handle_data_df(Handle_data_rule):
    __name__='Handle_data_df'

    def before_trading_start(self, context):

        #获取历史30分钟数据
        today = context.now.date();

        for stock in context.stock_list:

            if stock not in context.bar_30.keys():

                #初始化30分钟线数据
                context.bar_30[stock] = get_price(stock, start_date = today - datetime.timedelta(days = 70), end_date = today - datetime.timedelta(days = 1), frequency = '30m').tail(150)
                context.bar_30[stock] = macd_alert_calculation(context.bar_30[stock], stock); 

                context.bar_60[stock] = get_price(stock, start_date = today - datetime.timedelta(days = 150), end_date = today - datetime.timedelta(days = 1), frequency = '60m').tail(150)
                context.bar_60[stock] = macd_alert_calculation(context.bar_60[stock], stock)
                #print('called2')

        for stock in context.portfolio.positions.keys():

            if stock not in context.stock_list:
                #初始化30分钟线数据
                context.bar_30[stock] = get_price(stock, start_date = today - datetime.timedelta(days = 70), end_date = today - datetime.timedelta(days = 1), frequency = '30m').tail(150)
                
                context.bar_60[stock] = get_price(stock, start_date = today - datetime.timedelta(days = 150), end_date = today - datetime.timedelta(days = 1), frequency = '60m').tail(150)
  

        #指数
        context.index_df = get_price('399678.XSHE', start_date = today - datetime.timedelta(days = 200), end_date = today - datetime.timedelta(days = 1), frequency = '1d').tail(150)
        '''
        #context.index_df_15 = get_price('399678.XSHE', start_date = today - datetime.timedelta(days = 40), end_date = today - datetime.timedelta(days = 1), frequency = '15m').tail(150)
        context.index_df_30 = get_price('399678.XSHE', start_date = today - datetime.timedelta(days = 70), end_date = today - datetime.timedelta(days = 1), frequency = '30m').tail(150)
        context.index_df_60 = get_price('399678.XSHE', start_date = today - datetime.timedelta(days = 100), end_date = today - datetime.timedelta(days = 1), frequency = '60m').tail(150)
        
        #context.index_df_15 = get_price('399678.XSHE', 150, '15m', 'close')
        context.index_df_15 = get_price('000001.XSHG', start_date = '2017-01-01', end_date = today, frequency='30m', fields=None, adjust_type='pre', skip_suspended=False)

        print(context.index_df_60, context.index_df_30, context.index_df_15)
        '''

        return None

    def handle_data(self,context,data):

        for stock in context.stock_list:
            self.handle_minute_data(context,data,stock)
            
        for stock in context.portfolio.positions.keys():
            if stock not in context.stock_list:
                self.handle_minute_data(context,data,stock)

    def handle_minute_data(self, context, data, stock):
            
        if context.timedelt % 30 == 0:
            
            temp_data = pd.DataFrame(
                {"low":history_bars(stock, 1, '30m', 'low')[0],
                "open":"",
                "high":history_bars(stock, 1, '30m', 'high')[0],
                "volume":"",
                "close":history_bars(stock, 1, '30m', 'close')[0],
                "total_turnover":""}, index = ["0"])
            
            context.bar_30[stock] = context.bar_30[stock].append(temp_data, ignore_index = True)
            context.bar_30[stock] = calculate_macd(context.bar_30[stock])

        if context.timedelt % 60 == 0:

            temp_data = pd.DataFrame(
                {"low":history_bars(stock, 1, '60m', 'low')[0],
                "open":"",
                "high":history_bars(stock, 1, '60m', 'high')[0],
                "volume":"",
                "close":history_bars(stock, 1, '60m', 'close')[0],
                "total_turnover":""}, index = ["0"])

            context.bar_60[stock] = context.bar_60[stock].append(temp_data, ignore_index = True)


    def __str__(self):
        return '分钟数据处理'