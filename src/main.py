# -*- coding: utf-8 -*-
from concurrent.futures import ThreadPoolExecutor
import json
import os
import sys

import tornado.web
import tornado.ioloop
import tornado.httpserver
import tornado.options
from tornado.concurrent import run_on_executor
import config
from reposca.prSca import doSca

from tornado import gen

class Main(tornado.web.RequestHandler):
    executor = ThreadPoolExecutor(1000)

    @gen.coroutine
    def get(self):
        """get请求"""
        prUrl = self.get_argument('prUrl')
        result = yield self.block(prUrl)
        self.finish(str(result))

    @gen.coroutine
    def post(self):
        '''post请求'''
        body = self.request.body
        body_decode = body.decode()
        body_json = json.loads(body_decode)
        prUrl = body_json.get("prUrl")
        result = yield self.block(prUrl)
        self.finish(str(result))
    
    @run_on_executor
    def block(self, prUrl):
        result = doSca(prUrl)
        return result


application = tornado.web.Application([(r"/sca", Main), ])

if __name__ == '__main__':
    sys.path.append(os.path.dirname(sys.path[0]))

    httpServer = tornado.httpserver.HTTPServer(application)
 
    httpServer.bind(config.options["port"])      #绑定在指定端口
                        #全局的options对象，所有定义的选项变量都会作为该对象的属性
                        #这里就可以使用tornado.options.parse_command_line()保存的变量的值
    httpServer.start(1)
                                #默认（0）开启一个进程，否则对面开启数值（大于零）进程
                             #值为None，或者小于0，则开启对应硬件机器的cpu核心数个子进程
                            #例如 四核八核，就四个进程或者八个进程
    tornado.ioloop.IOLoop.current().start()
    # application.listen(8868)
    # tornado.ioloop.IOLoop.instance().start()
    
