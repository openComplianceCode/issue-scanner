
import json
import random
from urllib.parse import urlsplit
import logging
import os
from os.path import basename
import shlex
import stat
import subprocess
import time
import urllib.request
from pathlib import Path
from git.repo import Repo
import pymysql
import urllib3
from reposca.repoDb import RepoDb
from reposca.itemLicSca import SOURTH_PATH
from reposca.prSca import TEMP_PATH,USER_AGENT
from reposca.analyzeSca import getScaAnalyze
from reposca.sourceAnalyze import getSourceData
from util.popUtil import popKill
from util.extractUtil import extractCode
from util.formateUtil import formateUrl
from util.catchUtil import catch_error
from util.downUtil import Down
from reposca.takeRepoSca import cleanTemp
from packageurl import PackageURL


class CommSca(object):

    def __init__(self):
        #Connect to the database
        self._dbObject_ = RepoDb(
            host_db = os.environ.get("MYSQL_HOST"), 
            user_db = os.environ.get("MYSQL_USER"), 
            password_db = os.environ.get("MYSQL_PASSWORD"), 
            name_db = os.environ.get("MYSQL_DB_NAME"), 
            port_db = int(os.environ.get("MYSQL_PORT")))


    @catch_error
    def runSca(self, url, oauthToken):
        try:
            self._timestamp_ = int(time.time())
            self._oauthToken_ = oauthToken
            # Create temporary files
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
                            "notice": "Download failed:"+ url,
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
                            "notice": "Download failed:"+ url,
                            "copyright": []
                        }
                    }
                    return scaResult 
                HttpMessage = response.info()                
                ContentType = HttpMessage.get("Content-Type")   
                self._commit_ = "master"           
                #Determine download link/website link 
                if "text/html;" in ContentType:        
                    type = urlList[2]
                    if self._oauthToken_:
                        self._typeUrl_ = 'https://oauth2:'+ self._oauthToken_ + '@' + type
                    else:
                        self._typeUrl_ = 'https://' + type
                    self._owner_ = self.getOwner(urlList)
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
                                "notice": "Download failed:"+ url,
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
                                "notice": "Download failed:"+ url,
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
                                "notice": "Download failed:"+ url,
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
                                "notice": "Download failed:"+ url,
                                "copyright": []
                            }
                        }
                        return scaResult 

            self._purl_ = url          
            scaResult = ''
            self._file_ = 'temp'
                  
            # Scan pr files
            scaJson = self.getRepoSca()
            scaResult = getScaAnalyze(scaJson, self._anlyzeSrc_, self._type_, "None", [])
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.exception("Error on %s" % (e))
        finally:
            # Clean temporary files
            if self._delSrc_ != '':
                try:
                    cleanTemp(self._delSrc_)
                    os.chmod(self._delSrc_, stat.S_IRWXU)
                    os.rmdir(self._delSrc_)
                except:
                    pass
            return scaResult
    
    @catch_error
    def getRepoSca(self):
        '''
        :param repoSrc: Scan project path
        :param pathList: Scan file path list
        :return:Scan result json
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

            self._type_ = "inde"
            reExt = extractCode(self._repoSrc_)
            if reExt == "Except":
                logging.error("file extracCode error")
            elif reExt == "ref":
                self._type_ = "ref"         

            logging.info("==============START SCAN REPO==============")
            # Call scancode
            command = shlex.split(
                'scancode -l -c %s  --json %s -n 3 --timeout 10 --max-in-memory -1 --license-score 80' % (self._repoSrc_, tempJson))
            resultCode = subprocess.Popen(command)
            while subprocess.Popen.poll(resultCode) == None:
                time.sleep(1)
            popKill(resultCode)

            scaJson = ''
            # Get json
            with open(tempJson, 'r+') as f:
                list = f.readlines()
                scaJson = "".join(list)
            logging.info("===============END SCAN REPO===============")
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.exception("Error on %s: %s" % (command, e))
        finally:
            # Clear files
            os.chmod(tempJson, stat.S_IWUSR)
            os.remove(tempJson)
            return scaJson

    @catch_error
    def getTypeUrl(self, type):
        typeFlag = False
        scaResult = {}
        if type in ['gitee','github','gitlab','szv-open.codehub.huawei']:
            typeFlag = True
            if self._oauthToken_:
                self._typeUrl_ = 'https://oauth2:'+ self._oauthToken_ + '@' + type + '.com'
            else:
                self._typeUrl_ = 'https://'+type + '.com'
        else:
            scaResult = {
                "repo_license": ['Unsupported type'],
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
        except:
            scaResult = {
                "repo_license_legal": {
                    "pass": False,
                    "result_code": "",
                    "notice": "Git clone failed, invalid URL/Token",
                    "is_legal": {"pass": False,"license": [],"notice": "","detail": {}}
                },
                "spec_license_legal": {},
                "license_in_scope": {},
                "repo_copyright_legal": {
                    "pass": False,
                    "result_code": "",
                    "notice": "Git clone failed, invalid URL/Token",
                    "copyright": []
                }
            }
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

    
    @catch_error
    def locSca(self, path):
        try:
            temJsonSrc = SOURTH_PATH +'/tempJson'
            temJsonSrc = formateUrl(temJsonSrc)
            if os.path.exists(temJsonSrc) is False:
                os.makedirs(temJsonSrc)

            timestamp = int(time.time())
            localRepo = os.path.basename(path)
            tempJson = temJsonSrc + '/' + localRepo +str(timestamp)+'.txt'
            tempJson = formateUrl(tempJson)
            if os.path.exists(tempJson) is False:
                open(tempJson, 'w')

            self._type_ = "inde"
            reExt = extractCode(path)
            if reExt == "Except":
                logging.error("file extracCode error")
            elif reExt == "ref":
                self._type_ = "ref"          

            logging.info("==============START SCAN REPO==============")
            # Call scancode
            command = shlex.split(
                'scancode -l -c %s  --json %s -n 3 --timeout 10 --max-in-memory -1 --license-score 80' % (path, tempJson))
            resultCode = subprocess.Popen(command)
            while subprocess.Popen.poll(resultCode) == None:
                time.sleep(1)
            popKill(resultCode)

            scaJson = ''
            # Get json
            with open(tempJson, 'r+') as f:
                list = f.readlines()
                scaJson = "".join(list)
            logging.info("===============END SCAN REPO===============")
            anlyzePath = os.path.dirname(path)
            scaResult = getScaAnalyze(scaJson, anlyzePath, self._type_, "None", [])
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.exception("Error on %s: %s" % (command, e))
        finally:
            # Clear files
            os.chmod(tempJson, stat.S_IWUSR)
            os.remove(tempJson)
            return scaResult
        
    @catch_error
    def scaResult(self, path, threadNum):
        try:
            temJsonSrc = SOURTH_PATH +'/tempJson'
            temJsonSrc = formateUrl(temJsonSrc)
            if os.path.exists(temJsonSrc) is False:
                os.makedirs(temJsonSrc)

            timestamp = int(time.time())
            localRepo = os.path.basename(path)
            tempJson = temJsonSrc + '/' + localRepo +str(timestamp)+'.txt'
            tempJson = formateUrl(tempJson)
            if os.path.exists(tempJson) is False:
                open(tempJson, 'w')

            self._type_ = "inde"
            reExt = extractCode(path)
            if reExt == "Except":
                logging.error("file extracCode error")
            elif reExt == "ref":
                self._type_ = "ref"          

            logging.info("==============START SCAN REPO==============")
            # Call scancode
            command = shlex.split(
                'scancode -l -c %s  --json %s -n %s --timeout 10 --max-in-memory -1 --license-score 80' % (path, tempJson, threadNum))
            resultCode = subprocess.Popen(command)
            while subprocess.Popen.poll(resultCode) == None:
                time.sleep(1)
            popKill(resultCode)

            scaJson = ''
            # Get json
            with open(tempJson, 'r+') as f:
                list = f.readlines()
                scaJson = "".join(list)
            logging.info("===============END SCAN REPO===============")
            scaResult = getSourceData(scaJson, self._type_)
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.exception("Error on %s: %s" % (command, e))
        finally:
            os.chmod(tempJson, stat.S_IWUSR)
            os.remove(tempJson)
            return scaResult
        
    @catch_error
    def infoSca(self, url):
        try:
            self._oauthToken_ = os.environ.get("MAJUN_TOKEN")
            urlList = url.split("/")           
            self._prUrl_ = url            
            self._domain_ = urlList[2]
            self._owner_ = urlList[3]
            self._repo_ = urlList[4]
            self._tag_ = "repo"
            repo_tag = 0
            self._num_ = ''
            if "/pulls/" in url:
                repo_tag = 1
                self._tag_ = "pr"
                self._num_ = urlList[6]
                self._branch_ = 'pr_' + self._num_
                fetchUrl = 'pull/' + self._num_ + '/head:pr_' + self._num_

            if repo_tag == 0:
                query_data = (self._owner_, self._repo_)
                item_data = self._dbObject_.Query_sca_result(query_data)
                if item_data is None:
                    repo_data = (self._repo_, self._owner_, url, repo_tag, self._num_, '', 0)
                    data_id = self._dbObject_.add_sca_result(repo_data)
                else:
                    data_id = item_data['id']
                    repoData = ('', 0, data_id)
                    self._dbObject_.upd_sca_result(repoData)

            self._typeUrl_ = 'https://oauth2:'+ self._oauthToken_ + '@' + self._domain_
            self._gitUrl_ = self._typeUrl_ + '/' + self._owner_ + '/' + self._repo_ + '.git'           
            timestemp = int(time.time())
            tempSrc = self._repo_ + str(timestemp)

            if os.path.exists(TEMP_PATH) is False:
                os.makedirs(TEMP_PATH)
             
            self._repoSrc_ = TEMP_PATH + '/'+self._owner_ + '/' + tempSrc + '/' + self._repo_               
            self._anlyzeSrc_ = TEMP_PATH + '/' + self._owner_ + '/' + tempSrc
            self._delSrc_ = TEMP_PATH + '/'+self._owner_ + '/' + tempSrc  

            logging.info("=============START FETCH REPO==============")  
            if self._tag_ == 'pr':   
                repo = Repo.init(path=self._repoSrc_)
                self._gitRepo_ = repo
                self._git_ = repo.git
                remote = self._gitRepo_.create_remote('origin', self._gitUrl_)
                remote.fetch(fetchUrl, depth=1)
                self._git_.checkout(self._branch_)

                fileList =  self.getDiffFiles()    
                if fileList is None:
                    fileList = []
                self._repoSrc_ = self.createDiff(fileList) 
            else:
                Repo.clone_from(self._gitUrl_, self._repoSrc_, depth=1)    
                repo = Repo(self._repoSrc_)
            
            logging.info("==============END FETCH REPO===============")                 
            scaResult = self.scaResult(self._repoSrc_, 3)

            if repo_tag == 0:
                scaJson = pymysql.escape_string(str(scaResult))
                repoData = (scaJson, 1, data_id)
                self._dbObject_.upd_sca_result(repoData)
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.exception("Error on %s" % (e))
        finally:
            # Clean temporary files
            if self._delSrc_ != '':
                try:
                    cleanTemp(self._delSrc_)
                    os.chmod(self._delSrc_, stat.S_IRWXU)
                    os.rmdir(self._delSrc_)
                except:
                    pass
            return scaResult
    
    @catch_error
    def getDiffFiles(self):
        fileList = []
        repoStr = "Flag"
        http = urllib3.PoolManager()  
        authorToken = os.environ.get("MAJUN_TOKEN")
        url = 'https://gitee.com/api/v5/repos/'+self._owner_+'/'+self._repo_+'/pulls/'+ self._num_ +'/files?access_token='+authorToken
        response = http.request(
            'GET',
            url
        )         
        resStatus = response.status
        
        if resStatus == 404:
            raise Exception("Gitee API Fail")

        if resStatus == 403:
            raise Exception("Gitee API LIMIT")

        repoStr = response.data.decode('utf-8')
        temList = json.loads(repoStr)
        fileList.extend(temList)     
        return fileList
    
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