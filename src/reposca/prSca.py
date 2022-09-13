# -*- coding: utf-8 -*-
import logging
import os
import shlex
import shutil
import stat
import subprocess
import time
from requests import head
import urllib3
import json
import jsonpath
<<<<<<< Updated upstream
=======
from reposca.repoDb import RepoDb
>>>>>>> Stashed changes
from reposca.analyzeSca import getScaAnalyze
from reposca.takeRepoSca import cleanTemp
from util.popUtil import popKill
from util.extractUtil import extractCode
from util.formateUtil import formateUrl
from util.catchUtil import catch_error
from git.repo import Repo

ACCESS_TOKEN = '694b8482b84b3704c70bceef66e87606'
GIT_URL = 'https://gitee.com'
SOURTH_PATH = 'D:/persistentRepo'
TEMP_PATH = 'D:/tempRepo'
passRepoList = ['kernel','bishengjdk','gcc']
logging.getLogger().setLevel(logging.INFO)

class PrSca(object):

    def __init__(self):
        #连接数据库
        self._dbObject_ = RepoDb(
            host_db = os.environ.get("MYSQL_HOST"), 
            user_db = os.environ.get("MYSQL_USER"), 
            password_db = os.environ.get("MYSQL_PASSWORD"), 
            name_db = os.environ.get("MYSQL_DB_NAME"), 
            port_db = int(os.environ.get("MYSQL_PORT")))

    @catch_error
    def doSca(self, url):
        try:
            delSrc = ''
            urlList = url.split("/")
            self._owner_ = urlList[3]
            self._repo_ = urlList[4]
            #过滤
            for item in passRepoList:
                repoLow = self._repo_.lower()
                if item in repoLow:
                    scaResult = {
                        "repo_license_legal": {
                            "pass": True,
                            "result_code": "",
                            "notice": '',
                            "is_legal": {
                                "pass": True,
                                "license": [],
                                "notice": "",
                                "detail": {}
                            }
                        },
                        "spec_license_legal": {
                            "pass": True,
                            "result_code": "",
                            "notice": "",
                            "detail": {}
                        },
                        "license_in_scope": {
                            "pass": True,
                            "result_code": "",
                            "notice": ""
                        },
                        "repo_copyright_legal": {
                            "pass": True,
                            "result_code": "",
                            "notice": "",
                            "copyright": []
                        }
                    }
                    return scaResult
            self._num_ = urlList[6]
            self._branch_ = 'pr_' + self._num_
            gitUrl = GIT_URL + '/' + self._owner_ + '/' + self._repo_ + '.git'
            fetchUrl = 'pull/' + self._num_ + '/head:pr_' + self._num_
            timestamp = int(time.time())

            if os.path.exists(TEMP_PATH) is False:
                os.makedirs(TEMP_PATH)

            self._repoSrc_ = SOURTH_PATH + '/'+self._owner_ + '/' + self._repo_
            self._anlyzeSrc_ = SOURTH_PATH + '/'+self._owner_
           
            self._file_ = 'sourth'
            if os.path.exists(self._repoSrc_):
                perRepo = Repo.init(path=self._repoSrc_)
                perRemote = perRepo.remote()
                perRemote.pull()
                #copy file
                tempDir = TEMP_PATH + '/'+self._owner_ + '/' + str(timestamp) + '/' + self._repo_
                shutil.copytree(self._repoSrc_, tempDir)
                self._repoSrc_ = tempDir              
            else:     
                self._file_ = 'temp'           
                self._repoSrc_ = TEMP_PATH + '/'+self._owner_ + '/' + str(timestamp) + '/' + self._repo_               
                if os.path.exists(self._repoSrc_) is False:
                    os.makedirs(self._repoSrc_)
            self._anlyzeSrc_ = TEMP_PATH + '/' + self._owner_ + '/' + str(timestamp)
            delSrc = TEMP_PATH + '/'+self._owner_ + '/' + str(timestamp)

            repo = Repo.init(path=self._repoSrc_)
            self._gitRepo_ = repo
            self._git_ = repo.git

            logging.info("=============Start fetch repo==============")
            # 拉取pr
            oBr = "master"
            if self._file_ == 'sourth':
                remote = self._gitRepo_.remote()
                branches = self._gitRepo_.branches
                oBr = branches[0].name
            else:
                remote = self._gitRepo_.create_remote('origin', gitUrl)
            remote.fetch(fetchUrl, depth=1)
            # 切换分支
            
            self._git_.checkout(self._branch_)
            curCommit = self._gitRepo_.index
            diffR = curCommit.diff(oBr)
            for diff_added in diffR:
                print(diff_added.a_path)
            logging.info("=============End fetch repo==============")

            # 扫描pr文件
            scaJson = self.getPrSca()
            scaResult = getScaAnalyze(scaJson, self._anlyzeSrc_, self._type_)
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
            temJsonSrc = TEMP_PATH +'/tempJson'
            temJsonSrc = formateUrl(temJsonSrc)
            if os.path.exists(temJsonSrc) is False:
                os.makedirs(temJsonSrc)

            timestamp = int(time.time())
            tempJson = temJsonSrc + '/' + self._repo_+str(timestamp)+'.txt'
            tempJson = formateUrl(tempJson)
            if os.path.exists(tempJson) is False:
                open(tempJson, 'w')

            self._type_ = "inde"#自研
            maxDepth = 2
            reExt = extractCode(self._repoSrc_)
            if reExt == "Except":
                logging.error("file extracCode error")
            elif reExt == "ref":
                self._type_ = "ref"#引用仓
                maxDepth = 3

            logging.info("=============Start scan repo==============")
            # 调用scancode
            command = shlex.split(
                'scancode -l -c %s --max-depth %s --json %s -n 4 --timeout 10 --max-in-memory -1 --license-score 80 --only-findings' % (self._repoSrc_, maxDepth, tempJson))
            resultCode = subprocess.Popen(command)
            while subprocess.Popen.poll(resultCode) == None:
                time.sleep(1)
            popKill(resultCode)

            scaJson = ''
            # 获取json
            with open(tempJson, 'r+') as f:
                list = f.readlines()
                scaJson = "".join(list)
            logging.info("=============End scan repo==============")

        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.exception("Error on %s" % (e))
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
