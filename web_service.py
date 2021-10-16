#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@License :   (C)Copyright 2017-2018, Liugroup-NLPR-CASIA
@Time    :   2021/10/15 07:58:43
@Contact :   noaghzil@gmail.com
@Desc    :   tornado websocket
'''

# here put the import lib
import time
import json
import gzip
import tornado
import tornado.web
import tornado.ioloop
import tornado.websocket
from tornado.options import define, options

define("port", default=6158, help="port to listen on")


def valid_json(json_str):
    try:
        data = json.loads(json_str)
        return data
    except:
        return json_str


class WSPob():

    connector = {}  # 连接备忘录

    def user_connect(self, user):
        if user not in self.connector:
            self.connector[user] = dict(count=0, ping=None)

    def user_remove(self, user):
        self.connector.pop(user)

    def trigger(self, message):
        ''' 向所有被记录的客户端推送最新内容 '''
        for user in self.connector:
            self.connector[user]["cnt"].write_message(message)

    def get_ping_data(self, data):
        ping_dic = {'ping': data}
        ping_json = json.dumps(ping_dic)
        ping_byte = bytes(ping_json, encoding='utf-8')
        ping_gzip = gzip.compress(ping_byte)
        return ping_byte

    def beatping(self):
        print('beatping')
        print(f"{self.connector}")
        timestamp = round(time.time() * 1000)
        ping_data = self.get_ping_data(timestamp)
        for user in self.connector:
            user.write_message(ping_data, binary=True)
            self.connector[user]['ping'] = timestamp
            if self.connector[user]['count'] == 2:
                user.close()
            else:
                self.connector[user]['count'] += 1

    def alive_user(self, user, msg):
        # 满足条件，即重置对应user_times
        if self.connector[user]['ping'] == msg['pong']:
            self.connector[user]['count'] = 0
        else:
            print(f"invaild pong msg: {msg}")


one = WSPob()


class ReceiveHandler(tornado.web.RequestHandler):
    def get(self):
        msg = self.get_argument('msg', '')
        one.trigger(msg)  # 接收到消息之后推送


class EchoWebSocket(tornado.websocket.WebSocketHandler):
    def check_origin(self, origin):
        '''重写同源检查 解决跨域问题'''
        return True

    def open(self):
        '''新的websocket连接后被调动'''
        one.user_connect(self)  #用户连接后记录
        print("WebSocket opened")

    def on_message(self, message):
        '''接收到客户端消息时被调用'''
        # self.write_message(u"You said: " + message)
        print(type(message))
        if type(message) == bytes:
            message = bytes.decode(message, encoding="utf-8")
        message = valid_json(message)
        print(type(message))
        print(message)
        # 若 pong 存在，则表示该请求用于测试连接
        if 'pong' in message:
            one.alive_user(self, message)

    def on_close(self):
        '''websocket连接关闭后被调用'''
        print("WebSocket closed")
        one.user_remove(self)  # 断开连接后remove


def make_app():
    return tornado.web.Application([
        (r"/pushing", ReceiveHandler),
        (r"/websocket", EchoWebSocket),
    ])


if __name__ == "__main__":
    app = make_app()
    app.listen(options.port)
    # start scheduler 每隔5s执行一次心跳包
    tornado.ioloop.PeriodicCallback(one.beatping, 5000).start()
    tornado.ioloop.IOLoop.current().start()
