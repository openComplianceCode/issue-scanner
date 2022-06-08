# -*- coding: utf-8 -*-
from concurrent.futures import ThreadPoolExecutor
import json
import os
import sys
import time

import tornado.web
import tornado.ioloop
import tornado.httpserver
import tornado.options
from tornado.concurrent import run_on_executor
import config
from reposca.licenseCheck import LicenseCheck
from reposca.prSca import PrSca

from tornado import gen

from util.postOrdered import infixToPostfix

class Main(tornado.web.RequestHandler):
    executor = ThreadPoolExecutor(1000)

    @gen.coroutine
    def get(self):
        """get请求"""
        # prUrl = self.get_argument('prUrl')
        # result = yield self.block(prUrl)
        license = self.get_argument('license')    
        type = self.get_argument('type')
        result = yield self.block(license, type)
        self.finish(str(result))

    @gen.coroutine
    def post(self):
        '''post请求'''
        body = self.request.body
        body_decode = body.decode()
        body_json = json.loads(body_decode)
        # prUrl = body_json.get("prUrl")
        # result = yield self.block(prUrl)
        license = body_json.get('license')    
        type = body_json.get('type')
        result = yield self.block(license, type)
        self.finish(str(result))
    
    @run_on_executor
    def block(self, license, type):
        # prSca = PrSca()
        # result = prSca.doSca(prUrl)
        licenseCheck = LicenseCheck(type)
        licenses = infixToPostfix(license)
        result = licenseCheck.check_license_safe(licenses)
        return result


application = tornado.web.Application([(r"/sca", Main), ])

if __name__ == '__main__':

    httpServer = tornado.httpserver.HTTPServer(application)
    httpServer.bind(config.options["port"])   
    httpServer.start(1)
    tornado.ioloop.IOLoop.current().start()
    
