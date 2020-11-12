# -*- coding: utf-8 -*-
# @Project: SAT654
# @Author: zhangxianshun
# @File name: global_singleton
# @Create time: 2020-07-30 21:48

from multiprocessing import Queue
from config import config
import redis


class GolbalSingleton(object):
    __instance = None
    __first_init = True
    redis_db = None
    names = locals()
    for i in range(config['cameras']['camNum']):
        names['obj_queue_' + str(i)] = Queue()

    def __init__(self):
        if self.__first_init:
            self.__first_init = False
            self.show_queue = Queue()
            self.ret_queue = Queue()
            self.capture_queue = Queue()
            self.chan_sub = config['redis_params']['chan_sub']
            # self.conn_redis()

    def __new__(cls, *args, **kwargs):
        if not cls.__instance:
            cls.__instance = object.__new__(cls)
        return cls.__instance

    def publish(self, info):
        """
        发布消息
        将内容发布到频道
        """
        if self.redis_db is None:
            self.conn_redis()
        self.redis_db.publish(self.chan_sub, info)
        return True

    def subscribe(self):
        if self.redis_db is None:
            self.conn_redis()
        pub = self.redis_db.pubsub()
        pub.subscribe(self.chan_sub)
        pub.parse_response()
        return pub

    def conn_redis(self):
        self.redis_db = redis.Redis(
            connection_pool=redis.ConnectionPool(host=config['redis_params']['IP'],
                                                 password=config['redis_params']['password'],
                                                 port=config['redis_params']['port'],
                                                 decode_responses=True,
                                                 db=0))
        return self.redis_db