# -*- coding: utf-8 -*-
import logging
import os
import shlex
import stat
import subprocess
import time
import pymysql
import urllib3
import json
import jsonpath
from reposca.analyzeSca import getScaAnalyze
from reposca.takeRepoSca import cleanTemp
from reposca.repoDb import RepoDb
from util.authApi import AuthApi
from util.popUtil import popKill
from util.extractUtil import extractCode
from util.formateUtil import formateUrl
from util.catchUtil import catch_error
from git.repo import Repo

ACCESS_TOKEN = '694b8482b84b3704c70bceef66e87606'
GIT_URL = 'https://gitee.com'
SOURTH_PATH = '/home/repo/persistentRepo'
TEMP_PATH = '/home/repo/tempRepo'
LIC_COP_LIST = ['license', 'readme', 'notice', 'copying', 'third_party_open_source_software_notice', 'copyright', '.spec']
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
            self._prUrl_ = url
            urlList = url.split("/")
            self._owner_ = urlList[3]
            self._repo_ = urlList[4]
            self._num_ = urlList[6]
            self._branch_ = 'pr_' + self._num_
            self._gitUrl_ = GIT_URL + '/' + self._owner_ + '/' + self._repo_ + '.git'
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

            logging.info("=============START FETCH REPO==============")          
            # 拉取pr
            if self._file_ == 'sourth':
                remote = self._gitRepo_.remote()
            else:
                remote = self._gitRepo_.create_remote('origin', self._gitUrl_)
            remote.fetch(fetchUrl, depth=1)
            # 切换分支
            self._git_.checkout(self._branch_)
            #获取PR增量文件目录
            fileList =  self.getDiffFiles()           
            #创建diff副本
            self._diffPath_ = self.createDiff(fileList)
            logging.info("==============END FETCH REPO===============")
            
            # 扫描pr文件
            scaJson = self.getPrSca()
            scaResult = getScaAnalyze(scaJson, self._anlyzeSrc_, self._type_)
            # Save Data
            self.savePr(scaResult, scaJson)
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.exception("Error on %s" % (e))
        finally:
            # 清理临时文件
            if delSrc != '':
                try:
                    cleanTemp(delSrc)
                    cleanTemp(self._diffPath_)
                    os.chmod(delSrc, stat.S_IRWXU)
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
            logging.info("============START EXTARCT CODE=============")
            reExt = extractCode(self._repoSrc_)
            logging.info("=============END EXTARCT CODE==============")
            if reExt == "Except":
                logging.error("file extracCode error")
            elif reExt == "ref":
                self._type_ = "ref"#引用仓
                # maxDepth = 3

            logging.info("==============START SCAN REPO==============")        
            # 调用scancode
            licInList = ("* --include=*").join(LIC_COP_LIST)
            command = shlex.split(
                'scancode -l -c %s --max-depth %s --json %s -n 4 --timeout 10 --max-in-memory -1 \
                    --license-score 80 --include=*%s*' % (self._repoSrc_, maxDepth, tempJson, licInList))
            resultCode = subprocess.Popen(command)
            while subprocess.Popen.poll(resultCode) == None:
                time.sleep(1)
            popKill(resultCode)
            itemJson = ''
            # 获取json
            with open(tempJson, 'r+') as f:
                list = f.readlines()
                itemJson = "".join(list)

            command = shlex.split(
                'scancode -l -c %s --json %s -n 4 --timeout 10 --max-in-memory -1  --license-score 80 ' % (self._diffPath_, tempJson))
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
            logging.info("===============END SCAN REPO===============")

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
            api = AuthApi()
            response = api.get_token(os.environ.get("GITEE_USER"),
                                    os.environ.get("GITEE_PASS"),
                                    os.environ.get("GITEE_REDIRECT_URI"),
                                    os.environ.get("GITEE_CLIENT_ID"),
                                    os.environ.get("GITEE_CLIENT_SECRET"),
                                    "user_info")
            accessToken = response["access_token"]
            url = 'https://gitee.com/api/v5/repos/'+self._owner_+'/'+self._repo_+'/pulls/'+ self._num_ +'/files?access_token='+accessToken
            response = http.request('GET',url)         
            resStatus = response.status
        
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
    
    def createDiff(self, fileList):
        diffPath = self._anlyzeSrc_ + "/diff/" + self._repo_ 
        for diff_added in fileList:
            try:
                filePath = diff_added['filename']
                fileDir = os.path.dirname(filePath)
                tempFile = diffPath + "/" + fileDir            
                if os.path.exists(tempFile) is False:
                    os.makedirs(tempFile)                
                sourcePath = self._repoSrc_ + "/" + filePath
                command = shlex.split('cp -r %s  %s' % (sourcePath, tempFile))
                resultCode = subprocess.Popen(command)
                while subprocess.Popen.poll(resultCode) == None:
                    time.sleep(1)
                popKill(resultCode)
            except:
                pass
        return diffPath


    @catch_error
    def savePr(self, scaResult, scaJson):
        try:
            status = 1
            message = ""
            apiObc = AuthApi()
            response = apiObc.getPrInfo(self._owner_, self._repo_, self._num_)
            repoLicense = ""
            repoLicLg = ""
            specLicLg = ""
            licScope = ""
            copyrightLg = ""
            prCommit = ""
            passState = 0
            mergeState = 0
            if response == 403:
                status = 0
                message = "GITEE API LIMIT"
            elif response == 404:
                status = 0
                message = "GITEE API ERROR"
            else:
                prData = response.data.decode('utf-8')
                prData = json.loads(prData)
                prHead = prData['head']
                prCommit = prHead['ref']
                mergedAt = prData['merged_at']
                if mergedAt is not None:
                    mergeState = 1
                # 存入数据库
                scaJson = pymysql.escape_string(scaJson)
                repoLicLg = scaResult['repo_license_legal']
                specLicLg = scaResult['spec_license_legal']
                licScope = scaResult['license_in_scope']
                copyrightLg = scaResult['repo_copyright_legal']
                repoLicense = ','.join(repoLicLg['is_legal']['license'])
                if self._type_ == "inde" and repoLicLg['pass'] and licScope['pass']:
                    passState = 1
                elif self._type_ == "ref" and specLicLg['pass'] and licScope['pass']:
                    passState = 1
                repoLicLg = pymysql.escape_string(str(repoLicLg))
                specLicLg = pymysql.escape_string(str(specLicLg))
                licScope = pymysql.escape_string(str(licScope))
                copyrightLg = pymysql.escape_string(str(copyrightLg))
            
            #检查是否存在数据
            itemData = (self._owner_, self._repo_, self._num_)
            itemLic = self._dbObject_.Query_PR(itemData)
            if itemLic is None:
                repoData = (self._repo_, self._owner_, self._gitUrl_, repoLicense, self._num_, scaJson, repoLicLg, specLicLg,\
                    licScope, copyrightLg, prCommit, passState, mergeState, self._prUrl_ , status, message)
                self._dbObject_.add_PR(repoData)
            else:
                repoData = ( repoLicense, scaJson, repoLicLg, specLicLg, licScope, copyrightLg, passState, mergeState, status,\
                             message, itemLic['id'])
                self._dbObject_.upd_PR(repoData)
        finally:
            self._dbObject_.Close_Con()