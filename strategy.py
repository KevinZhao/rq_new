#v0.3 2016-1-1 to 2017-2-5 回测收益 115.858

#思路：解决回撤的问题
#思路：解决开板之后的股票进入buy_stock的问题 Done
#思路: 对入围股票进行排名，新开板新股如果没有资金暂时不进入股票池
#前20天波动率

from rule import *
from adjust_condition import *
from filter_stock_list import *
from adjust_position import *
from filter_query import *
from util import *

'''选择规则组合成一个量化策略'''
def select_strategy():
    '''
    策略选择设置说明:
    策略由以下步骤规则组合，组合而成:
    1.持仓股票的处理规则
    2.调仓条件判断规则
    3.Query选股规则 (可选，有些规则可能不需要这个)
    4.股票池过滤规则 (可选，有些规则可能不需要这个)
    5.调仓规则
    6.其它规则(如统计)
    
    每个步骤的规则组合为一个二维数组
    一维指定由什么规则组成，注意顺序，程序将会按顺序创建，按顺序执行。
    不同的规则组合可能存在一定的顺序关系。
    二维指定具体规则配置，由 [0.是否启用，1.描述，2.规则实现类名，3.规则传递参数(dict)]] 组成。
    注：所有规则类都必需继承自Rule类或Rule类的子类
    '''
    # 规则配置list下标描述变量。提高可读性与未来添加更多规则配置。
    g.cs_enabled, g.cs_memo, g.cs_class_name, g.cs_param = range(4)
    
    # 0.是否启用，1.描述，2.规则实现类名，3.规则传递参数(dict)]
    # period = 3                                      # 调仓频率
    # 配置 1.持仓股票的处理规则 (这里主要配置是否进行个股止损止盈)
    g.position_stock_config = [
         #[False,'个股止损','Stop_loss_stocks_by_percentage',{
             #'percent':0.2                     # 调仓频率，日
             #},],
         #[False,'个股止盈','Stop_profit_stocks_by_percentage',{
             #'percent':0.15                     # 调仓频率，日
             #},],
         #[True,'个股止盈','Stop_profit_stocks',
             #{'period':period ,                  # 调仓频率，日
             #}]
    ]
        
    # 配置 2.调仓条件判断规则 
    g.adjust_condition_config = [
        # [False,'指数最高低价比值止损','Stop_loss_by_price',{
        #     'index':'000001.XSHG',                  # 使用的指数,默认 '000001.XSHG'
        #      'day_count':160,                       # 可选 取day_count天内的最高价，最低价。默认160
        #      'multiple':2.2                         # 可选 最高价为最低价的multiple倍时，触 发清仓
        #     }],
        # [False,'指数三乌鸦止损','Stop_loss_by_3_black_crows',{
        #     'index':'000001.XSHG',                  # 使用的指数,默认 '000001.XSHG'
        #      'dst_drop_minute_count':60,            # 可选，在三乌鸦触发情况下，一天之内有多少分钟涨幅<0,则触发止损，默认60分钟
        #     }],
        # [False,'28择时','Stop_loss_by_28_index',{
        #             'index2' : '000016.XSHG',       # 大盘指数
        #             'index8' : '399333.XSHE',       # 小盘指数
        #             'index_growth_rate': 0.01,      # 判定调仓的二八指数20日增幅
        #             'dst_minute_count_28index_drop': 120 # 符合条件连续多少分钟则清仓
        #         }],
        [True,'跌幅择时','BigLost_condition',{    # 该调仓条件可能会产生清仓行为
                 'index' : '399006.XSHE',       # 大盘指数
             }],
        [True,'调仓时间','Time_condition',{
                 'hour': 14,                    # 调仓时间,小时
                 'minute' : 00                   # 调仓时间，分钟
             }],
        [True,'28择时','Index28_condition',{    # 该调仓条件可能会产生清仓行为
                 'index2' : '000016.XSHG',       # 大盘指数
                 'index8' : '399006.XSHE',       # 小盘指数
                 'index_growth_rate': -0.04,      # 判定调仓的二八指数20日增幅
             }],
        #[False,'调仓日计数器','Period_condition',{
        #         'period' : 4,             # 调仓频率,日
        #     }],
        #[False,'Macd择时','Index_MACD_condition',{
        #         'index' : '000016.XSHG',             
        #     }],
    ]
        
    # 配置 3.Query选股规则
    g.pick_stock_by_query_config = [
        # [False,'选取小市值','Pick_small_cap',{}],
        [True,'选取流通小市值','Pick_small_circulating_market_cap',{}],
        # [False,'过滤PE','Filter_pe',{ 
        #     'pe_min':0                          # 最小PE
        #     ,'pe_max':200                       # 最大PE
        #     }],
        [True,'过滤流通市值','Filter_circulating_market_cap',{ 
            'cm_cap_min':0                          # 最小流通市值
            ,'cm_cap_max':3000000000                # 最大流通市值
            }],    
        # [False,'过滤EPS','Filter_eps',{
        #     'eps_min':0                         # 最小EPS
        #     }],
        [True,'初选股票数量','Filter_limite',{
            'pick_stock_count':50              # 备选股票数目
            }]
    ]
    
    # 配置 4.股票池过滤规则
    g.filter_stock_list_config = [
        #[False,'过滤创业板','Filter_gem',{}],
        #[False,'过滤ST','Filter_st',{}],
        #[True,'过滤停牌','Filter_paused_stock',{}],
        [True,'过滤涨停,不过滤持仓股','Filter_limitup',{}],
        [True,'过滤上市超过一定时间的股票','Filter_old_stock',{
            'day_count':200                     # 超过多少天
            }],
        [True,'过滤新开板','Filter_just_open_limit',{}],
        #[True,'当日跌幅超过一定比例','Filter_drop_percentage',{
            #'drop_percent':-0.06                     # 超过多少天
            #}],
        # [False,'过滤跌停,不过滤持仓股','Filter_limitdown',{}],
        #[False,'过滤涨跌停,持仓股也过滤','Filter_limit_up_and_down',{}],
        # [False,'过滤n日增长率为负的股票','Filter_growth_is_down',{
        #     'day_count':20                      # 判断多少日内涨幅
        #     }],
        # [False,'过滤黑名单','Filter_blacklist',{}],
        # [False,'股票评分','Filter_rank',{
        #     'rank_stock_count': 20              # 评分股数
        #     }],
        
        [True,'获取最终选股数','Filter_buy_count',{
            'buy_count': 5                    # 最终入选股票数
            }],
    ]
        
    # 配置 5.调仓规则
    g.adjust_position_config = [
        # [False,'卖出股票','Sell_stocks',{}],
        [True,'卖出不在Buy_stocks且未涨停的股票','Sell_stocks2',{}],
        [True,'买入股票','Buy_stocks',{
            'buy_count': 4                     # 最终买入股票数
            }]                     
    ]
    
    # 配置 6.其它规则
    g.other_config = [
        [True,'统计','Stat',{}]
    ]

