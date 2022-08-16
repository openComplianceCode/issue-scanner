import json
import logging
import os
import shlex
import stat
import subprocess
import time
import jsonpath
import pymysql
from git.repo import Repo
from reposca.makeRepoCsv import checkRepoLicense
from reposca.repoDb import RepoDb
from util.popUtil import popKill
from util.extractUtil import extractCode
from util.formateUtil import formateUrl
from util.catchUtil import catch_error
from reposca.takeRepoSca import cleanTemp

ACCESS_TOKEN = '694b8482b84b3704c70bceef66e87606'
GIT_URL = 'https://gitee.com'
SOURTH_PATH = '/home/giteeFile'

logging.getLogger().setLevel(logging.INFO)

class ItemLicSca(object):

    def __init__(self):
        self._current_dir_ = os.path.dirname(os.path.abspath(__file__))
        #连接数据库
        self._dbObject_ = RepoDb(
            host_db = os.environ.get("MYSQL_HOST"), 
            user_db = os.environ.get("MYSQL_USER"), 
            password_db = os.environ.get("MYSQL_PASSWORD"), 
            name_db = os.environ.get("MYSQL_DB_NAME"), 
            port_db = int(os.environ.get("MYSQL_PORT")))

    @catch_error
    def licSca(self, url, commit):
        try:
            urlList = url.split("/")
            self._owner_ = urlList[3]
            self._repo_ = urlList[4]
            gitUrl = GIT_URL + '/' + self._owner_ + '/' + self._repo_ + '.git'
            timestamp = int(time.time())

            #先查询数据是否存在
            itemData = (self._owner_, self._repo_)
            itemLic = self._dbObject_.get_ItemLic(itemData)
            scaResult = ''
            delSrc = ''
            if itemLic is None or (itemLic is not None and (itemLic['commite'] != commit or itemLic['is_pro_license'] is None)):
                # 创建临时文件
                temFileSrc = self._current_dir_+'/tempSrc'
                temFileSrc = formateUrl(temFileSrc)

                if os.path.exists(temFileSrc) is False:
                    os.makedirs(temFileSrc)

                self._file_ = 'temp'
                self._repoSrc_ = temFileSrc + '/'+self._owner_ + '/' + str(timestamp) + '/' + self._repo_
                self._anlyzeSrc_ = temFileSrc + '/' + self._owner_ + '/' + str(timestamp)
                delSrc = temFileSrc + '/'+self._owner_ + '/' + str(timestamp)
                if os.path.exists(self._repoSrc_) is False:
                    os.makedirs(self._repoSrc_)

                logging.info("=============Start fetch repo==============")
                repo = Repo.clone_from(gitUrl,to_path=self._repoSrc_)
                repo.git.checkout(commit)
                self._gitRepo_ = repo
                self._git_ = repo.git
                logging.info("=============End fetch repo==============")

                # 扫描pr文件
                scaJson = self.getPrSca()
                scaResult = self.getScaAnalyze(scaJson)

                # 存入数据库
                scaJson = pymysql.escape_string(scaJson)
                repoLicense = ','.join(scaResult['license'])
                sqlRes = pymysql.escape_string(str(scaResult))
                if itemLic is None: 
                    repoData = (commit, self._repo_, self._owner_, url, repoLicense, scaJson, sqlRes)
                    self._dbObject_.add_ItemLic(repoData)
                else:
                    repoData = (commit, repoLicense, scaJson, sqlRes, itemLic['id'])
                    self._dbObject_.upd_ItemLic(repoData)
            else:           
                scaResult = eval(itemLic['is_pro_license'])
            
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
    def getScaAnalyze(self, scaJson):
        '''
        :param repoSrc: 扫描文件路径
        :param repo: 项目名
        :param scaJson: 扫描结果json
        :return:分析结果json
        '''
        sca_result = {}
        itemPathList = []

        haveLicense = False
        itemLicList = []
        noticeLicense = '缺少项目级License声明文件'

        jsonData = json.loads(scaJson)
        itemPath = jsonpath.jsonpath(jsonData, '$.files[*].path')
        licenseList = jsonpath.jsonpath(jsonData, '$.files[*].licenses')

        logging.info("=============Start analyze result==============")
        for i, var in enumerate(licenseList):
            path = itemPath[i]
            if len(var) == 0:
                continue
            for pathLicense in var:
                isLicenseText = pathLicense['matched_rule']['is_license_text']
                spdx_name = pathLicense['spdx_license_key']
                if 'LicenseRef-scancode-' in spdx_name:
                    continue        
                # 判断是否有项目license
                if checkRepoLicense(path) and isLicenseText is True :
                    if haveLicense is False:
                        haveLicense = True
                        noticeLicense = ""
                        itemLicList.append(spdx_name)
                        itemPathList.append(path)
                    elif path.lower().endswith(("license",)) and path not in itemPathList:
                        itemLicList.clear()
                        itemPathList.clear()
                        itemLicList.append(spdx_name)
                        itemPathList.append(path)
                    elif path in itemPathList and spdx_name not in itemLicList: 
                        #同一个文件的做检查
                        itemLicList.append(spdx_name)                       
                else:
                    continue
        
        if len(itemPathList) == 0:
            itemPathList.append(noticeLicense)

        sca_result = {
            "pass": haveLicense,
            "result_code": "",
            "notice": itemPathList[0],
            "license": itemLicList,
        }
        logging.info("=============End analyze result==============")

        return sca_result

    