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
    def after_trading_end(self, context):
        return None

class Handle_data_df(Handle_data_rule):
    __name__='Handle_data_df'

    def before_trading_start(self, context):

        today = context.now.date();

        #清空历史数据
        context.bar_15 = {}
        context.bar_30 = {}
        context.bar_60 = {}

        for stock in context.stock_list:

            #print(history_bars(stock, 150, frequency = '30m', fields = ['close', 'high', 'low'], include_now = False))

            #初始化30分钟线数据
            context.bar_30[stock] = pd.DataFrame(history_bars(stock, 150, frequency = '30m', fields = ['close', 'high', 'low'], include_now = False), index = None)
            context.bar_60[stock] = pd.DataFrame(history_bars(stock, 150, frequency = '60m', fields = ['close', 'high', 'low']), index = None)
            context.bar_15[stock] = pd.DataFrame(history_bars(stock, 150, frequency = '15m', fields = ['close', 'high', 'low']), index = None)

        #持仓列表
        for stock in context.portfolio.positions.keys():
            #且不在选股池列表中
            if stock not in context.stock_list:
                #初始化30分钟线数据
                context.bar_30[stock] = pd.DataFrame(history_bars(stock, 150, frequency = '30m', fields = ['close', 'high', 'low']), index = None)
                context.bar_60[stock] = pd.DataFrame(history_bars(stock, 150, frequency = '60m', fields = ['close', 'high', 'low']), index = None)
                context.bar_15[stock] = pd.DataFrame(history_bars(stock, 150, frequency = '15m', fields = ['close', 'high', 'low']), index = None)

        #-------------------------------------------#
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

        #次新指数
        context.index_df = pd.DataFrame(history_bars('399678.XSHE', 150, frequency = '1d', fields = ['close', 'high', 'low']), index = None)
        context.index_df['bottom_alert'] = pd.DataFrame(None, index = context.index_df.index, columns = ['bottom_alert'])
        context.index_df['bottom_buy'] = pd.DataFrame(None, index = context.index_df.index, columns = ['bottom_buy'])        
        context.index_df = macd_alert_calculation(context.index_df)

        '''
        context.index_df_30 = pd.DataFrame(history_bars('399678.XSHE', 150, frequency = '30m', fields = ['close', 'high', 'low'], include_now = True), index = None)
        context.index_df_30['bottom_alert'] = pd.DataFrame(None, index = context.index_df_30.index, columns = ['bottom_alert'])
        context.index_df_30['bottom_buy'] = pd.DataFrame(None, index = context.index_df_30.index, columns = ['bottom_buy'])  
        context.index_df_30 = macd_alert_calculation(context.index_df_30)

        if context.index_df_30.iloc[-1]['bottom_buy'] == 1:
            print("399678指数 30分钟底部结构")
        '''
        

        #自选股评分
        stock_score(context)

        return None

    def handle_data(self,context,data):

        #分钟线数据制作
        for stock in context.stock_list:
            self.handle_minute_data(context,data,stock)
            
        for stock in context.portfolio.positions.keys():
            if stock not in context.stock_list:
                self.handle_minute_data(context,data,stock)

        #选股评分
        if context.timedelt % 60 == 0:
            stock_score(context, data)

        '''
        #指数分时线结构
        if context.timedelt % 30 == 0:

            context.index_df_30 = pd.DataFrame(history_bars('399678.XSHE', 150, frequency = '30m', fields = None, include_now = True), index = None)
            context.index_df_30['bottom_alert'] = pd.DataFrame(None, index = context.index_df_30.index, columns = ['bottom_alert'])
            context.index_df_30['bottom_buy'] = pd.DataFrame(None, index = context.index_df_30.index, columns = ['bottom_buy'])  
            context.index_df_30 = macd_alert_calculation(context.index_df_30)

            if context.index_df_30.iloc[-1]['bottom_buy'] == 1:
                print("399678指数 30分钟底部结构")
        '''


        #指数日线快照
        if context.timedelt % 30 == 0:

            temp_data = pd.DataFrame(history_bars('399678.XSHE', 1, frequency = '1d', fields = ['close', 'high', 'low'], include_now = True), index = None)

            context.index_df = context.index_df.head(150)    
            context.index_df = context.index_df.append(temp_data, ignore_index = True)
            context.index_df = macd_alert_calculation(context.index_df)

    def handle_minute_data(self, context, data, stock):

        if context.timedelt % 15 == 0:
            temp_data = pd.DataFrame(history_bars(stock, 1, frequency = '15m', fields = ['close', 'high', 'low'], include_now = True), index = None)
            
            context.bar_15[stock] = context.bar_15[stock].append(temp_data, ignore_index = True)
            context.bar_15[stock] = macd_alert_calculation(context.bar_15[stock])
            
            if context.bar_15[stock].iloc[-1]['bottom_alert'] == 1:
                print(instruments(stock).symbol, "15分钟钝化", stock)
            if context.bar_15[stock].iloc[-1]['bottom_buy'] == 1:
                print(instruments(stock).symbol, "15分钟结构", stock)
            
        if context.timedelt % 30 == 0:
            
            temp_data = pd.DataFrame(history_bars(stock, 1, frequency = '30m', fields = ['close', 'high', 'low'], include_now = True), index = None)

            context.bar_30[stock] = context.bar_30[stock].append(temp_data, ignore_index = True)
            context.bar_30[stock] = macd_alert_calculation(context.bar_30[stock])

            if context.bar_30[stock].iloc[-1]['bottom_alert'] == 1:
                print(instruments(stock).symbol, "30分钟钝化", stock)
            if context.bar_30[stock].iloc[-1]['bottom_buy'] == 1:
                print(instruments(stock).symbol, "30分钟结构", stock)

        if context.timedelt % 60 == 0:

            temp_data = pd.DataFrame(history_bars(stock, 1, frequency = '60m', fields = ['close', 'high', 'low'], include_now = True), index = None)

            context.bar_60[stock] = context.bar_60[stock].append(temp_data, ignore_index = True)
            context.bar_60[stock] = macd_alert_calculation(context.bar_60[stock])

            if context.bar_60[stock].iloc[-1]['bottom_alert'] == 1:
                print(instruments(stock).symbol, "60分钟钝化", stock)
            if context.bar_60[stock].iloc[-1]['bottom_buy'] == 1:
                print(instruments(stock).symbol, "60分钟结构", stock)

    def after_trading_end(self, context):

        stock_score(context)

        return None

    def __str__(self):
        return '分钟数据处理'