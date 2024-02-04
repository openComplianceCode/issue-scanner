# -*- coding: utf-8 -*-
import logging
import os
import random
import shlex
import stat
import subprocess
import time
import pymysql
import urllib3
import json
import jsonpath
import yaml
from reposca.analyzeSca import getScaAnalyze
from reposca.takeRepoSca import cleanTemp
from reposca.repoDb import RepoDb
from util.authApi import AuthApi
from util.popUtil import popKill
from util.extractUtil import extractCode
from util.formateUtil import formateUrl
from util.catchUtil import catch_error
from git.repo import Repo

SOURTH_PATH = '/home/repo/persistentRepo'
TEMP_PATH = '/home/repo/tempRepo'
LIC_COP_LIST = ['license', 'readme', 'notice', 'copying', 'third_party_open_source_software_notice', 'copyright', '.spec']
USER_AGENT = [
    'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36 OPR/26.0.1656.60',
    'Opera/8.0 (Windows NT 5.1; U; en)',
    'Mozilla/5.0 (Windows NT 5.1; U; en; rv:1.8.1) Gecko/20061208 Firefox/2.0.0 Opera 9.50',
    'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; en) Opera 9.50',
    'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.71 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
    'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Chrome/10.0.648.133 Safari/534.16',
    'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:34.0) Gecko/20100101 Firefox/34.0',
    'Mozilla/5.0 (X11; U; Linux x86_64; zh-CN; rv:1.9.2.10) Gecko/20100922 Ubuntu/10.10 (maverick) Firefox/3.6.10'
]
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
            self._domain_ = 'https://' + urlList[2]
            self._owner_ = urlList[3]
            self._repo_ = urlList[4]
            self._num_ = urlList[6]
            self._branch_ = 'pr_' + self._num_
            self._gitUrl_ = self._domain_ + '/' + self._owner_ + '/' + self._repo_ + '.git'
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
            #获取PR增量文件目录&commit信息
            if 'gitee.com' in self._domain_:
                pr_flag = "gitee"
                fileList =  self.getDiffFiles()    
                if fileList is None:
                    fileList = []
                self._commit_ = self.getCommitInfo() 
            else:
                pr_flag = "github"
                fileList = self.getDiffFilesByGithub()
                self._commit_ = self.getCommitByGithub() 
            #创建diff副本
            self._diffPath_ = self.createDiff(fileList)             
            copyright_type = self.get_copyright_type(self._commit_)
            
            logging.info("==============END FETCH REPO===============")
            
            # 扫描pr文件
            scaJson = self.getPrSca()
            scaResult = getScaAnalyze(scaJson, self._anlyzeSrc_, self._type_, copyright_type, self._fileArray_)
            # Save Data
            self.savePr(pr_flag, scaResult, scaJson)
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
        project_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))      
        config_url = project_path + '/token.yaml'
        CONF = yaml.safe_load(open(config_url))
        params = CONF['API_TOKEN']
        token_list = params.split(",")
        authorToken = random.choice(token_list)
        url = 'https://gitee.com/api/v5/repos/'+self._owner_+'/'+self._repo_+'/pulls/'+ self._num_ +'/files'
        response = http.request(
            'GET',
            url,
            headers = {
                'User-Agent': random.choice(USER_AGENT),
                'access_token': authorToken
            }
        )         
        resStatus = response.status
        if resStatus == 403:
            token_list.remove(authorToken)
            while (len(token_list) > 0):
                authorToken = random.choice(token_list)
                url = 'https://gitee.com/api/v5/repos/'+self._owner_+'/'+self._repo_+'/pulls/'+ self._num_ +'/files'
                response = http.request(
                    'GET',
                    url,
                    headers = {
                        'User-Agent': random.choice(USER_AGENT),
                        'access_token': authorToken
                    }
                )         
                resStatus = response.status
                if resStatus == 200:
                    break
                else:
                    token_list.remove(authorToken)
        
        if resStatus == 404:
            raise Exception("Gitee API Fail")

        if resStatus == 403:
            raise Exception("Gitee API LIMIT")

        repoStr = response.data.decode('utf-8')
        temList = json.loads(repoStr)
        fileList.extend(temList)     
        return fileList
    

    @catch_error
    def getDiffFilesByGithub(self):
        fileList = []
        repoStr = "Flag"
        http = urllib3.PoolManager()        
        authorToken = os.environ.get("GITHUB_TOKEN")
        url = 'https://api.github.com/repos/'+self._owner_+'/'+self._repo_+'/pulls/'+ self._num_ + '/files'
        response = http.request(
            'GET',
            url,
            headers = {
                'User-Agent': random.choice(USER_AGENT),
                'Accept' : 'application/vnd.github+json',
                'Authorization':'Bearer ' + authorToken
            }
        )         
        resStatus = response.status
        
        if resStatus == 403:
            raise Exception("Github API Token Limit")
        
        if resStatus == 404:
            raise Exception("Github API Fail")

        repoStr = response.data.decode('utf-8')
        temList = json.loads(repoStr)
        fileList.extend(temList)     
        return fileList

    @catch_error
    def getCommitInfo(self):
        commit_info = []
        repoStr = "Flag"
        http = urllib3.PoolManager()        
        project_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))      
        config_url = project_path + '/token.yaml'
        CONF = yaml.safe_load(open(config_url))
        params = CONF['API_TOKEN']
        token_list = params.split(",")
        authorToken = random.choice(token_list) 
        url = 'https://gitee.com/api/v5/repos/'+self._owner_+'/'+self._repo_+'/pulls/'+ self._num_ +'/commits'
        response = http.request(
            'GET',
            url,
            headers = {
                'User-Agent': random.choice(USER_AGENT),
                'access_token': authorToken
            }
        )

        resStatus = response.status       
        if resStatus == 403:
            token_list.remove(authorToken)
            while (len(token_list) > 0):
                authorToken = random.choice(token_list)
                url = 'https://gitee.com/api/v5/repos/'+self._owner_+'/'+self._repo_+'/pulls/'+ self._num_ +'/commits'
                response = http.request(
                    'GET',
                    url,
                    headers = {
                        'User-Agent': random.choice(USER_AGENT),
                        'access_token': authorToken
                    }
                )         
                resStatus = response.status
                if resStatus == 200:
                    break
                else:
                    token_list.remove(authorToken)
        
        if resStatus == 404:
            raise Exception("Gitee API Fail")

        if resStatus == 403:
            raise Exception("Gitee API LIMIT")

        repoStr = response.data.decode('utf-8')
        temList = json.loads(repoStr)
        commit_info.extend(temList)     
        return commit_info
    
    @catch_error
    def getCommitByGithub(self):
        commit_info = []
        repoStr = "Flag"
        http = urllib3.PoolManager()        
        authorToken = os.environ.get("GITHUB_TOKEN")    
        url = 'https://api.github.com/repos/'+self._owner_+'/'+self._repo_+'/pulls/'+ self._num_ +'/commits'
        response = http.request(
            'GET',
            url,
            headers = {
                'User-Agent': random.choice(USER_AGENT),
                'Accept' : 'application/vnd.github+json',
                'Authorization':'Bearer ' + authorToken
            }
        )        
        resStatus = response.status
        
        if resStatus == 403:
            raise Exception("Github API Token Limit")
        
        if resStatus == 404:
            raise Exception("Gitee API Fail")

        repoStr = response.data.decode('utf-8')
        temList = json.loads(repoStr)
        commit_info.extend(temList)     
        return commit_info
    
    @catch_error
    def get_copyright_type(self, commit_info):
        copyright_type = "No"
        if commit_info is not None:
            for item in commit_info:
                commit_email = item['commit']['committer']['email']
                if ("huawei.com" in commit_email):
                    copyright_type = "Huawei"
                    break
        return copyright_type
            

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
        self._fileArray_= []
        for diff_added in fileList:
            try:
                filePath = diff_added['filename']
                self._fileArray_.append(filePath)
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
    def savePr(self, pr_flag, scaResult, scaJson):
        status = 1
        message = ""
        apiObc = AuthApi()
        if pr_flag == 'gitee':
            response = apiObc.getPrInfo(self._owner_, self._repo_, self._num_)
        else:
            response = apiObc.getPrInfoByGithub(self._owner_, self._repo_, self._num_)
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
            message = "PR INFO API LIMIT"
        elif response == 404:
            status = 0
            message = "PR INFO API ERROR"
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