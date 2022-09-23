# -*- coding: utf-8 -*-
import logging
import os
import shlex
import stat
import subprocess
import time
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
SOURTH_PATH = '/home/repo/persistentRepo'
TEMP_PATH = '/home/repo/tempRepo'
LIC_COP_LIST = ['license', 'readme', 'notice', 'copying', 'third_party_open_source_software_notice', 'copyright']
logging.getLogger().setLevel(logging.INFO)

class PrSca(object):

    @catch_error
    def doSca(self, url):
        try:
            delSrc = ''
            urlList = url.split("/")
            self._owner_ = urlList[3]
            self._repo_ = urlList[4]
            self._num_ = urlList[6]
            self._branch_ = 'pr_' + self._num_
            gitUrl = GIT_URL + '/' + self._owner_ + '/' + self._repo_ + '.git'
            fetchUrl = 'pull/' + self._num_ + '/head:pr_' + self._num_
            timestemp = int(time.time())
            tempSrc = self._repo_ + str(timestemp)

            if os.path.exists(TEMP_PATH) is False:
                os.makedirs(TEMP_PATH)

            self._repoSrc_ = SOURTH_PATH + '/'+self._owner_ + '/' + self._repo_
            self._anlyzeSrc_ = SOURTH_PATH + '/'+self._owner_
           
            self._file_ = 'sourth'
            if os.path.exists(self._repoSrc_):
                try:
                    perRepo = Repo.init(path=self._repoSrc_)
                    perRemote = perRepo.remote()
                    perRemote.pull()
                    #copy file
                    tempDir = TEMP_PATH + '/'+self._owner_ + '/' + tempSrc + '/' + self._repo_
                    os.makedirs(TEMP_PATH + '/'+self._owner_ + '/' + tempSrc)
                    command = shlex.split('cp -r %s  %s' % (self._repoSrc_, tempDir))
                    resultCode = subprocess.Popen(command)
                    while subprocess.Popen.poll(resultCode) == None:
                        time.sleep(1)
                    popKill(resultCode)
                    self._repoSrc_ = tempDir
                except Exception as e:
                    self._file_ = 'temp'
                    self._repoSrc_ = TEMP_PATH + '/'+self._owner_ + '/' + tempSrc + '/' + self._repo_               
                    if os.path.exists(self._repoSrc_) is False:
                        os.makedirs(self._repoSrc_)
                    pass  
            else:     
                self._file_ = 'temp'
                self._repoSrc_ = TEMP_PATH + '/'+self._owner_ + '/' + tempSrc + '/' + self._repo_               
                if os.path.exists(self._repoSrc_) is False:
                    os.makedirs(self._repoSrc_)
            self._anlyzeSrc_ = TEMP_PATH + '/' + self._owner_ + '/' + tempSrc
            delSrc = TEMP_PATH + '/'+self._owner_ + '/' + tempSrc

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
            #获取PR增量文件目录
            fileList =  self.getDiffFiles()
            self._sca_path_ = []        
            for diff_added in fileList:
                self._sca_path_.append(diff_added['filename'])
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
                # maxDepth = 3

            logging.info("=============Start scan repo==============")           
            # 调用scancode
            licInList = ("* --include=*").join(LIC_COP_LIST)
            command = shlex.split(
                'scancode -l -c %s --max-depth %s --json %s -n 4 --timeout 10 --max-in-memory -1 \
                    --license-score 80 --only-findings --include=*%s*' % (self._repoSrc_, maxDepth, tempJson, licInList))
            resultCode = subprocess.Popen(command)
            while subprocess.Popen.poll(resultCode) == None:
                time.sleep(1)
            popKill(resultCode)
            itemJson = ''
            # 获取json
            with open(tempJson, 'r+') as f:
                list = f.readlines()
                itemJson = "".join(list)

            inclList = (" --include=*/").join(self._sca_path_)
            collectDepth = self.getDepth()
            command = shlex.split(
                'scancode -l -c %s --max-depth %s --json %s -n 4 --timeout 10 --max-in-memory -1 \
                    --license-score 80 --only-findings --include=*/%s' % (self._repoSrc_, collectDepth, tempJson, inclList))
            resultCode = subprocess.Popen(command)
            while subprocess.Popen.poll(resultCode) == None:
                time.sleep(1)
            popKill(resultCode)

            scaJson = ''
            # 获取json
            with open(tempJson, 'r+') as f:
                list = f.readlines()
                scaJson = "".join(list)
            
            reJson = self.mergJson(itemJson, scaJson)
            logging.info("=============End scan repo==============")

        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.exception("Error on %s" % (e))
        finally:
            # 清空文件
            os.chmod(tempJson, stat.S_IWUSR)
            os.remove(tempJson)
            return reJson

    @catch_error
    def rmExtract(self, path):
        pathList = path.split("/")

        for item in pathList:
            if '-extract' in item:
                pathList.remove(item)
                break

        return "/".join(pathList)
    
    @catch_error
    def getDiffFiles(self):
        fileList = []
        repoStr = "Flag"
        http = urllib3.PoolManager()            
        url = 'https://gitee.com/api/v5/repos/'+self._owner_+'/'+self._repo_+'/pulls/'+ self._num_ +'/files?access_token='+ACCESS_TOKEN
        response = http.request('GET',url)         
        resStatus = response.status

        if resStatus == 403:
            raise Exception('Token 权限问题')
        
        if resStatus == 404:
            raise Exception("Gitee API Fail")

        repoStr = response.data.decode('utf-8')
        temList = json.loads(repoStr)
        fileList.extend(temList)     
        return fileList
    
    @catch_error
    def mergJson(self,itemJson, scaJson):
        itemData = json.loads(itemJson)
        scaData = json.loads(scaJson)
        itemDateFile = itemData['files']
        scaDataFile = scaData['files']
        reData = scaDataFile
        if len(scaDataFile) > 0:
            scaPath = jsonpath.jsonpath(scaData, '$.files[*].path')
            for item in itemDateFile:
                if item['path'] not in scaPath:
                    reData.append(item)
        else:
            reData = itemDateFile
        reJson = {
            "files": reData
        }
        return json.dumps(reJson)

    @catch_error
    def getDepth(self):
        maxDepth = 0
        for item in self._sca_path_:
            pathLevel = item.split("/")
            if len(pathLevel) > maxDepth:
                maxDepth = len(pathLevel)
            
        return maxDepth
