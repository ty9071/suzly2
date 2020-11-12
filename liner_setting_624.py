# 料带相关设置
from enum import Enum
# scale = 150
liner = {
    # 'track_anchor': 'liner',  # 根据lienr还是洞做定位，637， 691是liner，681是洞
    'x_range': (740, 5250),  # 左右两边的范围
    # 'y_range': (100, 3400),  # 上下两边范围
    # 'mid_xy': (2915, 1903),
    # # 'y1': 1724,
    # 'width': 1324,
    # # 'time_diff': 0.2, # 没两片之间的间隔时间
    # # 'match_score': 0.7, # 第一次模板匹配的阈值
    # 'blue_diff': 60, # 提取liner时的阈值，样机阈值70
    # # 'mid_y': (500, 2000), # 中间区域模板匹配能出现的位置
}
