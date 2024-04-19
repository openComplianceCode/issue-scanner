# -*- coding: utf-8 -*-
import calendar
from concurrent.futures import ThreadPoolExecutor
import json
import time
import tornado.web
import tornado.ioloop
import tornado.httpserver
import tornado.options
from tornado.concurrent import run_on_executor
from reposca.analyzeSca import copyright_check
import config
from reposca.fixSca import fixSca
from reposca.itemLicSca import ItemLicSca
from reposca.queryBoard import QueryBoard
from reposca.queryMeasure import QueryMeasure
from reposca.prSca import PrSca
from reposca.resonseSca import ResonseSca
from reposca.licenseCheck import LicenseCheck
from tornado import gen
from reposca.scheduleSca import ScheduleSca
from reposca.tempSca import TempSca
from util.scheduleUtil import Scheduler
from util.postOrdered import infixToPostfix
from datetime import datetime, timedelta
exitFlag = 0
class Main(tornado.web.RequestHandler):
    executor = ThreadPoolExecutor(1000)

    @gen.coroutine
    def get(self):
        """get request"""
        self.set_header('Content-Type', 'application/json; charset=UTF-8')
        prUrl = self.get_argument('prUrl')
        result = yield self.block(prUrl)
        self.finish(str(result))

    @gen.coroutine
    def post(self):
        '''post request'''
        self.set_header('Content-Type', 'application/json; charset=UTF-8')
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
        """get request"""
        self.set_header('Content-Type', 'application/json; charset=UTF-8')
        url = self.get_argument('purl')
        url = json.loads(url)
        result = yield self.block(url)
        self.finish(result)

    @gen.coroutine
    def post(self):
        '''post request'''
        self.set_header('Content-Type', 'application/json; charset=UTF-8')
        url = self.get_argument('purl')    
        url = json.loads(url)
        result = yield self.block(url)
        self.finish(result)
    
    @run_on_executor
    def block(self, url):
        itemLic = ItemLicSca()
        result = itemLic.scaPurl(url)
        jsonRe = json.dumps(result)
        return jsonRe
    
class ItemSca(tornado.web.RequestHandler):
    executor = ThreadPoolExecutor(1000)

    @gen.coroutine
    def get(self):
        """get request"""
        self.set_header('Content-Type', 'application/json; charset=UTF-8')
        url = self.get_argument('url')
        asyn = self.get_argument('async','False')
        resp = self.get_argument('resp','')
        para = self.get_argument('para','')
        if asyn == "True":
            self.finish(json.dumps({"result":True,"notice": "scanning..."}))
            result = yield self.block(url)
            if resp:
                respon = ResonseSca(resp, para, result, url)
                respon.httpReq()
        else:
            result = yield self.block(url)
            self.finish(result)

    @gen.coroutine
    def post(self):
        '''post request'''
        self.set_header('Content-Type', 'application/json; charset=UTF-8')
        url = self.get_argument('url')  
        asyn = self.get_argument('async','False')  
        resp = self.get_argument('resp','')
        para = self.get_argument('para','')
        if asyn == "True":
            self.finish(json.dumps({"result":True,"notice": "scanning..."}))
            result = yield self.block(url)
            if resp:
                respon = ResonseSca(resp, para, result, url)
                respon.httpReq()
        else:
            result = yield self.block(url)
            self.finish(result)
    
    @run_on_executor
    def block(self, url):      
        itemLic = ItemLicSca()
        result = itemLic.licSca(url)
        jsonRe = json.dumps(result)
        return jsonRe
    

class Query(tornado.web.RequestHandler):
    executor = ThreadPoolExecutor(1000)

    @gen.coroutine
    def get(self):
        """get request"""
        self.set_header('Content-Type', 'application/json; charset=UTF-8')
        tag = self.get_argument('tag')
        org = self.get_argument('org','')
        repo = self.get_argument('repo','')
        result = yield self.block(tag, org, repo)
        self.finish(result)

    @gen.coroutine
    def post(self):
        '''post request'''
        self.set_header('Content-Type', 'application/json; charset=UTF-8')
        tag = self.get_argument('tag')
        org = self.get_argument('org','')
        repo = self.get_argument('repo','')
        result = yield self.block(tag, org, repo)
        self.finish(result)
    
    @run_on_executor
    def block(self, tag, org, repo):      
        boardQuery = QueryBoard()
        result = boardQuery.query(tag, org, repo)
        jsonRe = json.dumps(result)
        return jsonRe

class Check(tornado.web.RequestHandler):
    executor = ThreadPoolExecutor(1000)

    @gen.coroutine
    def get(self):
        """get request"""
        self.set_header('Content-Type', 'application/json; charset=UTF-8')
        license = self.get_argument('license')
        result = yield self.block(license)
        self.finish(result)

    @gen.coroutine
    def post(self):
        '''post request'''
        self.set_header('Content-Type', 'application/json; charset=UTF-8')
        license = self.get_argument('license')
        result = yield self.block(license)
        self.finish(result)
    
    @run_on_executor
    def block(self, license):      
        licCheck = LicenseCheck('repo', 'indelic')
        result = licCheck.check_admittance(license)
        jsonRe = json.dumps(result)
        return jsonRe
    
class Query_Measure(tornado.web.RequestHandler):
    executor = ThreadPoolExecutor(1000)

    @gen.coroutine
    def get(self):
        """get request"""
        self.set_header('Content-Type', 'application/json; charset=UTF-8')
        tag = self.get_argument('tag')
        org = self.get_argument('org','')
        repo = self.get_argument('repo','')
        dataMonth = self.get_argument('date','')
        result = yield self.block(tag, org, repo, dataMonth)
        self.finish(result)

    @gen.coroutine
    def post(self):
        '''post request'''
        self.set_header('Content-Type', 'application/json; charset=UTF-8')
        tag = self.get_argument('tag')
        org = self.get_argument('org','')
        repo = self.get_argument('repo','')
        dataMonth = self.get_argument('date','')
        result = yield self.block(tag, org, repo, dataMonth)
        self.finish(result)
    
    @run_on_executor
    def block(self, tag, org, repo, dataMonth):      
        measure_query = QueryMeasure()
        result = measure_query.query(tag, org, repo, dataMonth)
        jsonRe = json.dumps(result)
        return jsonRe


application = tornado.web.Application([
    (r"/sca", Main), 
    (r"/lic", LicSca), 
    (r"/doSca", ItemSca), 
    (r"/board", Query),
    (r"/check", Check),
    (r"/measure", Query_Measure)
    ])

if __name__ == '__main__':
    # schedOb = Scheduler()
    httpServer = tornado.httpserver.HTTPServer(application)
    httpServer.bind(config.options["port"])   
    httpServer.start(1)
    tornado.ioloop.IOLoop.current().start()