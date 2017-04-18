# -*- coding:utf-8 -*- 

#from kuanke.user_space_api import *
from rule import *
from util import *


'''==============================个股止盈止损规则=============================='''

'''-----------------------个股止损 by pct_change------------------------------'''
class Stop_loss_stocks(Rule):
    __name__='Stop_loss_stocks'
    # get_period_func 为获取period的函数,无传入参数，传出参数为period
    # on_close_position_func 卖出股票时触发的事件，传入参数为 stock,无返回
    def __init__(self,params):
        self.last_high = {}
        self.period = params.get('period',3)
        self.pct_change = {}
    def update_params(self,context,params):
        self.period = params.get('period',self.period)
        
    # 个股止损
    def handle_data(self,context, data):
        for stock in context.portfolio.positions.keys():
            cur_price = data[stock].close
            xi = history_bars(stock, 2, '1d', 'high')
            ma = xi.max()
            if self.last_high[stock] < cur_price:
                self.last_high[stock] = cur_price

            threshold = self.__get_stop_loss_threshold(stock, self.period)
            #logger.debug("个股止损阈值, stock: %s, threshold: %f" %(stock, threshold))
            if cur_price < self.last_high[stock] * (1 - threshold):
                #logger.info("==> 个股止损, stock: %s, cur_price: %f, last_high: %f, threshold: %f" 
                #   %(stock, cur_price, self.last_high[stock], threshold))
    
                position = context.portfolio.positions[stock]
                self.close_position(position,False)
    
    # 获取个股前n天的m日增幅值序列
    # 增加缓存避免当日多次获取数据
    def __get_pct_change(self,security, n, m):
        pct_change = None
        if security in self.pct_change.keys():
            pct_change = self.pct_change[security]
        else:
            h = history_bars(security, n, '1d', 'close')
            pct_change = h['close'].pct_change(m) # 3日的百分比变比（即3日涨跌幅）
            self.pct_change[security] = pct_change
        return pct_change
        
    # 计算个股回撤止损阈值
    # 即个股在持仓n天内能承受的最大跌幅
    # 算法：(个股250天内最大的n日跌幅 + 个股250天内平均的n日跌幅)/2
    # 返回正值
    def __get_stop_loss_threshold(self,security, n = 3):
        pct_change = self.__get_pct_change(security, 250, n)
        #logger.debug("pct of security [%s]: %s", pct)
        maxd = pct_change.min()
        #maxd = pct[pct<0].min()
        avgd = pct_change.mean()
        #avgd = pct[pct<0].mean()
        # maxd和avgd可能为正，表示这段时间内一直在增长，比如新股
        bstd = (maxd + avgd) / 2
    
        # 数据不足时，计算的bstd为nan
        if not isnan(bstd):
            if bstd != 0:
                return abs(bstd)
            else:
                # bstd = 0，则 maxd <= 0
                if maxd < 0:
                    # 此时取最大跌幅
                    return abs(maxd)
    
        return 0.099 # 默认配置回测止损阈值最大跌幅为-9.9%，阈值高貌似回撤降低

    def when_sell_stock(self,position,order,is_normal):
        if position.security in self.last_high:
            self.last_high.pop(position.security)
        pass
    
    def when_buy_stock(self,stock,order):
        if order.status == OrderStatus.held and order.filled == order.amount:
            # 全部成交则删除相关证券的最高价缓存
            self.last_high[stock] = get_close_price(stock, 1, '1m')
        pass
    
    def after_trading_end(self,context):
        self.pct_change = {}
        pass
                
    def __str__(self):
        return '个股止损器:[当前缓存价格数: %d ]'%(len(self.__last_high))
        
