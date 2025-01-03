



import json
import logging
import os
import random
import shlex
import stat
import subprocess
import time
import pymysql
import urllib3
import jsonpath
from git.repo import Repo

import yaml
from tqdm import tqdm
from reposca.repoDb import RepoDb
from reposca.licenseCheck import LicenseCheck
from reposca.analyzeSca import checkNotice, checkRepoLicense, mergDetial
from reposca.takeRepoSca import cleanTemp
from util.postOrdered import infixToPostfix
from util.popUtil import popKill
from util.catchUtil import catch_error
from util.formateUtil import formateUrl

PER_PAGE = 100
TEMP_PATH = '/home/repo/schedulRepo'
class ScheduleSca(object):

    def __init__(self):
        #Connect to the database
        self._dbObject_ = RepoDb(
            host_db = os.environ.get("MYSQL_HOST"), 
            user_db = os.environ.get("MYSQL_USER"), 
            password_db = os.environ.get("MYSQL_PASSWORD"), 
            name_db = os.environ.get("MYSQL_DB_NAME"), 
            port_db = int(os.environ.get("MYSQL_PORT")))

    @catch_error    
    def sca_repo(self):
        project_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))      
        config_org = project_path + '/org.yaml'
        CONF = yaml.safe_load(open(config_org))
        params = CONF['ORG']
        org_list = params.split(",")
        for item in org_list:
            item = item.strip()
            item_list = self.get_repo_url(item)
            self.sca_item(item_list, item)

    

    @catch_error
    def get_repo_url(self, orgName):

        # Get all items under the url item
        start = 1
        repoStr = "Flag"
        http = urllib3.PoolManager()   
        authorToken = os.environ.get("MAJUN_TOKEN")
        repoList = []
        while repoStr != '[]':            
            url = 'https://gitee.com/api/v5/orgs/'+orgName+'/repos?access_token='+authorToken+'&type=all'
            response = self.get_api_result(url, start)
            resStatus = response.status

            while resStatus == 403:
                response = http.request('GET',url)
                resStatus = response.status
            if resStatus == 404:
                continue

            repoStr = response.data.decode('utf-8')
            temList = json.loads(repoStr)
            repoList.extend(temList)
            start+=1

        return repoList
    
    @catch_error
    def get_api_result(self, url, start):
        http = urllib3.PoolManager() 
        response = http.request('GET',url+'&page='+str(start)+'&per_page='+str(PER_PAGE))        
        return response

    @catch_error
    def sca_item(self, itemList, org):
        try:
            if os.path.exists(TEMP_PATH) is False:
                os.makedirs(TEMP_PATH)
            desc = "SCAN " + org + " REPO"
            ticks = time.localtime()
            monstr = str(ticks.tm_year) + str(ticks.tm_mon)
            authorToken = os.environ.get("MAJUN_TOKEN")
            for item in tqdm(itemList,desc=desc,total=len(itemList),colour='green'):
                repo_org = item['namespace']['name']
                if repo_org.lower() != org:
                    continue
                url = item['html_url']
                repo_name = item["name"] 
                #check
                repo_check = self._dbObject_.Query_Repo_Sca((repo_org, repo_name, monstr))
                if repo_check is not None:
                    continue
                repo_src = TEMP_PATH + '/'+repo_org + '/' + repo_name          
                if os.path.exists(repo_src) is False:
                    os.makedirs(repo_src)
                del_src = TEMP_PATH + '/'+repo_org
                command = shlex.split('git clone https://oauth2:%s@gitee.com/%s/%s.git  %s --depth=1' % (authorToken, repo_org, repo_name, repo_src))
                result_code = subprocess.Popen(command)
                while subprocess.Popen.poll(result_code) == None:
                    time.sleep(5)
                popKill(result_code)
                tem_json = TEMP_PATH + '/'+repo_org  +'/' + repo_name + 'tempJson'
                tem_json = formateUrl(tem_json)
                if os.path.exists(tem_json) is False:
                    os.makedirs(tem_json)

                tem_json = tem_json + '/' + repo_name +'.txt'
                tem_json = formateUrl(tem_json)
                if os.path.exists(tem_json) is False:
                    open(tem_json, 'w')

                # Call scancode
                command = shlex.split(
                    'scancode -l -c %s  --json %s -n 3 --timeout 10 --max-in-memory -1 --license-score 80' % (repo_src, tem_json))
                result_code = subprocess.Popen(command)
                while subprocess.Popen.poll(result_code) == None:
                    time.sleep(1)
                popKill(result_code)
                sca_json = ''
                # Get json
                with open(tem_json, 'r+') as f:
                    list = f.readlines()
                    sca_json = "".join(list)
                
                sca_res = self.sca_analyze(sca_json)
                # Save to database
                # sca_json = pymysql.escape_string(sca_json)
                repoLicLg = sca_res['repo_license_legal']
                specLicLg = sca_res['spec_license_legal']
                licScope = sca_res['license_in_scope']
                copyrightLg = sca_res['repo_copyright_legal']
                repoLicense = ','.join(repoLicLg['is_legal']['license'])
                repoLicLg = pymysql.escape_string(str(repoLicLg))
                specLicLg = pymysql.escape_string(str(specLicLg))
                licScope = pymysql.escape_string(str(licScope))
                copyrightLg = pymysql.escape_string(str(copyrightLg))           
                repo_score, scope_score, copy_score = self.get_score(sca_res)
                repo_data = (repo_name, repo_org, url, repoLicense, repoLicLg, specLicLg,\
                    licScope, copyrightLg, "master", int(monstr), repo_score, scope_score, copy_score)
                self._dbObject_.add_repo_sca(repo_data)
                try:
                    if del_src != '':
                        cleanTemp(del_src)
                        os.chmod(del_src, stat.S_IRWXU)
                        os.rmdir(del_src)
                except:
                        pass

        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.exception("Error on %s" % (e))

    @catch_error      
    def sca_analyze(self, sca_json):

        sca_result = {}
        itemPathList = []

        haveLicense = False
        isCopyright = False
        approved = True
        specLicense = False
        itemLicense = False
        noticeItemLic = '缺少项目级License声明文件'
        itemDetial = {}
        itemLicList = []
        noticeLicense = '缺少项目级License声明文件'
        noticeScope = ''
        noticeSpec = '无spec文件'
        noticeCopyright = '缺少项目级Copyright声明文件'
        checkCopyright = ''
        failCopList = []
        loseCopList = []
        crInfoList = []
        speLicDetial = {}
        self._scope_list_ = 0

        json_data = json.loads(sca_json)
        item_path = jsonpath.jsonpath(json_data, '$.files[*].path')
        license_list = jsonpath.jsonpath(json_data, '$.files[*].licenses')
        copyright_list = jsonpath.jsonpath(json_data, '$.files[*].copyrights')

        logging.info("===========START ANALYZE RESULT============")
        file_check = LicenseCheck('file', 'osf')
        repo_check = LicenseCheck('repo', 'osf')
        path_depth = 3
        if license_list is False:
            license_list = []
        itemLicFlag = False
        for i, var in enumerate(license_list):   
            path = item_path[i]
            # Determine whether the project copyrgiht file is included
            if checkNotice(path, path_depth) and len(copyright_list[i]) > 0:
                if isCopyright is False:
                    isCopyright = True
                    noticeCopyright = ""
                copyrightInfo = copyright_list[i]
                for info in copyrightInfo:
                    crInfoList.append(info['copyright'])
                noticeCopyright = noticeCopyright + "(" + path + "), "

            if len(var) == 0:
                continue
            for pathLicense in var:
                spdx_name = pathLicense['spdx_license_key']
                if 'LicenseRef-scancode-' in spdx_name:
                    if "public-domain" in spdx_name:
                        spdx_name = "Public Domain"
                    elif "mulanpsl" in spdx_name or 'utopia' in spdx_name:
                        spdx_name = spdx_name.split("LicenseRef-scancode-")[1]
                    else:
                        continue
                spdxLicenses = infixToPostfix(spdx_name)
                # Determine whether there is a repo license
                if checkRepoLicense(path, path_depth):
                    if haveLicense is False:
                        haveLicense = True
                        noticeLicense = ""
                        # Determine whether the repo license is approved
                        itemLicCheck = repo_check.check_license_safe(spdxLicenses)
                        itemLicense = itemLicCheck.get('pass')
                        noticeItemLic = itemLicCheck.get('notice')
                        itemDetial = itemLicCheck.get('detail')
                        itemLicList.append(spdx_name)
                        itemPathList.append(path)
                        if path.lower().endswith(("license",)):
                            itemLicFlag = True
                    elif path.lower().endswith(("license",)) and path not in itemPathList and itemLicFlag is False:
                        # Determine whether the repo license is approved
                        itemLicCheck = repo_check.check_license_safe(spdxLicenses)
                        itemLicense = itemLicCheck.get('pass')
                        noticeItemLic = itemLicCheck.get('notice')
                        itemDetial = itemLicCheck.get('detail')
                        itemLicList.clear()
                        itemPathList.clear()
                        itemLicList.append(spdx_name)
                        itemPathList.append(path)
                    elif path in itemPathList and spdx_name not in itemLicList:
                        # Check the same file
                        itemLicCheck = repo_check.check_license_safe(spdxLicenses)
                        itemLicTemp = itemLicCheck.get('pass')
                        if itemLicTemp is False:
                            itemLicense = itemLicTemp
                            if noticeItemLic != '通过':
                                noticeItemLic = noticeItemLic + "。" + itemLicCheck.get('notice')
                            else:
                                noticeItemLic = itemLicCheck.get('notice')
                            itemDetial = mergDetial(itemDetial, itemLicCheck.get('detail'))
                        itemLicList.append(spdx_name)
                else:
                    # Determine whether the license belongs to certification
                    fileLicense = file_check.check_license_safe(spdxLicenses)
                    reLicense = fileLicense.get('pass')
                    spdLower = spdx_name.lower()
                    if reLicense is False and pathLicense['start_line'] != pathLicense['end_line'] and 'exception' not in spdLower and 'doc' != spdLower:
                        approved = False
                        noticeScope = noticeScope + spdx_name + "("+path + ", start_line: "+str(
                            pathLicense['start_line'])+", end_line: "+str(pathLicense['end_line'])+"), " 
                        self._scope_list_+=1

        if len(itemPathList) == 0:
            itemPathList.append(noticeLicense)
        if len(failCopList) > 0:
            tempFail = '、'.join(failCopList)
            checkCopyright = checkCopyright + tempFail + "文件Copyright校验不通过, "
        if len(loseCopList) > 0:
            tempLose = '、'.join(loseCopList)
            checkCopyright = checkCopyright + tempLose + "文件缺失Copyright声明, "
        if checkCopyright != '':
            noticeCopyright = checkCopyright + " Copyright path：" + noticeCopyright
        noticeCopyright = noticeCopyright.strip(', ')
        noticeScope = noticeScope.strip(', ')
        if noticeScope == '':
            noticeScope = '准入License'
        else:
            noticeScope = '存在非准入License：' + noticeScope + ' License准入列表请参考 https://compliance.openeuler.org/license-list, 若需对License发起准入申请，请联系合规SIG组'

        sca_result = {
            "repo_license_legal": {
                "pass": haveLicense,
                "result_code": "",
                "notice": itemPathList[0],
                "is_legal": {
                    "pass": itemLicense,
                    "license": itemLicList,
                    "notice": noticeItemLic,
                    "detail": itemDetial
                }
            },
            "spec_license_legal": {
                "pass": specLicense,
                "result_code": "",
                "notice": noticeSpec,
                "detail": speLicDetial
            },
            "license_in_scope": {
                "pass": approved,
                "result_code": "",
                "notice": noticeScope
            },
            "repo_copyright_legal": {
                "pass": isCopyright,
                "result_code": "",
                "notice": noticeCopyright,
                "copyright": crInfoList
            }
        }
        logging.info("============END ANALYZE RESULT=============")

        return sca_result

    @catch_error
    def get_score(self, sca_result):
        repo_lic = sca_result['repo_license_legal']
        copy_legal = sca_result['repo_copyright_legal']
        repo_lic_list = repo_lic['is_legal']['license']
        repo_score = 0
        if len(repo_lic_list) > 0:
            repo_score = 25
        scope_score = 15 - self._scope_list_*0.1
        if scope_score < 0:
            scope_score = 0
        copy_pass = copy_legal['pass']
        copy_score = 0
        if copy_pass:
            copy_score = 5
        
        return repo_score, scope_score, copy_score
        