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
from pyrpm.spec import Spec

from reposca.makeRepoCsv import checkNotice, checkRepoLicense
from reposca.repoDb import RepoDb
from reposca.takeRepoSca import cleanTemp
from reposca.licenseCheck import LicenseCheck
from util.extractUtil import extractCode
from util.formateUtil import formateUrl
from util.catchUtil import catch_error
from util.postOrdered import infixToPostfix

ACCESS_TOKEN = '694b8482b84b3704c70bceef66e87606'
GIT_URL = 'https://gitee.com'
SOURTH_PATH = '/home/giteeFile'


class PrSca(object):
        
    def __init__(self):
        #连接数据库
        self._dbObject_ = RepoDb(
            host_db = os.environ.get("MYSQL_HOST"), 
            user_db = os.environ.get("MYSQL_USER"), 
            password_db = os.environ.get("MYSQL_PASSWORD"), 
            name_db = os.environ.get("MYSQL_DB_NAME"), 
            port_db = int(os.environ.get("MYSQL_PORT")))
        
        self._current_dir_ = os.path.dirname(os.path.abspath(__file__))

    @catch_error
    def doSca(self, url):
        try:
            urlList = url.split("/")
            self._owner_ = urlList[3]
            self._repo_ = urlList[4]
            self._num_ = urlList[6]
            gitUrl = GIT_URL + '/' + self._owner_ + '/' + self._repo_ + '.git'
            timestamp = int(time.time())
        
            #获取pr分支
            head, base = self.getPrBranch()
            if head == 403:
                return "ACCESS_TOKEN 无效、过期或已被撤销"
            elif head == 502:
                return "GITEE 服务器维护中"
            
            fetchUrl = 'pull/' + self._num_ + '/head:pr_' + self._num_ 
            
            # 创建临时文件
            temFileSrc = self._current_dir_+'/tempSrc'
            temFileSrc = formateUrl(temFileSrc)
            
            if os.path.exists(temFileSrc) is False:
                os.makedirs(temFileSrc) 

            self._repoSrc_ = SOURTH_PATH +'/'+self._owner_ + '/' + self._repo_
            self._anlyzeSrc_ = SOURTH_PATH +'/'+self._owner_
            delSrc = ''
            self._file_ = 'sourth'
            if os.path.exists(self._repoSrc_) is False:
                self._file_ = 'temp'
                self._repoSrc_ = temFileSrc + '/'+self._owner_ + '/' + str(timestamp) + '/' + self._repo_
                self._anlyzeSrc_ = temFileSrc + '/'+self._owner_ + '/' + str(timestamp)
                delSrc = temFileSrc + '/'+self._owner_ + '/' + str(timestamp)
                if os.path.exists(self._repoSrc_) is False:
                    os.makedirs(self._repoSrc_)
                #拉取项目
                # command = shlex.split('git clone --depth=1 --branch=%s %s %s' % (base[0], gitUrl, self._repoSrc_))           
                # resultCode = subprocess.Popen(command)
                command = shlex.split('git init')           
                resultCode = subprocess.Popen(command, cwd=self._repoSrc_)
                while subprocess.Popen.poll(resultCode) == None:
                    time.sleep(1)
            #拉取pr
            command = shlex.split('git fetch --depth=1 %s %s' % (gitUrl, fetchUrl))           
            resultCode = subprocess.Popen(command, cwd=self._repoSrc_)
            while subprocess.Popen.poll(resultCode) == None:
                time.sleep(1)
            #切换分支
            command = shlex.split('git checkout pr_%s' % (self._num_))          
            resultCode = subprocess.Popen(command, cwd=self._repoSrc_)
            while subprocess.Popen.poll(resultCode) == None:
                time.sleep(0.5)

            if resultCode.stdin:
                resultCode.stdin.close()
            if resultCode.stdout:
                resultCode.stdout.close()
            if resultCode.stderr:
                resultCode.stderr.close()
            try:
                resultCode.kill()
            except OSError:
                pass

            #扫描pr文件
            scaJson = self.getPrSca()
            scaResult = self.getScaAnalyze(scaJson)

        except Exception as e:
            logger = logging.getLogger(__name__)      
            logger.exception("Error on %s: %s" % (command, e.strerror))
        finally:
            #清理临时文件
            if delSrc != '':
                cleanTemp(delSrc)
                os.chmod(delSrc, stat.S_IWUSR) 
                os.rmdir(delSrc)
            
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
        url = 'https://gitee.com/api/v5/repos/' +self._owner_+ '/' +self._repo_+ '/pulls/' +self._num_+ '?access_token='+ACCESS_TOKEN
        response = http.request('GET',url)
        resStatus = response.status
 
        while resStatus == '403':
            return 403, 403
        
        while resStatus == '502':
            return 502, 502

        repoStr = response.data.decode('utf-8')
        apiJson = json.loads(repoStr)
        
        head = jsonpath.jsonpath(apiJson, '$.head.ref')
        base =jsonpath.jsonpath(apiJson, '$.base.ref')

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
            tempJson = temJsonSrc + '/' +self._repo_+str(timestamp)+'.txt'
            tempJson = formateUrl(tempJson)
            if os.path.exists(tempJson) is False:
                open(tempJson,'w')

            #调用先解压文件里得压缩文件
            # command = shlex.split('extractcode --shallow %s' % (self._repoSrc_))
            # resultCode = subprocess.Popen(command)
            # while subprocess.Popen.poll(resultCode) == None:
            #     time.sleep(1)
            reExt = extractCode(self._repoSrc_)
            if reExt is False:
                logging.error("file extracCode error")
            
            #调用scancode
            command = shlex.split('scancode -l -c %s --max-depth 3 --json %s -n 5 --timeout 3' % (self._repoSrc_, tempJson))
            resultCode = subprocess.Popen(command)
            while subprocess.Popen.poll(resultCode) == None:
                time.sleep(1)

            if self._file_ == 'sourth':
                #切回master
                command = shlex.split('git checkout master')          
                resultCode = subprocess.Popen(command, cwd=self._repoSrc_)
                while subprocess.Popen.poll(resultCode) == None:
                    time.sleep(0.5)
                #删除临时分支
                command = shlex.split('git branch -D pr_%s' % (self._num_))          
                resultCode = subprocess.Popen(command, cwd=self._repoSrc_)
                while subprocess.Popen.poll(resultCode) == None:
                    time.sleep(0.5)
                    
            if resultCode.stdin:
                resultCode.stdin.close()
            if resultCode.stdout:
                resultCode.stdout.close()
            if resultCode.stderr:
                resultCode.stderr.close()
            try:
                resultCode.kill()
            except OSError:
                pass

            scaJson = ''
            #获取json
            with open(tempJson, 'r+') as f:
                list = f.readlines()
                scaJson = "".join(list)

        except Exception as e:
            logger = logging.getLogger(__name__)      
            logger.exception("Error on %s: %s" % (command, e.strerror))
        finally:    
            #清空文件
            os.chmod(tempJson, stat.S_IWUSR) 
            os.remove(tempJson)
        
            return scaJson

    @catch_error
    def getScaAnalyze(self, scaJson):
        '''
        :param repoSrc: 扫描文件路径
        :param repo: 项目名
        :param scaJson: 扫描结果json
        :return:分析结果json
        '''
        sca_result = {}
        specLicenseList = []
        pathList = []

        haveLicense = False    
        isCopyright = False
        approved = True
        specLicense = True
        noticeLicense = '缺少项目级License声明文件'
        noticeScope = ''
        noticeSpec = '无spec文件'
        noticeCopyright = '缺少项目级Copyright声明文件'
        speLicDetial = {}

        jsonData = json.loads(scaJson)
        itemPath = jsonpath.jsonpath(jsonData, '$.files[*].path')
        licenseList =jsonpath.jsonpath(jsonData, '$.files[*].licenses')
        copyrightList = jsonpath.jsonpath(jsonData, '$.files[*].copyrights')
                
        #获取所有数据
        # dbObject = RepoDb()
        licenseCheck = LicenseCheck()
    
        for i,var in enumerate(licenseList):

            path = itemPath[i]
            #移除目录中'-extract'
            # path = self.rmExtract(path)

            #判断是否含有notice文件
            if checkNotice(path) and len(copyrightList[i]) > 0 :
                if isCopyright is False:
                    isCopyright = True
                    noticeCopyright = ""

                noticeCopyright = noticeCopyright + "("+path + "), "
                    
            if ".spec" in path and self.checkPath(path):
                #提取spec里的许可证声明
                fileUrl = self._anlyzeSrc_ +"/"+ itemPath[i]
                spec = Spec.from_file(fileUrl)
                if spec.license is not None:
                    licenses = infixToPostfix(spec.license)
                    isSpecLicense = licenseCheck.check_license_safe(licenses)
                    specLicense = isSpecLicense.get('result')
                    noticeSpec = isSpecLicense.get('notice')
                    speLicDetial = isSpecLicense.get('detail')

                    specLicenseList.append(spec.license)

            if len(var) == 0 :
                continue                    
                                    
            for pathLicense in var:

                isLicenseText = pathLicense['matched_rule']['is_license_text']
                #判断是否有项目license
                if checkRepoLicense(path) and isLicenseText is True and path not in pathList:
                    if haveLicense is False:
                        haveLicense = True
                        noticeLicense = ""
                        
                    noticeLicense = noticeLicense + "("+path+"), "
                    pathList.append(path)
                        
                spdx_name = pathLicense['spdx_license_key']
                        
                #判断license是否属于认证
                reLicense = self._dbObject_.Check_license(spdx_name)

                if len(reLicense) == 0 and pathLicense['start_line'] != pathLicense['end_line'] and 'LicenseRef-scancode-' not in spdx_name:
                    approved = False
                    noticeScope = noticeScope + spdx_name + "("+path + ", start_line: "+str(pathLicense['start_line'])+", end_line: "+str(pathLicense['end_line'])+"), "

        noticeLicense = noticeLicense.strip(', ')
        noticeCopyright = noticeCopyright.strip(', ')
        noticeScope = noticeScope.strip(', ')
        if noticeScope == '':
            noticeScope = 'OSI/FSF认证License'
        else:
            noticeScope = '存在非OSI/FSF认证的License：' + noticeScope

        sca_result = {
            "repo_license_legal": {
                "pass": haveLicense,
                "result_code" : "",
                "notice" : noticeLicense
            },
            "spec_license_legal": {
                "pass": specLicense,
                "result_code" : "",
                "notice" : noticeSpec,
                "detail" : speLicDetial
            },
            "license_in_scope": {
                "pass": approved,
                "result_code" : "",
                "notice" : noticeScope        
            },
            "repo_copyright_legal": {
                "pass": isCopyright,
                "result_code" : "",
                "notice" : noticeCopyright
            }
        }

        return sca_result

    @catch_error
    def checkPath(self, path):
        # 检查是notice文件
        path = path.lower()

        pathLevel = path.split("/")
        if len(pathLevel) > 3:
            return False
        
        return True

    @catch_error
    def rmExtract(self, path):
        pathList = path.split("/")

        for item in pathList:
            if '-extract' in item:
                pathList.remove(item)
                break
        
        return "/".join(pathList)