''' ----------------------个股止盈 by pct_change------------------------------'''
class Stop_profit_stocks(Rule):
    __name__='Stop_profit_stocks'
    def __init__(self,params):
        self.last_high = {}
        self.period = params.get('period',3)
        self.pct_change = {}
    def update_params(self,context,params):
        self.period = params.get('period',self.period)    
    # 个股止盈
    def handle_data(self,context, data):
        for stock in context.portfolio.positions.keys():
                position = context.portfolio.positions[stock]
                cur_price = data[stock].close
                threshold = self.__get_stop_profit_threshold(stock, self.period)
                #logger.debug("个股止盈阈值, stock: %s, threshold: %f" %(stock, threshold))
                if cur_price > position.avg_cost * (1 + threshold):
                    #logger.info("==> 个股止盈, stock: %s, cur_price: %f, avg_cost: %f, threshold: %f" 
                    #    %(stock, cur_price, self.last_high[stock], threshold))
        
                    position = context.portfolio.positions[stock]
                    self.close_position(position,False)

    # 获取个股前n天的m日增幅值序列
    # 增加缓存避免当日多次获取数据
    def __get_pct_change(self,security, n, m):
        pct_change = None
        if security in self.pct_change.keys():
            pct_change = self.pct_change[security]
        else:
            h = history_bars(security, n, '1d', 'close')
            pct_change = h['close'].pct_change(m) # 3日的百分比变比（即3日涨跌幅）
            self.pct_change[security] = pct_change
        return pct_change
    
    # 计算个股止盈阈值
    # 算法：个股250天内最大的n日涨幅
    # 返回正值
    def __get_stop_profit_threshold(self,security, n = 3):
        pct_change = self.__get_pct_change(security, 250, n)
        maxr = pct_change.max()
        
        # 数据不足时，计算的maxr为nan
        # 理论上maxr可能为负
        if (not isnan(maxr)) and maxr != 0:
            return abs(maxr)
        return 0.30 # 默认配置止盈阈值最大涨幅为30%
    
    def when_sell_stock(self,position,order,is_normal):
        if order.status == OrderStatus.held and order.filled == order.amount:
            # 全部成交则删除相关证券的最高价缓存
            if position.security in self.last_high:
                self.last_high.pop(position.security)
        pass
    
    def when_buy_stock(self,stock,order):
        self.last_high[stock] = get_close_price(stock, 1, '1m')
        pass
    
    def after_trading_end(self,context):
        self.pct_change = {}
        pass
    def __str__(self):
        return '个股止盈器:[当前缓存价格数: %d ]'%(len(self.__last_high))

''' ----------------------个股止损 by 比例-------------------------------------'''
class Stop_loss_stocks_by_percentage(Rule):
    __name__='Stop_loss_stocks_by_percentage'

    def __init__(self,params):
        self.percent = params.get('percent', 0.05)
        #self.last_high = {}
        #self.pct_change = {}
    def update_params(self,context,params):
        self.percent = params.get('percent', self.period)
        
    # 个股止损
    def handle_data(self,context, data):
        for stock in context.portfolio.positions.keys():
            cur_price = data[stock].close
            #xi = history_bars(stock, 2, '1d', 'high')
            #ma = xi.max()
            #if self.last_high[stock] < cur_price:
            #    self.last_high[stock] = cur_price

            #threshold = self.__get_stop_loss_threshold(stock, self.period)
            #logger.debug("个股止损阈值, stock: %s, threshold: %f" %(stock, threshold))
            if cur_price < context.portfolio.positions[stock].avg_price * (1 - self.percent):
                #logger.info("==> 个股止损, stock: %s, cur_price: %f, last_high: %f, threshold: %f" 
                #   %(stock, cur_price, self.last_high[stock], threshold))
    
                position = context.portfolio.positions[stock]
                self.close_position(position, False)

                logger.debug("==> 个股止损, stock: %s, cur_price: %f" %(stock, cur_price))

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

''' ----------------------个股止赢 by 比例-------------------------------------'''
class Stop_profit_stocks_by_percentage(Rule):
    __name__='Stop_profit_stocks_by_percentage'

    def __init__(self,params):
        self.percent = params.get('percent', 0.02)
        #self.last_high = {}
        #self.pct_change = {}
    def update_params(self,context,params):
        self.percent = params.get('percent', self.percent)
        
    # 个股止损
    def handle_data(self,context, data):

        #print('called')
        for stock in context.portfolio.positions.keys():
            cur_price = data[stock].close
            if cur_price > context.portfolio.positions[stock].avg_price * (1 + self.percent):
                position = context.portfolio.positions[stock]
                if position.sellable > 0:
                    
                    close_position_2(position, False)
                    logger.debug("==> 个股止盈, stock: %s, cur_price: %f" %(stock, cur_price))
                    pass
        #print('called')
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
        return '个股止损器:[按比例止赢: %d ]' %self.percent

