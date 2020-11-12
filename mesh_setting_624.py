# scale = 150
mesh = {
    'bin_thresh': 130,  # 钢网二值化阈值
    'radis': 60,
    'kernel_size': 3,
    'area_thresh': 6126,
    # 'bin_thresh_side': { # 侧位相机的二值化阈值
    #     1: 50,
    #     2: 70,
    # },
    # 'jiao_thresh': 60, # 样机
    #'jiao_thresh': 80,
    # 'bao_thresh': 60, # 样机系统,60
    # #'bao_thresh': 60,
    # 'bianxing_threh': 17, # 变形上下沿阈值，越小越严格, 建议17
    # 'bao_radis': 105, # 凸包半径, 90, 85
    # 'bao_edge_top': (0.70, 1.1),  # 钢网大小边阈值，上边，包低的一侧, 0.63, 0.75
    # 'bao_edge_but': (0.80, 1.1),  # 钢网大小边阈值，下边，包高的一侧, 0.84, 0.96
    # 'bao_edge_right': (0.71, 0.92),  # 钢网大小边阈值，右侧， 0.69, 0.81
    # 'bao_edge_left': (0.71, 0.92),  # 钢网大小边阈值，左侧 0.71, 0.83
    # 'bao_pad': 15, # 钢网大小边，小边的阈值，越大越严格, 13, 17, redias是85的时候，18会有很多误检, 15
    # 'bao_pad_big': 300, # 钢网大小边，大边阈值，越小越严格
    # 'hole_thresh': 10, # 堵孔阈值，越小越严格, 16
}