# 创建一个规则执行器，并初始化一些通用事件
def create_rule(class_name,params):
    '''
    在这借用eval函数，把规则配置里的字符串类名实例化。
    eval函数说明：将字符串当成有效Python表达式来求值，并返回计算结果
    x = 1
    y = eval('x+1')
    则结果为 y==2
    '''
    obj = eval(class_name)(params)
    obj.open_position_by_percent = open_position_by_percent
    obj.on_open_position = open_position
    obj.on_close_position = close_position
    obj.on_clear_position = clear_position
    return obj
    
# 根据规则配置创建规则执行器
def create_rules(config):
    # config里 0.是否启用，1.描述，2.规则实现类名，3.规则传递参数(dict)]
    return [create_rule(c[g.cs_class_name],c[g.cs_param]) for c in config if c[g.cs_enabled]]

def init(context):
    context.stock_count = 0
    context.today = None
    context.stock_list = None
    context.stock_to_buy = None

    select_strategy()
    '''-----1.持仓股票的处理规则:-----'''
    g.position_stock_rules = create_rules(g.position_stock_config)

    '''-----2.调仓条件判断规则:-----'''
    g.adjust_condition_rules = create_rules(g.adjust_condition_config)

    '''-----3.Query选股规则:-----'''
    g.pick_stock_by_query_rules = create_rules(g.pick_stock_by_query_config)

    '''-----4.股票池过滤规则:-----'''
    g.filter_stock_list_rules = create_rules(g.filter_stock_list_config)
    
    '''-----5.调仓规则:器-----'''
    g.adjust_position_rules = create_rules(g.adjust_position_config)
    
    '''-----6.其它规则:-------'''
    g.other_rules = create_rules(g.other_config)
    
    # 把所有规则合并排重生成一个总的规则收录器。以方便各处共同调用的
    g.all_rules = list(set(g.position_stock_rules 
            + g.adjust_condition_rules
            + g.pick_stock_by_query_rules
            + g.filter_stock_list_rules
            + g.adjust_position_rules
            + g.other_rules
        ))
        
    for rule in g.all_rules:
        rule.initialize(context)

    # 打印规则参数
    log_param()

