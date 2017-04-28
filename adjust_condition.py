# -*- coding:utf-8 -*- 

#from kuanke.user_space_api import *
from rule import *
from util import *
import pandas as pd

'''==============================调仓条件判断器基类=============================='''
class Adjust_condition(Rule):
    __name__='Adjust_condition'
    # 返回能否进行调仓
    @property
    def can_adjust(self):
        return True

''' ----------------------最高价最低价比例止损------------------------------'''
class Stop_loss_by_price(Adjust_condition):
    __name__='Stop_loss_by_price'
    def __init__(self,params):
        self.index = params.get('index','000001.XSHG')
        self.day_count = params.get('day_count',160)
        self.multiple = params.get('multiple',2.2)
        self.is_day_stop_loss_by_price = False
    def update_params(self,context,params):
        self.index = params.get('index',self.index)
        self.day_count = params.get('day_count',self.day_count)
        self.multiple = params.get('multiple',self.multiple)

    def handle_data(self,context, data):
        # 大盘指数前130日内最高价超过最低价2倍，则清仓止损
        # 基于历史数据判定，因此若状态满足，则当天都不会变化
        # 增加此止损，回撤降低，收益降低
    
        if not self.is_day_stop_loss_by_price:
            h = history_bars(self.index, self.day_count, '1d', ('close', 'high', 'low'))
            low_price_130 = h.low.min()
            high_price_130 = h.high.max()
            if high_price_130 > self.multiple * low_price_130 and h['close'][-1]<h['close'][-4]*1 and  h['close'][-1]> h['close'][-100]:
                # 当日第一次输出日志
                logger.info("==> 大盘止损，%s指数前130日内最高价超过最低价2倍, 最高价: %f, 最低价: %f" %(get_security_info(self.index).display_name, high_price_130, low_price_130))
                self.is_day_stop_loss_by_price = True
    
        if self.is_day_stop_loss_by_price:
            self.clear_position(context)

    def before_trading_start(self,context):
        self.is_day_stop_loss_by_price = False
        pass
    def __str__(self):
        return '大盘高低价比例止损器:[指数: %s] [参数: %s日内最高最低价: %s倍] [当前状态: %s]'%(
                self.index,self.day_count,self.multiple,self.is_day_stop_loss_by_price)
        
    @property
    def can_adjust(self):
        return not self.is_day_stop_loss_by_price

''' ----------------------三乌鸦止损------------------------------'''
class Stop_loss_by_3_black_crows(Adjust_condition):
    __name__='Stop_loss_by_3_black_crows'
    def __init__(self,params):
        self.index = params.get('index','000001.XSHG')
        self.dst_drop_minute_count = params.get('dst_drop_minute_count',60)
        # 临时参数
        self.is_last_day_3_black_crows = False
        self.t_can_adjust = True
        self.cur_drop_minute_count = 0
    def update_params(self,context,params):
        self.index = params.get('index',self.index )
        self.dst_drop_minute_count = params.get('dst_drop_minute_count',self.dst_drop_minute_count)
        
    def initialize(self,context):
        pass
    
    def handle_data(self,context, data):
        # 前日三黑鸦，累计当日每分钟涨幅<0的分钟计数
        # 如果分钟计数超过一定值，则开始进行三黑鸦止损
        # 避免无效三黑鸦乱止损
        if self.is_last_day_3_black_crows:
            if get_growth_rate(self.index, 1) < 0:
                self.cur_drop_minute_count += 1
    
            if self.cur_drop_minute_count >= self.dst_drop_minute_count:
                if self.cur_drop_minute_count == self.dst_drop_minute_count:
                    logger.info("==> 超过三黑鸦止损开始")
                
                self.clear_position(context)
                self.t_can_adjust = False
        else:
            self.t_can_adjust = True
        pass
    
    def before_trading_start(self,context):
        self.is_last_day_3_black_crows = is_3_black_crows(self.index)
        if self.is_last_day_3_black_crows:
            logger.info("==> 前4日已经构成三黑鸦形态")
        pass
    
    def after_trading_end(self,context):
        self.is_last_day_3_black_crows = False
        self.cur_drop_minute_count = 0
        pass
    
    def __str__(self):
        return '大盘三乌鸦止损器:[指数: %s] [跌计数分钟: %d] [当前状态: %s]'%(
            self.index,self.dst_drop_minute_count,self.is_last_day_3_black_crows)
        
    @property
    def can_adjust(self):
        return self.t_can_adjust

