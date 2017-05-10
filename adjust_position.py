# -*- coding:utf-8 -*- 

#from kuanke.user_space_api import *
from rule import *
from util import *
import pandas


'''==============================个股止盈止损规则=============================='''

''' ---------个股止损 by 自最高值回落一定比例比例进行止损-------------------------'''
class Stop_loss_stocks_by_percentage(Rule):
    __name__='Stop_loss_stocks_by_percentage'

    def __init__(self,params):
        self.percent = params.get('percent', 0.08)

    def update_params(self,context,params):
        self.percent = params.get('percent', self.period)
        
    # 个股止损
    def handle_data(self,context, data):

        #持仓股票循环
        for stock in context.portfolio.positions.keys():

            #持有数量超过0
            if context.portfolio.positions[stock].quantity > 0:

                #当前价格
                cur_price = data[stock].close
                
                #历史最高价格
                stockdic = context.maxvalue[stock]
                highest = stockdic[0]

                if data[stock].high > highest:

                    del context.maxvalue[stock]        
                    temp = pd.DataFrame({str(stock):[max(highest, data[stock].high)]})
                    context.maxvalue = pd.concat([context.maxvalue, temp], axis=1, join='inner') # 更新其盘中最高价值和先阶段比例。

                    #更新历史最高价格
                    stockdic = context.maxvalue[stock]
                    highest = stockdic[0]

                if cur_price < highest * (1 - self.percent):
                    position = context.portfolio.positions[stock]
                    self.close_position(position, False)
                    context.black_list.append(stock)

                    print('[比例止损卖出]', instruments(stock).symbol, context.portfolio.positions[stock].avg_price, highest, data[stock].last)
            else:
                if stock in context.ATRList:
                    context.ATRList.remove(stock)

                #if stock in context.maxvalue.keys:
                    #del context.maxvalue[stock]

    def when_sell_stock(self,position,order,is_normal):
        #if position.security in self.last_high:
        #    self.last_high.pop(position.security)
        pass
    
    def when_buy_stock(self,stock,order):
        #if order.status == OrderStatus.held and order.filled == order.amount:
            # 全部成交则删除相关证券的最高价缓存
        #    self.last_high[stock] = get_close_price(stock, 1, '1m')
        pass
           
    def __str__(self):
        return '个股止损器:[按比例止损: %d ]' %self.percent

''' ----------------------个股止损 by ATR 60-------------------------------------'''
class Stop_loss_stocks_by_ATR(Rule):
    __name__='Stop_loss_stocks_by_ATR'

    def __init__(self,params):
        pass
    def update_params(self,context,params):
        pass
    # 个股止损
    def handle_data(self, context, data):

        #if context.timedelt % 60 == 0:
        #    print(context.ATRList)

        for stock in context.ATRList:

            if stock in context.portfolio.positions.keys() and context.portfolio.positions[stock].quantity > 0: 

                stockdic = context.maxvalue[stock]
                highest = stockdic[0]

                #当前涨幅判断
                raisePercentage = (highest - context.portfolio.positions[stock].avg_price) /context.portfolio.positions[stock].avg_price
                #print(highest, raisePercentage)

                if  raisePercentage > 0.18:

                    bar = context.bar_60
                    minute = '60分钟'

                if  (raisePercentage > 0.12) and (raisePercentage <= 0.18):

                    bar = context.bar_30
                    minute = '30分钟'

                if  (raisePercentage >= 0.06) and (raisePercentage <= 0.12):

                    bar = context.bar_15
                    minute = '15分钟'

                if (raisePercentage < 0.06):
                    return


                ATR = findATR(context, bar, stock)

                #print(stock, minute, ATR, ATR/context.portfolio.positions[stock].avg_price)

                high = bar[stock].iloc[-1]['high']
                current = bar[stock].iloc[-1]['close']

                del context.maxvalue[stock]        
                temp = pd.DataFrame({str(stock):[max(highest,high)]})

                context.maxvalue= pd.concat([context.maxvalue, temp], axis=1, join='inner') # 更新其盘中最高价值和先阶段比例。

                stockdic = context.maxvalue[stock]
                highest = stockdic[0]
        
                if data[stock].close < highest - 3*ATR:
                
                    print(minute, '[ATR止损卖出]', instruments(stock).symbol, context.portfolio.positions[stock].avg_price, highest, data[stock].last, ATR)
                    position = context.portfolio.positions[stock]
                    self.close_position(position)
                    context.black_list.append(stock)
            else:
                del context.maxvalue[stock]
                context.ATRList.remove(stock)

        
    def when_sell_stock(self,position,order,is_normal):
        #if position.security in self.last_high:
        #    self.last_high.pop(position.security)
        pass
    
    def when_buy_stock(self,stock,order):
        #if order.status == OrderStatus.held and order.filled == order.amount:
            # 全部成交则删除相关证券的最高价缓存
        #    self.last_high[stock] = get_close_price(stock, 1, '1m')
        pass

    def after_trading_end(self,context):
        #self.pct_change = {}
        pass
           
    def __str__(self):
        return '个股止损器:ATR止损'

