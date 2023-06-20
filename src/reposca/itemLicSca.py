import json
from urllib.parse import urlsplit
import jsonpath
import logging
import os
from os.path import basename
import shlex
import stat
import subprocess
import time
import urllib.request
import pymysql
from pathlib import Path
from git.repo import Repo
from reposca.licenseCheck import LicenseCheck
from reposca.analyzeSca import getScaAnalyze, licenseSplit
from reposca.repoDb import RepoDb
from util.popUtil import popKill
from util.extractUtil import extractCode
from util.formateUtil import formateUrl
from util.catchUtil import catch_error
from util.downUtil import Down
from reposca.takeRepoSca import cleanTemp
from packageurl import PackageURL

ACCESS_TOKEN = '694b8482b84b3704c70bceef66e87606'
SOURTH_PATH = '/home/repo/tempRepo'

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
        try:
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
                #temp
                if 'openeuler' in owner.lower():
                    self._commit_ = 'master'
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
                if itemLic is None or (itemLic is not None and itemLic['sca_json'] is None):
                    scaResult = {
                        "repo_license": [],
                        "repo_license_legal": [],
                        "repo_license_illegal": [],
                        "repo_copyright_legal": [],
                        "repo_copyright_illegal": [],
                        "is_sca": False
                    }
                else:           
                    repoLicLg = eval(itemLic['is_pro_license']) 
                    copyrightLg = eval(itemLic['is_copyright'])
                    reLicList = repoLicLg['is_legal']['license']
                    reDetial = repoLicLg['is_legal']['detail']
                    chJson = json.dumps(reDetial)
                    jsonData = json.loads(chJson)
                    reRisks = jsonpath.jsonpath(jsonData, '$.[*].risks')
                    spLicList = []
                    for lic in reLicList:
                        spLic = licenseSplit(lic)
                        spLicList.extend(spLic)
                    licenseCheck = LicenseCheck('repo')
                    for item in range(len(spLicList) - 1, -1, -1):
                        if licenseCheck.check_exception(spLicList[item]):
                            del spLicList[item]
                    risksList = []
                    leLicList = []
                    if reRisks is False:
                        reRisks = []
                    for item in reRisks:
                        risksList.extend(item)
                    for item in range(len(risksList) - 1, -1, -1):
                        if licenseCheck.check_exception(risksList[item]):
                            del risksList[item]
                    for leLic in spLicList:
                        if leLic not in risksList:
                            leLicList.append(leLic)
                    reCopy = copyrightLg['copyright']
                    scaResult['repo_license'] = reLicList
                    scaResult['repo_license_legal'] = leLicList
                    scaResult['repo_license_illegal'] = risksList
                    scaResult['repo_copyright_legal'] = reCopy
                    scaResult['repo_copyright_illegal'] = []
                    scaResult['is_sca'] = True
                repoRe = {
                    "purl" : var,
                    "result": scaResult
                }
                result.append(repoRe)
            return result
        finally:
            self._dbObject_.Close_Con()

    @catch_error
    def licSca(self, url):
        try:
            self._timestamp_ = int(time.time())
            # 创建临时文件
            temFileSrc = SOURTH_PATH +'/tempSrc'
            temFileSrc = formateUrl(temFileSrc)
            self._delSrc_ = ''
            if os.path.exists(temFileSrc) is False:
                os.makedirs(temFileSrc) 
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
                scaResult = self.gitCloneFile(temFileSrc)    
                if scaResult != "":
                    return scaResult          
            else:                                     
                urlList = url.split("/")
                try:
                    response = urllib.request.urlopen(url)  
                except:
                    scaResult = {
                        "repo_license_legal": {
                            "pass": False,
                            "result_code": "",
                            "notice": "下载失败:"+ url,
                            "is_legal": {
                                "pass": False,
                                "license": [],
                                "notice": "",
                                "detail": {}
                            }
                        },
                        "spec_license_legal": {},
                        "license_in_scope": {},
                        "repo_copyright_legal": {
                            "pass": False,
                            "result_code": "",
                            "notice": "下载失败:"+ url,
                            "copyright": []
                        }
                    }
                    return scaResult 
                HttpMessage = response.info()                
                ContentType = HttpMessage.get("Content-Type")   
                self._commit_ = "master"           
                #判断下载链接/网站链接 
                if "text/html;" in ContentType:        
                    type = urlList[2]
                    self._typeUrl_ = 'https://' + type
                    self._owner_ =  self.getOwner(urlList)
                    self._repo_ = urlList[len(urlList) - 1]        
                    self._repo_ = self._repo_.strip(".git")          
                    scaResult = self.gitCloneFile(temFileSrc)    
                    if scaResult != "":
                        return scaResult  
                else:
                    logging.info("=================DOWN FILE=================")
                    downUtil = Down()
                    urlSplit = urlsplit(url) 
                    fileName = basename(urlSplit[2])     
                    self._owner_ = urlSplit[1]
                    self._repoUrl_ = url       
                    self._repo_ = self.getFileName(url)
                    
                    self._repoSrc_ = temFileSrc + '/'+ "downRepo" + '/' + self._repo_ + str(self._timestamp_) + "/" + self._repo_
                    self._anlyzeSrc_ = temFileSrc + '/' + "downRepo" + '/' + self._repo_ + str(self._timestamp_) + "/" + self._repo_
                    self._delSrc_ = temFileSrc + '/' + "downRepo" + '/' + self._repo_ + str(self._timestamp_)
                    if os.path.exists(self._repoSrc_) is False:
                        os.makedirs(self._repoSrc_)
                    try:
                        filePath = self._repoSrc_ + "/" + fileName
                        downIn = downUtil.downLoad(url, filePath , 3)
                    except:
                        scaResult = {
                            "repo_license_legal": {
                                "pass": False,
                                "result_code": "",
                                "notice": "下载失败:"+ url,
                                "is_legal": {
                                    "pass": False,
                                    "license": [],
                                    "notice": "",
                                    "detail": {}
                                }
                            },
                            "spec_license_legal": {},
                            "license_in_scope": {},
                            "repo_copyright_legal": {
                                "pass": False,
                                "result_code": "",
                                "notice": "下载失败:"+ url,
                                "copyright": []
                            }
                        }
                    if downIn:
                        logging.info("=================END DOWN==================")
                    else:
                        scaResult = {
                            "repo_license_legal": {
                                "pass": False,
                                "result_code": "",
                                "notice": "下载失败:"+ url,
                                "is_legal": {
                                    "pass": False,
                                    "license": [],
                                    "notice": "",
                                    "detail": {}
                                }
                            },
                            "spec_license_legal": {},
                            "license_in_scope": {},
                            "repo_copyright_legal": {
                                "pass": False,
                                "result_code": "",
                                "notice": "下载失败:"+ url,
                                "copyright": []
                            }
                        }
                        return scaResult 

            self._purl_ = url          
            scaResult = ''
            self._file_ = 'temp'
                  
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
                repoData = (self._repo_, self._owner_, self._repoUrl_, repoLicense, scaJson, repoLicLg, specLicLg,\
                    licScope, copyrightLg, self._commit_, self._purl_ )
                self._dbObject_.add_ItemLic(repoData)
            else:
                repoData = (self._commit_, repoLicense,scaJson, repoLicLg, specLicLg, licScope, copyrightLg, itemLic['id'])
                self._dbObject_.upd_ItemLic(repoData)
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.exception("Error on %s" % (e))
        finally:
            self._dbObject_.Close_Con()
            # 清理临时文件
            if self._delSrc_ != '':
                try:
                    cleanTemp(self._delSrc_)
                    os.chmod(self._delSrc_, stat.S_IRWXU)
                    os.rmdir(self._delSrc_)
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

            logging.info("==============START SCAN REPO==============")
            # 调用scancode
            command = shlex.split(
                'scancode -l -c %s --max-depth %s --json %s -n 3 --timeout 10 --max-in-memory -1 --license-score 80' % (self._repoSrc_, maxDepth, tempJson))
            resultCode = subprocess.Popen(command)
            while subprocess.Popen.poll(resultCode) == None:
                time.sleep(1)
            popKill(resultCode)
            scaJson = ''
            # 获取json
            with open(tempJson, 'r+') as f:
                list = f.readlines()
                scaJson = "".join(list)
            logging.info("===============END SCAN REPO===============")
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
                "repo_license": ['不支持的type类型'],
                "repo_license_legal": [],
                "repo_license_illegal": [],
                "repo_copyright_legal": [],
                "repo_copyright_illegal": [],
                "is_sca": False
            }
        return typeFlag, scaResult

    @catch_error
    def gitCloneFile(self, temFileSrc):
        logging.info("=============START FETCH REPO==============")
        scaResult = ""
        self._gitUrl_ = self._typeUrl_ + '/' + self._owner_ + '/' + self._repo_ + '.git'
        self._repoUrl_ = self._typeUrl_ + '/' + self._owner_ + '/' + self._repo_
        self._repoSrc_ = temFileSrc + '/'+self._owner_ + '/' + str(self._timestamp_) + '/' + self._repo_
        self._anlyzeSrc_ = temFileSrc + '/' + self._owner_ + '/' + str(self._timestamp_)
        self._delSrc_ = temFileSrc + '/'+self._owner_ + '/' + str(self._timestamp_)
        if os.path.exists(self._repoSrc_) is False:
            os.makedirs(self._repoSrc_)       
        try:
            repo = Repo.init(self._repoSrc_)
            origin = repo.create_remote("origin", self._gitUrl_)
            origin.fetch(self._commit_, depth=1)
            repo.git.checkout("FETCH_HEAD")
        except Exception as e:
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
        logging.info("===============END FETCH REPO==============")
        return scaResult

    @catch_error
    def getFileName(self, path):
        fileName = Path(path).stem
        if '.tar' in fileName:
            fileName = self.getFileName(fileName)
        elif '.tgz' in fileName:
            fileName = self.getFileName(fileName)
        elif '.zip' in fileName:
            fileName = self.getFileName(fileName)
        elif '.rar' in fileName:
            fileName = self.getFileName(fileName)

        return fileName

    @catch_error
    def getOwner(self, urlList):
        owner = ""
        for var in urlList[3:len(urlList) - 1]:
            owner = owner + var + "/"
        return owner.strip('/')