from enum import Enum
config = {
    # 相机参数设置
    # cam 曝光时间
    'cameras': {
        # 相机数量
        'camNum': 6,

        # 曝光时间
        'exposetime': [50, 25, 8, 8, 8, 8],
        'exposetime_below': [3, 3, 8, 8, 8, 8],
        # 相机sn码
        'sns': [b'040082720156',
                b'040082720159',
                b'049061910333',
                b'',
                b'040041420209',
                b'049061910309',
                ],
        'roi': ((),
                (),
                (800, 2800, 1100, 1600),  # 拍摄区域,x0, x1, y0, y1
                (800, 2800, 1100, 1600),  # 拍摄区域,x0, x1, y0, y1
                (800, 2800, 1100, 1600),  # 拍摄区域,x0, x1, y0, y1
            ),
        # 白平衡,使用SDK工具一键白平衡后获取
        'gains': [[157,126,100],
                  [157,126,100],
                  [157,126,100],
                  [157,126,100],
                  [157,126,100],
                  [157,126,100],
                  ],
        'gain': [20, 15, 3, 3, 3, 3],
        # trigger_num:
        'trigger_num': [1, 1, 1, 1, 1, 1],
        'usb_cam': [True,
                     True,
                     True,
                     True,
                     True,
                     True
                    ],
        # show
        'show_realtime': [True,
                     True,
                     False,
                     False,
                     False,
                     False
                    ],
    },
    'plc_modbus': {
        'port': '/dev/ttyWCH1',
        'baudrate': 19200,
        'bytesize': 8,
        'parity': 'E',
        'stopbits': 1,
        'xonxoff': 0,
        'ip': '192.168.1.10'
    },
    'redis_params': {
            'IP': '127.0.0.1',
            'port': 6379,
            'password': '',
            'chan_sub': ''
    },
    'template_dir': '../template/',
    'DEBUG': False,
    'logging_full': False,
    'full_dir': '/home/ta/sdb2T/logs/full/',
    'roi_dir': '/home/ta/Downloads/logs/roi/',
    'log_dir': '/home/ta/Downloads/logs/logfiles/',
    'obj_dir': '/home/ta/sdb2T/logs/obj/',
    'defect_dir': '/home/ta/Downloads/logs/defect/',

    # match相关
    'linemod_root': 'linemod-gpu-master/',
    'mesh_template': '/home/ta/Downloads/template/707.pkl',
    'rough_template': '/home/ta/Downloads/template/707_rough.pkl',
    'time_diff': 0.3,
    'saved_wrong_info':True,
    'use_torch': True,  # 笔记本上跑torch以外的检测
    'ui_in_win': False,
    # PLC拉料速度
    'speed': 5, # 15
    # PLC每次拉料排数
    # 拉料指令起始地址
    'step_command_start_addr': 2000,
    'model_type': '624',

    # use local images as input
    'LOCAL_IMAGE': False,
    # 测试时，跑完所有的缺陷
    'ALL_DEFECTS': True,
    # 输出用于训练的图像
    'OUTPUT_TRAIN': False,
}

class DEFECTS(Enum):
    LIANGPIN = 0,'良品'
    MOPAO = 1,'膜泡'
    MOHUASHANG = 2,'膜划伤'
    MOQUE = 3,'膜缺'
    MOYASHANG = 4,'膜压伤'
    MAOCI = 5,'毛刺'
    ZANGWU = 6,'脏污'
    # WUKONG = 7,'孔异常'
    WUKONG = 7, '无孔'
    FANXIANG = 8,'反向'

    def __init__(self, key, desc):
        self._key = key
        self._desc = desc

    @property
    def desc(self):
        return self._desc

    @property
    def key(self):
        return self._key