''' ----------------------个股止损 by ATR-------------------------------------'''
class Stop_loss_stocks_by_ATR(Rule):
    __name__='Stop_loss_stocks_by_ATR'

    def __init__(self,params):
        pass
    def update_params(self,context,params):
        pass
    # 个股止损
    def handle_data(self, context, data):

        for stock in context.ATRList:

            if stock in context.portfolio.positions.keys() and context.portfolio.positions[stock].quantity > 0: #and stock not in context.stock_list:

                ATR = findATR_60(context, stock)

                high = context.bar_60[stock].iloc[-1]['high']
                current = context.bar_60[stock].iloc[-1]['close']
                stockdic = context.maxvalue[stock]
                highest = stockdic[0]

                del context.maxvalue[stock]        
                temp = pd.DataFrame({str(stock):[max(highest,high)]})

                context.maxvalue= pd.concat([context.maxvalue, temp], axis=1, join='inner') # 更新其盘中最高价值和先阶段比例。
        
                if data[stock].last < highest - 3*ATR:
                
                    print(str(stock)+'的成本为：' +str( context.portfolio.positions[stock].average_cost) +', 最高价为：'+str(highest)+'ATR为：'+ str(ATR) + '当前价格为: ' + str(data[stock].last))
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

'''---------------卖出股票规则--------------'''  
     
class Sell_stocks(Adjust_position):
    __name__='Sell_stocks'
    def adjust(self,context,data,buy_stocks):
        
        for stock in context.portfolio.positions.keys():
            if context.portfolio.positions[stock].quantity == 0:
                return

            if data[stock].close < context.portfolio.positions[stock].avg_price * 1.05:
                if data[stock].close < context.portfolio.positions[stock].avg_price * 0.92:

                    position = context.portfolio.positions[stock]
                    self.close_position(position)
                    context.black_list.append(stock)

            else:
                if stock not in context.ATRList: #and data[stock].close > context.portfolio.positions[stock].avg_price * 1.04:
                    context.ATRList.append(stock)

    def __str__(self):
        return '股票调仓卖出规则：卖出不在buy_stocks的股票'


'''---------------卖出股票规则2--------------'''       
class Sell_stocks2(Adjust_position):
    __name__='Sell_stocks2'
    def adjust(self,context,data,buy_stocks):

        # 现持仓的股票，如果不在“目标池”中，且未涨停，卖出
        if len(context.portfolio.positions) > 0:
            for stock in context.portfolio.positions.keys():

                if stock not in buy_stocks:
                #if data[stock].close < current_snapshot(stock).prev_close*1.005:
                    position = context.portfolio.positions[stock]
                    self.close_position(position)

                #else:
                    #logger.debug("Sell_stocks2 stock [%s] 无需卖出" %(stock))
    def __str__(self):
        return '股票调仓卖出规则：卖出不在buy_stocks且未涨停的的股票'        
    
'''---------------买入股票规则--------------'''  
class Buy_stocks(Adjust_position):
    __name__='Buy_stocks'
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
        if context.timedelt < 60 or context.timedelt > 237:
            return

        #60分钟线进行交易
        if (context.timedelt % 60 >= 5) or (context.timedelt % 60 == 0): #and (context.timedelt % 60 <= 5):
            return

        #股票打分    
        stock_score(context)

        for stock in buy_stocks:

            if stock in context.black_list:
                return

            #避免小额下单
            if context.portfolio.cash < 20000:
                return

            #构成买入条件
            if context.score_df[stock].iloc[-1]['close'] > (context.score_df[stock].iloc[-2]['close'] * 0.98) and (context.score_df[stock].iloc[-1]['close'] < context.score_df[stock].iloc[-2]['close'] * 1.04):
                
                #计算买入数量
                #print('现金占比', context.portfolio.cash / context.portfolio.portfolio_value)

                #if context.portfolio.cash / context.portfolio.portfolio_value > 1 / self.buy_count:
                    #print(context.portfolio.portfolio_value * 1 / self.buy_count / data[stock].close)


                createdic(context, data, stock)
                    
                if context.portfolio.positions[stock].value_percent * 1.1 < 1/self.buy_count:
                    self.open_position_by_percent(stock, 1/self.buy_count)
            #else:
                #self.open_position_by_percent(stock, 1/buy_count)

        pass
    def __str__(self):
        return '股票调仓买入规则：现金平分式买入股票达目标股票数'