''' ----------------------28指数值实时进行止损------------------------------'''
class Stop_loss_by_28_index(Adjust_condition):
    __name__='Stop_loss_by_28_index'
    def __init__(self,params):
        self.index2 = params.get('index2','')
        self.index8 = params.get('index8','')
        self.index_growth_rate = params.get('index_growth_rate',0.01)
        self.dst_minute_count_28index_drop = params.get('dst_minute_count_28index_drop',120)
        # 临时参数
        self.t_can_adjust = True
        self.minute_count_28index_drop = 0
    def update_params(self,context,params):
        self.index2 = params.get('index2',self.index2)
        self.index8 = params.get('index8',self.index8)
        self.index_growth_rate = params.get('index_growth_rate',self.index_growth_rate)
        self.dst_minute_count_28index_drop = params.get('dst_minute_count_28index_drop',self.dst_minute_count_28index_drop)     
    def initialize(self,context):
        pass
    
    def handle_data(self,context, data):
        # 回看指数前20天的涨幅
        gr_index2 = get_growth_rate(self.index2)
        gr_index8 = get_growth_rate(self.index8)
    
        if gr_index2 <= self.index_growth_rate and gr_index8 <= self.index_growth_rate:
            if (self.minute_count_28index_drop == 0):
                logger.info("当前二八指数的20日涨幅同时低于[%.2f%%], %s指数: [%.2f%%], %s指数: [%.2f%%]" \
                    %(self.index_growth_rate*100, 
                    get_security_info(self.index2).display_name, 
                    gr_index2*100, 
                    get_security_info(self.index8).display_name, 
                    gr_index8*100))
    
            self.minute_count_28index_drop += 1
        else:
            # 不连续状态归零
            if self.minute_count_28index_drop < self.dst_minute_count_28index_drop:
                self.minute_count_28index_drop = 0
    
        if self.minute_count_28index_drop >= self.dst_minute_count_28index_drop:
            if self.minute_count_28index_drop == self.dst_minute_count_28index_drop:
                logger.info("==> 当日%s指数和%s指数的20日增幅低于[%.2f%%]已超过%d分钟，执行28指数止损" \
                    %(get_security_info(self.index2).display_name, get_security_info(self.index8).display_name, self.index_growth_rate*100, self.dst_minute_count_28index_drop))
    
            self.clear_position(context)
            self.t_can_adjust = False
        else:
            self.t_can_adjust = True
        pass
    
    def after_trading_end(self,context):
        self.t_can_adjust = False
        self.minute_count_28index_drop = 0
        pass
    
    def __str__(self):
        return '28指数值实时进行止损:[大盘指数: %s %s] [小盘指数: %s %s] [判定调仓的二八指数20日增幅 %.2f%%]'%(
                self.index2,self.index8,self.index_growth_rate * 100)
        
    @property
    def can_adjust(self):
        return self.t_can_adjust


'''-------------------------调仓时间控制器-----------------------'''
class Time_condition(Adjust_condition):
    __name__='Time_condition'
    def __init__(self,params):
        # 配置调仓时间（24小时分钟制）
        self.hour = params.get('hour',14)
        self.minute = params.get('minute',50)
    def update_params(self,context,params):
        self.hour = params.get('hour',self.hour)
        self.minute = params.get('minute',self.minute)
        pass
    @property   
    def can_adjust(self):
        return self.t_can_adjust

    def handle_data(self,context, data):
        hour = context.now.hour
        minute = context.now.minute
        self.t_can_adjust = hour >= self.hour and minute <= self.minute+10
        pass
    
    def __str__(self):
        return '调仓时间控制器: [调仓时间: %d:%d]'%(
                self.hour,self.minute)

