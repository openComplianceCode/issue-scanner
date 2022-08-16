# -*- coding: utf-8 -*-
from concurrent.futures import ThreadPoolExecutor
import json
import tornado.web
import tornado.ioloop
import tornado.httpserver
import tornado.options
from tornado.concurrent import run_on_executor
import config
from reposca.itemLicSca import ItemLicSca
from reposca.licenseCheck import LicenseCheck
from reposca.prSca import PrSca

from tornado import gen

from util.postOrdered import infixToPostfix

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
        prUrl = self.get_argument('prUrl')
        result = yield self.block(prUrl)
        self.finish(str(result))
    
    @run_on_executor
    def block(self, prUrl):
        prSca = PrSca()
        result = prSca.doSca(prUrl)
        jsonRe = json.dumps(result)
        return jsonRe
 
class LicSca(tornado.web.RequestHandler):
    executor = ThreadPoolExecutor(1000)

    @gen.coroutine
    def get(self):
        """get请求"""
        url = self.get_argument('repoUrl')    
        commit = self.get_argument('commit')
        result = yield self.block(url, commit)
        self.finish(str(result))

    @gen.coroutine
    def post(self):
        '''post请求'''
        url = self.get_argument('repoUrl')    
        commit = self.get_argument('commit')
        result = yield self.block(url, commit)
        self.finish(str(result))
    
    @run_on_executor
    def block(self, url, commit):
        itemLic = ItemLicSca()
        result = itemLic.licSca(url, commit)
        jsonRe = json.dumps(result)
        return jsonRe

application = tornado.web.Application([(r"/sca", Main), (r"/lic", LicSca),])

if __name__ == '__main__':
    httpServer = tornado.httpserver.HTTPServer(application)
    httpServer.bind(config.options["port"])   
    httpServer.start(1)
    tornado.ioloop.IOLoop.current().start()