'''==============================调仓的操作基类================================'''
class Adjust_position(Rule):
    __name__='Adjust_position'
    def adjust(self,context,data,buy_stocks):
        pass

'''---------------卖出股票规则------------------------'''
'''---------------个股涨幅超过5%，进入ATR--------------'''  
class Sell_stocks(Adjust_position):
    __name__='Sell_stocks'
    def adjust(self,context,data,buy_stocks):
        
        for stock in context.portfolio.positions.keys():
            
            if context.portfolio.positions[stock].quantity == 0:
                return

            if context.portfolio.positions[stock].sellable == 0:
                return

            #if data[stock].close < context.portfolio.positions[stock].avg_price * 1.04:

                #止损
                #if data[stock].close < context.portfolio.positions[stock].avg_price * 0.92:
                    #position = context.portfolio.positions[stock]
                    #self.close_position(position)
                    #context.black_list.append(stock)

            if (context.maxvalue[stock][0] - context.portfolio.positions[stock].avg_price)/context.portfolio.positions[stock].avg_price > 0.04:
                if stock not in context.ATRList: 
                    context.ATRList.append(stock)
                    
            if stock in context.stock_60:
                #涨幅 8%
                if data[stock].close > context.portfolio.positions[stock].avg_price * 1.07:
                    positions = context.portfolio.positions[stock]
                    percentage = context.portfolio.positions[stock].value_percent

                    print(stock, instruments(stock).symbol, data[stock].close, '60分钟 7%止盈卖出')
                    close_position_2(positions, percentage)
                    context.black_list.append(stock)
                    context.stock_60.remove(stock)

            if stock in context.stock_30:
                #涨幅 4%
                if data[stock].close > context.portfolio.positions[stock].avg_price * 1.04:
                    positions = context.portfolio.positions[stock]
                    percentage = context.portfolio.positions[stock].value_percent

                    print(stock, instruments(stock).symbol, data[stock].close, '30分钟 4%止盈卖出')
                    close_position_2(positions, percentage)
                    context.black_list.append(stock)
                    context.stock_30.remove(stock)

            if stock in context.stock_15:
                #涨幅 2.5%
                if data[stock].close > context.portfolio.positions[stock].avg_price * 1.025:
                    positions = context.portfolio.positions[stock]
                    percentage = context.portfolio.positions[stock].value_percent

                    print(stock, instruments(stock).symbol, data[stock].close, '15分钟 2.5%止盈卖出')
                    close_position_2(positions, percentage)
                    context.black_list.append(stock)
                    context.stock_15.remove(stock)


    def __str__(self):
        return '股票调仓卖出规则：卖出不在buy_stocks的股票'
      
    
'''---------------买入股票规则 补足仓位--------------'''  
class Buy_stocks_position(Adjust_position):
    __name__='Buy_stocks'
    def __init__(self,params):
        self.buy_count = params.get('buy_count', 4)
    def update_params(self,context,params):
        self.buy_count = params.get('buy_count',self.buy_count)
    def adjust(self,context,data,buy_stocks):


        actual_position = context.portfolio.market_value / context.portfolio.portfolio_value

        if actual_position > context.position * 0.98:
            return

        #避免小额下单
        if context.portfolio.cash < 10000:
            return

        buy_stock_list = []

        stock_list_count = len(context.stock_list)

        for stock in context.stock_list:

            if stock in context.black_list:
                return

            #todo：盘前计算
            fiveday_avg = calc_5day(stock, data).tolist()
            fiveday_avg.reverse();

            if fiveday_avg[0]/fiveday_avg[1] > 0.99:
                if data[stock].close > fiveday_avg[0]:

                    createdic(context, data, stock)
                    if context.portfolio.positions[stock].value_percent * 1.05 < (context.position/self.buy_count):
                        self.open_position_by_percent(stock, (context.position/self.buy_count))
                        print('[Score 补仓买入]', instruments(stock).symbol, (context.position/self.buy_count), data[stock].close)

        pass
    def __str__(self):
        return '股票调仓买入规则：现金平分式买入股票达目标股票数'
        