'''-------------------------调仓日计数器-----------------------'''
class Period_condition(Adjust_condition):
    __name__='Period_condition'
    def __init__(self,params):
        # 调仓日计数器，单位：日
        self.period = params.get('period',3)
        self.day_count = 0
        self.t_can_adjust = False
        
    def update_params(self,context,params):
        self.period  = params.get('period',self.period )
        
    @property   
    def can_adjust(self):
        return self.t_can_adjust

    #todo:分钟线回测
    def handle_data(self,context, data):
        print ("调仓日计数 [%d]"%(self.day_count))
        self.t_can_adjust = self.day_count % self.period == 0

        print(context.today, context.now.date())

        if context.today != context.now.date():
            context.today = context.now.date()
            self.day_count += 1
        pass
    
    def before_trading_start(self,context):
        self.t_can_adjust = False
        pass
    def when_sell_stock(self,position,order,is_normal):
        if not is_normal: 
            # 个股止损止盈时，即非正常卖股时，重置计数，原策略是这么写的
            self.day_count = 0
        pass
    # 清仓时调用的函数
    def when_clear_position(self,context):
        self.day_count = 0
        pass
    
    def __str__(self):
        return '调仓日计数器:[调仓频率: %d日] [调仓日计数 %d]'%(
                self.period,self.day_count)
        
'''-------------------------28指数涨幅调仓判断器----------------------'''
class Index28_condition(Adjust_condition):
    __name__='Index28_condition'
    def __init__(self,params):
        self.index2 = params.get('index2','')
        self.index8 = params.get('index8','')
        self.index_growth_rate = params.get('index_growth_rate', 0.01)
        self.t_can_adjust = False
    
    def update_params(self,context,params):
        self.index2 = params.get('index2',self.index2)
        self.index8 = params.get('index8',self.index8)
        self.index_growth_rate = params.get('index_growth_rate',self.index_growth_rate)
        
    @property    
    def can_adjust(self):
        return self.t_can_adjust

    def handle_data(self,context, data):
        # 回看指数前20天的涨幅
        gr_index2 = get_growth_rate(self.index2)
        gr_index8 = get_growth_rate(self.index8)

        if gr_index2 <= self.index_growth_rate and gr_index8 <= self.index_growth_rate:
            self.clear_position(context)
            self.t_can_adjust = False
        else:
            self.t_can_adjust = True
        pass
    
    def before_trading_start(self,context):
        pass
    
    def __str__(self):
        return '28指数择时:[大盘指数:%s %s] [小盘指数:%s %s] [判定调仓的二八指数20日增幅 %.2f%%]'%(
                self.index2,instruments(self.index2).symbol,
                self.index8,instruments(self.index8).symbol,
                self.index_growth_rate * 100)

'''-------------------------当日大跌调仓判断器----------------------'''
class BigLost_condition(Adjust_condition):
    __name__='BigLost_condition'
    def __init__(self,params):
        self.index = params.get('index','')
        self.t_can_adjust = False
    
    def update_params(self,context,params):
        self.index = params.get('index',self.index)
        
    @property    
    def can_adjust(self):
        return self.t_can_adjust

    def handle_data(self,context, data):
        snapshot_index = current_snapshot(self.index)
        #logger.info("当前指数的跌幅 [%.2f%%]" %(1 - (snapshot_index.last / snapshot_index.prev_close)))

        if (snapshot_index.last / snapshot_index.prev_close) < (1 - 0.03):
            self.clear_position(context)
            self.t_can_adjust = False
        else:
            self.t_can_adjust = True
        pass
    
    def before_trading_start(self,context):
        pass
    
    def __str__(self):
        return '当前指数的跌幅调仓'

'''-------------------------MACD指数涨幅调仓判断器----------------------'''
class Index_MACD_condition(Adjust_condition):
    __name__='Index_MACD_condition'
    def __init__(self,params):
        self.index = params.get('index','')
        self.t_can_adjust = False
    
    def update_params(self,context,params):
        self.index = params.get('index',self.index)
        
    @property    
    def can_adjust(self):
        return self.t_can_adjust

    def handle_data(self,context, data):

        context.position = 0

        #日线
        if context.index_df.iloc[-1]['macd'] > 0:
            context.position = 1
        else:
            context.position = 1

        if context.position > 0:
            self.t_can_adjust = True
        else:
            self.clear_position(context)
            self.t_can_adjust = False

        return self.t_can_adjust
    
    def before_trading_start(self,context):
        
        pass
    '''
    def __str__(self):
        return '28指数择时:[大盘指数:%s %s] [小盘指数:%s %s] [判定调仓的二八指数20日增幅 %.2f%%]'%(
                self.index2,instruments(self.index2).symbol,
                self.index8,instruments(self.index8).symbol,
                self.index_growth_rate * 100)
    '''

