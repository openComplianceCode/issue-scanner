# -*- coding: utf-8 -*-
import logging
import os
import shlex
import stat
import subprocess
import time
from requests import head
import urllib3
import json
import jsonpath
from reposca.analyzeSca import getScaAnalyze
from reposca.takeRepoSca import cleanTemp
from util.popUtil import popKill
from util.extractUtil import extractCode
from util.formateUtil import formateUrl
from util.catchUtil import catch_error

from git.repo import Repo

ACCESS_TOKEN = '694b8482b84b3704c70bceef66e87606'
GIT_URL = 'https://gitee.com'
SOURTH_PATH = '/home/giteeFile'
logging.getLogger().setLevel(logging.INFO)

class PrSca(object):

    def __init__(self):
        self._current_dir_ = os.path.dirname(os.path.abspath(__file__))

    @catch_error
    def doSca(self, url):
        try:
            urlList = url.split("/")
            self._owner_ = urlList[3]
            self._repo_ = urlList[4]
            self._num_ = urlList[6]
            self._branch_ = 'pr_' + self._num_
            gitUrl = GIT_URL + '/' + self._owner_ + '/' + self._repo_ + '.git'
            fetchUrl = 'pull/' + self._num_ + '/head:pr_' + self._num_
            timestamp = int(time.time())

            # 创建临时文件
            temFileSrc = self._current_dir_+'/tempSrc'
            temFileSrc = formateUrl(temFileSrc)

            if os.path.exists(temFileSrc) is False:
                os.makedirs(temFileSrc)

            self._repoSrc_ = SOURTH_PATH + '/'+self._owner_ + '/' + self._repo_
            self._anlyzeSrc_ = SOURTH_PATH + '/'+self._owner_
            delSrc = ''
            self._file_ = 'sourth'
            if os.path.exists(self._repoSrc_) is False:
                self._file_ = 'temp'
                self._repoSrc_ = temFileSrc + '/'+self._owner_ + '/' + str(timestamp) + '/' + self._repo_
                self._anlyzeSrc_ = temFileSrc + '/' + self._owner_ + '/' + str(timestamp)
                delSrc = temFileSrc + '/'+self._owner_ + '/' + str(timestamp)
                if os.path.exists(self._repoSrc_) is False:
                    os.makedirs(self._repoSrc_)

            repo = Repo.init(path=self._repoSrc_)
            self._gitRepo_ = repo
            self._git_ = repo.git

            logging.info("=============Start fetch repo==============")
            # 拉取pr
            if self._file_ == 'sourth':
                remote = self._gitRepo_.remote()
            else:
                remote = self._gitRepo_.create_remote('origin', gitUrl)
            remote.fetch(fetchUrl, depth=1)
            # 切换分支
            self._git_.checkout(self._branch_)
            logging.info("=============End fetch repo==============")

            # 扫描pr文件
            scaJson = self.getPrSca()
            scaResult = getScaAnalyze(scaJson, self._anlyzeSrc_, self._owner_)
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.exception("Error on %s" % (e))
        finally:
            # 清理临时文件
            if delSrc != '':
                try:
                    cleanTemp(delSrc)
                    os.chmod(delSrc, stat.S_IWUSR)
                    os.rmdir(delSrc)
                except:
                    pass
            return scaResult

    @catch_error
    def getPrBranch(self):
        '''
        :param owner: 仓库所属空间地址(企业、组织或个人的地址path)
        :param repo: 仓库路径(path)
        :param number: 	第几个PR，即本仓库PR的序数
        :return:head,base
        '''
        repoStr = "Flag"
        apiJson = ''
        http = urllib3.PoolManager()
        url = 'https://gitee.com/api/v5/repos/' + self._owner_ + '/' + \
            self._repo_ + '/pulls/' + self._num_ + '?access_token='+ACCESS_TOKEN
        response = http.request('GET', url)
        resStatus = response.status

        while resStatus == '403':
            return 403, 403

        while resStatus == '502':
            return 502, 502

        repoStr = response.data.decode('utf-8')
        apiJson = json.loads(repoStr)

        head = jsonpath.jsonpath(apiJson, '$.head.ref')
        base = jsonpath.jsonpath(apiJson, '$.base.ref')

        return head, base

    @catch_error
    def getPrSca(self):
        '''
        :param repoSrc: 扫描项目路径
        :param pathList: 扫描文件路径List
        :return:扫描结果json
        '''
        try:
            temJsonSrc = self._current_dir_+'/tempJson'
            temJsonSrc = formateUrl(temJsonSrc)
            if os.path.exists(temJsonSrc) is False:
                os.makedirs(temJsonSrc)

            timestamp = int(time.time())
            tempJson = temJsonSrc + '/' + self._repo_+str(timestamp)+'.txt'
            tempJson = formateUrl(tempJson)
            if os.path.exists(tempJson) is False:
                open(tempJson, 'w')

            reExt = extractCode(self._repoSrc_)
            if reExt is False:
                logging.error("file extracCode error")

            logging.info("=============Start scan repo==============")
            # 调用scancode
            command = shlex.split(
                'scancode -l -c %s --max-depth 3 --json %s -n 2 --timeout 10 --max-in-memory -1 --license-score 80 --only-findings' % (self._repoSrc_, tempJson))
            resultCode = subprocess.Popen(command)
            while subprocess.Popen.poll(resultCode) == None:
                time.sleep(1)
            popKill(resultCode)

            if self._file_ == 'sourth':
                # 切回master
                self._git_.checkout('master')
                # 删除临时分支
                self._git_.branch('-D', self._branch_)

            scaJson = ''
            # 获取json
            with open(tempJson, 'r+') as f:
                list = f.readlines()
                scaJson = "".join(list)
            logging.info("=============End scan repo==============")

        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.exception("Error on %s: %s" % (command, e))
        finally:
            # 清空文件
            os.chmod(tempJson, stat.S_IWUSR)
            os.remove(tempJson)

            return scaJson

    @catch_error
    def rmExtract(self, path):
        pathList = path.split("/")

        for item in pathList:
            if '-extract' in item:
                pathList.remove(item)
                break

        return "/".join(pathList)
