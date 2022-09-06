import logging
import os
from pickle import FALSE
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
SOURTH_PATH = '/home/giteeFile'

logging.getLogger().setLevel(logging.INFO)

class ItemLicSca(object):

    def __init__(self):
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
            type = urlDic['type']
            typeFlag,scaResult = self.getTypeUrl(type)
            if typeFlag:
                owner = urlDic['namespace']
                name = urlDic['name']
                commit = urlDic['version']
                self._owner_ = owner
                self._repo_ = name
                self._commit_ = commit
                self._purl_ = var
                #先查询数据是否存在
                if commit is None:
                    #获取最新数据
                    itemData = (self._owner_, self._repo_)
                    itemLic = self._dbObject_.Query_Repo_ByTime(itemData)
                else:
                    itemData = (self._owner_, self._repo_, self._commit_)
                    itemLic = self._dbObject_.Query_Repo_ByVersion(itemData)
                scaResult = {}
                if itemLic is None or (itemLic is not None and itemLic['is_pro_license'] is None):
                    scaResult = {
                        "repo_license_legal": {
                            "license": ["项目未扫描"]
                            },
                        "repo_copyright_legal": {
                            "copyright": ["项目未扫描"]
                        }
                    }
                else:           
                    repoLicLg = eval(itemLic['is_pro_license']) 
                    copyrightLg = eval(itemLic['is_copyright'])
                    reLicList = repoLicLg['is_legal']['license']
                    reCopy = copyrightLg['copyright']
                    scaResult['repo_license_legal'] = {
                        "license": reLicList
                    }
                    scaResult['repo_copyright_legal'] = {
                        "copyright": reCopy
                    }

            repoRe = {
                "purl" : var,
                "result": scaResult
            }
            result.append(repoRe)
        return result

    @catch_error
    def licSca(self, url):
        try:      
            if url.startswith('pkg:'):
                purl = PackageURL.from_string(url)
                urlDic = purl.to_dict()
                type = urlDic['type']
                typeFlag,scaResult = self.getTypeUrl(type)
                if typeFlag is False:
                    return scaResult
                owner = urlDic['namespace']
                name = urlDic['name']
                commit = urlDic['version']
                self._owner_ = owner
                self._repo_ = name
                self._commit_ = commit             
            else:
                urlList = url.split("/")
                type = urlList[2]
                self._typeUrl_ = 'https://' + type
                self._owner_ = urlList[3]
                self._repo_ = urlList[4]
                self._commit_ = "master"
            self._purl_ = url

            gitUrl = self._typeUrl_ + '/' + self._owner_ + '/' + self._repo_ + '.git'
            repoUrl = self._typeUrl_ + '/' + self._owner_ + '/' + self._repo_
            timestamp = int(time.time())
            scaResult = ''
            # 创建临时文件
            temFileSrc = SOURTH_PATH +'/tempSrc'
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
            try:
                repo = Repo.clone_from(gitUrl,to_path=self._repoSrc_)
            except:
                scaResult = {
                    "repo_license_legal": {
                        "pass": False,
                        "result_code": "",
                        "notice": "Git clone 失败，无效URL",
                        "is_legal": {"pass": False,"license": [],"notice": "","detail": {}}
                    },
                    "spec_license_legal": {},
                    "license_in_scope": {},
                    "repo_copyright_legal": {
                        "pass": False,
                        "result_code": "",
                        "notice": "Git clone 失败，无效URL",
                        "copyright": []
                    }
                }
                return scaResult
            try:
                repo.git.checkout(self._commit_)
            except:
                scaResult = {
                    "repo_license_legal": {
                        "pass": False,
                        "result_code": "",
                        "notice": "不存在该Version/commit: "+ self._commit_,
                        "is_legal": {
                            "pass": False,
                            "license": [],
                            "notice": "",
                            "detail": {}
                        }
                    },
                    "spec_license_legal": {
                    },
                    "license_in_scope": {
                    },
                    "repo_copyright_legal": {
                        "pass": False,
                        "result_code": "",
                        "notice": "不存在该Version/commit: "+ self._commit_,
                        "copyright": []
                    }
                }
                return scaResult
            logging.info("=============End fetch repo==============")
            # 扫描pr文件
            scaJson = self.getPrSca()
            scaResult = getScaAnalyze(scaJson, self._anlyzeSrc_, self._type_)
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
            #检查是否存在数据
            itemData = (self._owner_, self._repo_, self._commit_)
            itemLic = self._dbObject_.Query_Repo_ByVersion(itemData)
            if itemLic is None:
                repoData = (self._repo_, self._owner_, repoUrl, repoLicense, scaJson, repoLicLg, specLicLg,\
                    licScope, copyrightLg, self._commit_, self._purl_ )
                self._dbObject_.add_ItemLic(repoData)
            else:
                repoData = (self._commit_, repoLicense,scaJson, repoLicLg, specLicLg, licScope, copyrightLg, itemLic['id'])
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
            temJsonSrc = SOURTH_PATH +'/tempJson'
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
                'scancode -l -c %s --max-depth %s --json %s -n 3 --timeout 10 --max-in-memory -1 --license-score 80 --only-findings' % (self._repoSrc_, maxDepth, tempJson))
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
    def getTypeUrl(self, type):
        typeFlag = False
        scaResult = {}
        if type in ['gitee','github','gitlab']:
            typeFlag = True
            self._typeUrl_ = 'https://' + type + '.com'
        else:
            scaResult = {
                "repo_license_legal": {
                    "pass": False,
                    "result_code": "",
                    "notice": "不支持的type类型",
                    "is_legal": {"pass": False,"license": [],"notice": "","detail": {}}
                },
                "repo_copyright_legal": {
                    "pass": False,
                    "result_code": "",
                    "notice": "不支持的type类型",
                    "copyright": []
                }
            }
        return typeFlag, scaResult


    