'''---------------买入股票规则--------------'''  
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



        if context.timedelt < 30 or context.timedelt > 237:
            return

        #30分钟线进行交易
        if (context.timedelt % 30 >= 5) or (context.timedelt % 30 == 0): #and (context.timedelt % 60 <= 5):
            return

        #股票打分    
        #stock_score(context)

        for stock in buy_stocks:

            if stock in context.black_list:
                return

            #避免小额下单
            if context.portfolio.cash < 20000:
                return

            macd_df_60 = context.bar_60[stock]
            macd_df_30 = context.bar_30[stock]

            #print(macd_df)

            #构成买入条件
            if macd_df_60.iloc[-1]['bottom_buy'] == 1:

                createdic(context, data, stock)
                    
                if context.portfolio.positions[stock].value_percent * 1.1 < 1/self.buy_count:
                    self.open_position_by_percent(stock, 1/self.buy_count)

            if macd_df_30.iloc[-1]['bottom_buy'] == 1:

                createdic(context, data, stock)
                    
                if context.portfolio.positions[stock].value_percent * 1.1 < 0.5/self.buy_count:
                    self.open_position_by_percent(stock, 0.5/self.buy_count)
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

'''---------------买入股票规则--------------'''  
class Buy_stocks_30m(Adjust_position):
    __name__='Buy_stocks_30m'
    def __init__(self,params):
        self.buy_count = params.get('buy_count',3)
        self.buy_signal = False
    def update_params(self,context,params):
        self.buy_count = params.get('buy_count',self.buy_count)
    def adjust(self,context,data, buy_stocks):
        # 买入股票
        # 始终保持持仓数目为g.buy_stock_count
        # 根据股票数量分仓
        # 此处只根据可用金额平均分配购买，不能保证每个仓位平均分配

        #周期分钟线生成
        #print('called')
        for stock in buy_stocks:
            if context.timedelt % 15 >= 1 and context.timedelt % 15 <= 3: #and context.now.hour != 9:

                #15分钟K线 MACD值，出现金叉买入
                if (context.bar_15[stock].iloc[-1]['diff'] > context.bar_15[stock].iloc[-1]['dea']) and (context.bar_15[stock].iloc[-2]['dea'] > context.bar_15[stock].iloc[-2]['diff']):

                    self.buy_signal = True
                    
                    #30分钟线diff大于dea，或者diff下降值小于前值的一定比例
                    if (context.bar[stock].iloc[-1]['diff'] > context.bar[stock].iloc[-1]['dea']) or (context.bar[stock].iloc[-1]['diff']/context.bar[stock].iloc[-2]['diff'] <= 1.01):

                        #60分钟线买入判断
                        if (context.bar_60[stock].iloc[-1]['diff'] > context.bar_60[stock].iloc[-1]['dea']) or (context.bar_60[stock].iloc[-1]['diff']/context.bar_60[stock].iloc[-2]['diff'] <= 1.01):

                            if context.bar_15[stock].iloc[-1]['close'] / context.bar_15[stock].iloc[-2]['close'] >= 1.01:
                                if context.portfolio.cash > 10000:
                                    createdic(context, data, stock)
                                    if context.portfolio.positions[stock].value_percent + 1/self.buy_count <= 1/self.buy_count:

                                        #print(context.bar_60[stock].iloc[-1]['diff'], context.bar_60[stock].iloc[-2]['diff'])

                                        self.open_position_by_percent(stock, context.portfolio.positions[stock].value_percent + 1/self.buy_count)

                    #else:
                    #    self.open_position_by_percent(stock, 0.6)
        #print('called')
        pass
    def __str__(self):
        return '股票调仓买入规则：现金平分式买入股票达目标股票数'

def generate_portion(num):
    total_portion = num * (num+1) / 2
    start = num
    while num != 0:
        yield float(num) / float(total_portion)
        num -= 1
        
class Buy_stocks_portion(Adjust_position):
    def __init__(self,params):
        self.buy_count = params.get('buy_count',3)
    def update_params(self,context,params):
        self.buy_count = params.get('buy_count',self.buy_count)
    def adjust(self,context,data,buy_stocks):
        # 买入股票
        # 始终保持持仓数目为g.buy_stock_count
        # 根据股票数量分仓
        # 此处只根据可用金额平均分配购买，不能保证每个仓位平均分配
        position_count = len(context.portfolio.positions)
        if self.buy_count > position_count:
            buy_num = self.buy_count - position_count
            portion_gen = generate_portion(buy_num)
            available_cash = context.portfolio.cash
            for stock in buy_stocks:
                if context.portfolio.positions[stock].quantity == 0:
                    buy_portion = portion_gen.next()
                    value = available_cash * buy_portion
                    if self.open_position(stock, value):
                        if len(context.portfolio.positions) == self.buy_count:
                            break
        pass
    def __str__(self):
        return '股票调仓买入规则：现金比重式买入股票达目标股票数'  