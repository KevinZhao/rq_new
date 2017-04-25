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

        today = context.now.date();

        #清空历史数据
        context.bar_15 = {}
        context.bar_30 = {}
        context.bar_60 = {}

        #补全数据
        #选股池列表
        for stock in context.stock_list:
            #初始化30分钟线数据
            context.bar_30[stock] = get_price(stock, start_date = today - datetime.timedelta(days = 70), end_date = today - datetime.timedelta(days = 1), frequency = '30m').tail(150)
            context.bar_60[stock] = get_price(stock, start_date = today - datetime.timedelta(days = 150), end_date = today - datetime.timedelta(days = 1), frequency = '60m').tail(150)
            context.bar_15[stock] = get_price(stock, start_date = today - datetime.timedelta(days = 40), end_date = today - datetime.timedelta(days = 1), frequency = '15m').tail(150)
        #持仓列表
        for stock in context.portfolio.positions.keys():
            #且不在选股池列表中
            if stock not in context.stock_list:
                #初始化30分钟线数据
                context.bar_30[stock] = get_price(stock, start_date = today - datetime.timedelta(days = 70), end_date = today - datetime.timedelta(days = 1), frequency = '30m').tail(150)
                context.bar_60[stock] = get_price(stock, start_date = today - datetime.timedelta(days = 150), end_date = today - datetime.timedelta(days = 1), frequency = '60m').tail(150)
                context.bar_15[stock] = get_price(stock, start_date = today - datetime.timedelta(days = 40), end_date = today - datetime.timedelta(days = 1), frequency = '15m').tail(150)

        #计算数据
        for stock in context.bar_15.keys():
            context.bar_15[stock]['bottom_alert'] = pd.DataFrame(None, index = context.bar_15[stock].index, columns = ['bottom_alert'])
            context.bar_15[stock]['bottom_buy'] = pd.DataFrame(None, index = context.bar_15[stock].index, columns = ['bottom_buy'])
            context.bar_15[stock] = macd_alert_calculation(context.bar_15[stock]); 

            if context.bar_15[stock].iloc[-1]['bottom_alert'] == 1:
                print(instruments(stock).symbol, "15分钟钝化", stock)
            if context.bar_15[stock].iloc[-1]['bottom_buy'] == 1:
                print(instruments(stock).symbol, "15分钟结构", stock)

        for stock in context.bar_30.keys():
            context.bar_30[stock]['bottom_alert'] = pd.DataFrame(None, index = context.bar_30[stock].index, columns = ['bottom_alert'])
            context.bar_30[stock]['bottom_buy'] = pd.DataFrame(None, index = context.bar_30[stock].index, columns = ['bottom_buy'])
            context.bar_30[stock] = macd_alert_calculation(context.bar_30[stock]); 

            if context.bar_30[stock].iloc[-1]['bottom_alert'] == 1:
                print(instruments(stock).symbol, "30分钟钝化", stock)
            if context.bar_30[stock].iloc[-1]['bottom_buy'] == 1:
                print(instruments(stock).symbol, "30分钟结构", stock)

        for stock in context.bar_60.keys():
            context.bar_60[stock]['bottom_alert'] = pd.DataFrame(None, index = context.bar_60[stock].index, columns = ['bottom_alert'])
            context.bar_60[stock]['bottom_buy'] = pd.DataFrame(None, index = context.bar_60[stock].index, columns = ['bottom_buy'])
            context.bar_60[stock] = macd_alert_calculation(context.bar_60[stock]); 

            if context.bar_60[stock].iloc[-1]['bottom_alert'] == 1:
                print(instruments(stock).symbol, "60分钟钝化", stock)
            if context.bar_60[stock].iloc[-1]['bottom_buy'] == 1:
                print(instruments(stock).symbol, "60分钟结构", stock)

        context.index_df = get_price('399678.XSHE', start_date = today - datetime.timedelta(days = 300), end_date = today - datetime.timedelta(days = 1), frequency = '1d').tail(150)
        context.index_df['bottom_alert'] = pd.DataFrame(None, index = context.index_df.index, columns = ['bottom_alert'])
        context.index_df['bottom_buy'] = pd.DataFrame(None, index = context.index_df.index, columns = ['bottom_buy'])        
        context.index_df = macd_alert_calculation(context.index_df)
        
        return None

    def handle_data(self,context,data):

        for stock in context.stock_list:
            self.handle_minute_data(context,data,stock)
            
        for stock in context.portfolio.positions.keys():
            if stock not in context.stock_list:
                self.handle_minute_data(context,data,stock)

    def handle_minute_data(self, context, data, stock):

        if context.timedelt % 15 == 0:
            temp_data = pd.DataFrame(
                {"low":history_bars(stock, 1, '15m', 'low')[0],
                "open":"",
                "high":history_bars(stock, 1, '15m', 'high')[0],
                "volume":"",
                "close":history_bars(stock, 1, '15m', 'close')[0],
                "total_turnover":""}, index = ["0"])
            
            context.bar_15[stock] = context.bar_15[stock].append(temp_data, ignore_index = True)
            context.bar_15[stock] = macd_alert_calculation(context.bar_15[stock])
            
            if context.bar_15[stock].iloc[-1]['bottom_alert'] == 1:
                print(instruments(stock).symbol, "15分钟钝化", stock)
            if context.bar_15[stock].iloc[-1]['bottom_buy'] == 1:
                print(instruments(stock).symbol, "15分钟结构", stock)
            
        if context.timedelt % 30 == 0:
            
            temp_data = pd.DataFrame(
                {"low":history_bars(stock, 1, '30m', 'low')[0],
                "open":"",
                "high":history_bars(stock, 1, '30m', 'high')[0],
                "volume":"",
                "close":history_bars(stock, 1, '30m', 'close')[0],
                "total_turnover":""}, index = ["0"])

            context.bar_30[stock] = context.bar_30[stock].append(temp_data, ignore_index = True)
            context.bar_30[stock] = macd_alert_calculation(context.bar_30[stock])

            if context.bar_30[stock].iloc[-1]['bottom_alert'] == 1:
                print(instruments(stock).symbol, "30分钟钝化", stock)
            if context.bar_30[stock].iloc[-1]['bottom_buy'] == 1:
                print(instruments(stock).symbol, "30分钟结构", stock)

        if context.timedelt % 60 == 0:

            temp_data = pd.DataFrame(
                {"low":history_bars(stock, 1, '60m', 'low')[0],
                "open":"",
                "high":history_bars(stock, 1, '60m', 'high')[0],
                "volume":"",
                "close":history_bars(stock, 1, '60m', 'close')[0],
                "total_turnover":""}, index = ["0"])

            context.bar_60[stock] = context.bar_60[stock].append(temp_data, ignore_index = True)
            context.bar_60[stock] = macd_alert_calculation(context.bar_60[stock])

            if context.bar_60[stock].iloc[-1]['bottom_alert'] == 1:
                print(instruments(stock).symbol, "60分钟钝化", stock)
            if context.bar_60[stock].iloc[-1]['bottom_buy'] == 1:
                print(instruments(stock).symbol, "60分钟结构", stock)


    def __str__(self):
        return '分钟数据处理'