'''---------------买入股票规则 按底部结构买入--------------'''  
class Buy_stocks_low(Adjust_position):
    __name__='Buy_stocks_low'
    def __init__(self,params):
        self.buy_count = params.get('buy_count', 4)
    def update_params(self,context,params):
        self.buy_count = params.get('buy_count',self.buy_count)
    def adjust(self,context,data,buy_stocks):
        # 买入股票
        # 始终保持持仓数目为g.buy_stock_count
        # 根据股票数量分仓
        # 此处只根据可用金额平均分配购买，不能保证每个仓位平均分配

        #开盘和尾盘不进行交易
        if context.timedelt < 15 or context.timedelt > 237:
            return

        #30分钟线进行交易
        if (context.timedelt % 5 >= 3) or (context.timedelt % 5 == 0): #and (context.timedelt % 60 <= 5):
            return

        for stock in buy_stocks:

            if stock in context.black_list:
                return

            #避免小额下单
            if context.portfolio.cash < 20000:
                return

            macd_df_60 = context.bar_60[stock]
            macd_df_30 = context.bar_30[stock]
            macd_df_15 = context.bar_15[stock]

            #if (context.portfolio.market_value / context.portfolio.portfolio_value) > context.position:
            #    return
                
            #构成买入条件
            if macd_df_60.iloc[-1]['bottom_buy'] == 1:

                createdic(context, data, stock)
                    
                if context.portfolio.positions[stock].value_percent * 1.1 < context.position/self.buy_count:
                    self.open_position_by_percent(stock, context.position/self.buy_count)

                    if stock not in context.stock_60:
                        context.stock_60.append(stock)

                    print('[60分钟 底部结构买入]', instruments(stock).symbol, context.position/self.buy_count)

            if macd_df_30.iloc[-1]['bottom_buy'] == 1:

                createdic(context, data, stock)
                    
                if context.portfolio.positions[stock].value_percent * 1.1 < (context.position/self.buy_count):
                    self.open_position_by_percent(stock, context.position/self.buy_count) 

                    if stock not in context.stock_30:
                        context.stock_30.append(stock)

                    print('[30分钟 底部结构买入]', instruments(stock).symbol, context.position/self.buy_count)

            if macd_df_15.iloc[-1]['bottom_buy'] == 1 and context.index_df.iloc[-1]['macd'] > 0:

                createdic(context, data, stock)
                    
                if context.portfolio.positions[stock].value_percent * 1.1 < (context.position/self.buy_count):
                    self.open_position_by_percent(stock, context.position/self.buy_count)

                    if stock not in context.stock_15:
                        context.stock_30.append(stock)

                    print('[15分钟 底部结构买入]', instruments(stock).symbol, context.position/self.buy_count)

            #else:
                #self.open_position_by_percent(stock, 1/buy_count)

        pass
    def __str__(self):
        return '股票调仓买入规则：现金平分式买入股票达目标股票数'

class Buy_stocks2(Adjust_position):
    __name__='Buy_stocks2'
    def __init__(self,params):
        self.buy_count = params.get('buy_count',3)
        #self.buy_position = params.get('buy_position', 0)
    def update_params(self,context,params):
        self.buy_count = params.get('buy_count',self.buy_count)
        #self.buy_position = params.get('buy_position', self.buy_position)
    def adjust(self,context,data,buy_stocks):
        # 买入股票
        # 始终保持持仓数目为g.buy_stock_count
        # 根据股票数量分仓
        # 此处只根据可用金额平均分配购买，不能保证每个仓位平均分配
        print(context.portfolio.cash, context.portfolio.market_value, context.portfolio.portfolio_value, context.position)

        if (context.portfolio.market_value / context.portfolio.portfolio_value) < context.position:
            self.buy_position = context.position - context.portfolio.market_value / context.portfolio.portfolio_value
            value = context.portfolio.portfolio_value * self.buy_position - context.portfolio.market_value
            buy_value = value / self.buy_count
            for stock in buy_stocks:
                self.open_position(stock, buy_value)

        pass
    def __str__(self):
        return '股票调仓买入规则：现金平分式买入股票达目标股票数'

def generate_portion(num):
    total_portion = num * (num+1) / 2
    start = num
    while num != 0:
        yield float(num) / float(total_portion)
        num -= 1
        