def before_trading(context):
    logger.info("==========================================================================")
    for rule in g.all_rules:
        rule.before_trading_start(context)

def handle_bar(context, bar_dict):
    
    data = bar_dict

    # 执行其它辅助规则
    for rule in g.other_rules:
        rule.handle_data(context,data)

    # 持仓股票动作的执行,目前为个股止损止盈
    for rule in g.position_stock_rules:
        rule.handle_data(context,data)

    # ----------这部分当前本策略其实并没有啥用，扩展用--------------
    # 这里执行选股器调仓器的handle_data主要是为了扩展某些选股方式可能需要提前处理数据。
    # 举例：动态获取黑名单，可以调仓前一段时间先执行。28小市值规则这里都是空动作。
    #for rule in g.pick_stock_by_query_rules:
    #    rule.handle_data(context,data)
    
    #for rule in g.filter_stock_list_rules:
    #    rule.handle_data(context,data)
    
    # 调仓器的分钟处理
    #for rule in g.adjust_position_rules:
    #    rule.handle_data(context,data)
    # -----------------------------------------------------------
    
    # 判断是否满足调仓条件，所有规则以and 逻辑执行
    for rule in g.adjust_condition_rules:
        rule.handle_data(context,data)
        if not rule.can_adjust:
            return
    # ---------------------调仓--------------------------
    #logger.info("==> 满足条件进行调仓")
    # 调仓前预处理
    #for rule in g.all_rules:
    #    rule.before_adjust_start(context,data)
    
    # Query 选股
    q = None
    for rule in g.pick_stock_by_query_rules:
        q = rule.filter(context,data,q)
    
    # 过滤股票列表
    stock_list = list(get_fundamentals(q).columns.values)
    for rule in g.filter_stock_list_rules:
        stock_list = rule.filter(context,data,stock_list)
        
    #logger.info("选股后可买股票: %s" %(stock_list))
    
    # 执行调仓
    for rule in g.adjust_position_rules:
        rule.adjust(context,data,stock_list)
    
    # 调仓后处理
    for rule in g.all_rules:
        rule.after_adjust_end(context,data)
    # ----------------------------------------------------
    
    plot('postion', context.stock_count)

def after_trading(context):
    for rule in g.all_rules:
        rule.after_trading_end(context)
    
    # 得到当前未完成订单
    orders = get_open_orders()
    for _order in orders.values():
        logger.info("canceled uncompleted order: %s" %(_order.order_id))

def log_param():
    def get_rules_str(rules):
        return '\n'.join(['   %d.%s '%(i+1,str(r)) for i,r in enumerate(rules)]) + '\n'
    s = '\n---------------------策略一览：规则组合与参数----------------------------\n'
    s += '一、持仓股票的处理规则:\n'  + get_rules_str(g.position_stock_rules)
    s += '二、调仓条件判断规则:\n'    + get_rules_str(g.adjust_condition_rules)
    s += '三、Query选股规则:\n'       + get_rules_str(g.pick_stock_by_query_rules)
    s += '四、股票池过滤规则:\n'      + get_rules_str(g.filter_stock_list_rules)
    s += '五、调仓规则:\n'            + get_rules_str(g.adjust_position_rules)
    s += '六、其它规则:\n'            + get_rules_str(g.other_rules)
    s += '--------------------------------------------------------------------------'
    print (s)
