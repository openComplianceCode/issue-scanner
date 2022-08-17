import json
import logging
import os
import shlex
import stat
import subprocess
import time
import pymysql
from git.repo import Repo
from reposca.analyzeSca import getScaAnalyze
from reposca.repoDb import RepoDb
from util.popUtil import popKill
from util.extractUtil import extractCode
from util.formateUtil import formateUrl
from util.catchUtil import catch_error
from reposca.takeRepoSca import cleanTemp
from packageurl import PackageURL

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
    def scaPurl(self, purlList):
        result = []
        for var in purlList:
            self._purl_ = var
            url = PackageURL.from_string(var)
            urlDic = url.to_dict()
            owner = urlDic['namespace']
            name = urlDic['name']
            commit = urlDic['version']
            self._owner_ = owner
            self._repo_ = name
            self._commit_ = commit
            self._purl_ = var

            #先查询数据是否存在
            itemData = (self._owner_, self._repo_)
            itemLic = self._dbObject_.Query_Repo_ByName(itemData)
            scaResult = {}
            if itemLic is None or (itemLic is not None and (itemLic['commite'] != commit or itemLic['is_pro_license'] is None)):
                scaResult = self.licSca(itemLic)
                scaResult.pop('spec_license_legal')
                scaResult.pop('license_in_scope')
            else:           
                repoLicLg = eval(itemLic['is_pro_license']) 
                copyrightLg = eval(itemLic['is_copyright'])
                scaResult['repo_license_legal'] = repoLicLg
                scaResult['repo_copyright_legal'] = copyrightLg

            repoRe = {
                "purl" : var,
                "result": scaResult
            }
            result.append(repoRe)
        return result

    @catch_error
    def licSca(self, itemLic):
        try:      
            gitUrl = GIT_URL + '/' + self._owner_ + '/' + self._repo_ + '.git'
            repoUrl = GIT_URL + '/' + self._owner_ + '/' + self._repo_
            timestamp = int(time.time())
            scaResult = ''
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
            repo.git.checkout(self._commit_)
            self._gitRepo_ = repo
            self._git_ = repo.git
            logging.info("=============End fetch repo==============")

            # 扫描pr文件
            scaJson = self.getPrSca()
            scaResult = getScaAnalyze(scaJson, self._anlyzeSrc_, self._owner_)

            # 存入数据库
            scaJson = pymysql.escape_string(scaJson)
            repoLicLg = scaResult['repo_license_legal']
            specLicLg = scaResult['spec_license_legal']
            licScope = scaResult['license_in_scope']
            copyrightLg = scaResult['repo_copyright_legal']
            repoLicense = ','.join(repoLicLg['is_legal']['license'])
            repoLicLg = pymysql.escape_string(str(repoLicLg))
            specLicLg = pymysql.escape_string(str(specLicLg))
            licScope = pymysql.escape_string(str(licScope))
            copyrightLg = pymysql.escape_string(str(copyrightLg))
            if itemLic is None: 
                repoData = (self._repo_, self._owner_, repoUrl, repoLicense, scaJson, repoLicLg, specLicLg,\
                    licScope, copyrightLg, self._commit_, self._purl_ )
                self._dbObject_.add_ItemLic(repoData)
            else:
                repoData = (self._commit_, repoLicense, scaJson, repoLicLg, specLicLg,\
                    licScope, copyrightLg, itemLic['id'])
                self._dbObject_.upd_ItemLic(repoData)
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


    