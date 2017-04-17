# -*- coding:utf-8 -*- 

#from kuanke.user_space_api import *
from rule import *
from util import *


'''==============================选股 query过滤器基类=============================='''
class Filter_query(Rule):
    __name__='Filter_query'
    def filter(self,context,data,q):
        return None

'''------------------小市值选股器-----------------'''
class Pick_small_cap(Filter_query):
    __name__='Pick_small_cap'
    def filter(self,context,data,q):
        return query(
                fundamentals.eod_derivative_indicator.market_cap
                ).order_by(
                fundamentals.eod_derivative_indicator.market_cap.asc()
                )
    def __str__(self):
        return '按总市值倒序选取股票'
        
class Pick_small_circulating_market_cap(Filter_query):
    
    __name__='Pick_small_circulating_market_cap'

    def filter(self,context,data,q):
        return query(
                fundamentals.eod_derivative_indicator.a_share_market_val_2
                ).order_by(
                fundamentals.eod_derivative_indicator.a_share_market_val_2.asc()
                )
    
    def __str__(self):
        return '按流通市值倒序选取股票'
        
class Filter_pe(Filter_query):
    __name__='Filter_pe'
    def __init__(self,params):
        self.pe_min = params.get('pe_min',0)
        self.pe_max = params.get('pe_max',200)
        
    def update_params(self,context,params):
        self.pe_min = params.get('pe_min',self.pe_min)
        self.pe_max = params.get('pe_max',self.pe_max)
        
    def filter(self,context,data,q):
        return q.filter(
                fundamentals.eod_derivative_indicator.pe_ratio_2 > self.pe_min,
                fundamentals.eod_derivative_indicator.pe_ratio_2 < self.pe_max
                )
    def __str__(self):
        return '根据动态PE范围选取股票： [ %d < pe < %d]'%(self.pe_min, self.pe_max)
 
class Filter_circulating_market_cap(Filter_query):
    __name__='Filter_market_cap'
    def __init__(self,params):
        self.cm_cap_min = params.get('cm_cap_min', 0)
        self.cm_cap_max = params.get('cm_cap_max', 10000000000)

    def update_params(self,context,params):
        self.cm_cap_min = params.get('cm_cap_min',self.cm_cap_min)
        self.cm_cap_max = params.get('cm_cap_max',self.cm_cap_max)

    def filter(self,context,data,q):
        return q.filter(
                fundamentals.eod_derivative_indicator.a_share_market_val_2 <= self.cm_cap_max,
                fundamentals.eod_derivative_indicator.a_share_market_val_2 >= self.cm_cap_min
                )

    def __str__(self):
        return '根据流通市值范围选取股票： [ %d < circulating_market_cap < %d]'%(self.cm_cap_min,self.cm_cap_max)        
    
class Filter_limite(Filter_query):
    __name__='Filter_limite'
    def __init__(self,params):
        self.pick_stock_count = params.get('pick_stock_count',0)
    def update_params(self,context,params):
        self.pick_stock_count = params.get('pick_stock_count', self.pick_stock_count)
    def filter(self,context,data,q):
        return q.limit(self.pick_stock_count)
    def __str__(self):
        return '初选股票数量: %d'%(self.pick_stock_count)
