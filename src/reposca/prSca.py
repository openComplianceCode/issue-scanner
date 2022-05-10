# -*- coding: utf-8 -*-
import logging
import os
from pickle import FALSE, TRUE
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

logger = logging.getLogger("reposca")

ACCESS_TOKEN = '694b8482b84b3704c70bceef66e87606'
GIT_URL = 'https://gitee.com'
SOURTH_PATH = 'E:/giteeFile'


def catch_error(func):
    def wrapper(*args, **kw):
        try:
            return func(*args, **kw)
        except Exception as e:
            logging.exception(e)

    return wrapper
    

@catch_error
def doSca(url):
    try:
        urlList = url.split("/")
        owner = urlList[3]
        repo = urlList[4]
        num = urlList[6]
        gitUrl = GIT_URL + '/' + owner + '/' + repo + '.git'
    
        #获取pr分支
        head, base = getPrBranch(owner, repo, num)
        if head == 403:
            return "ACCESS_TOKEN 无效、过期或已被撤销"
        elif head == 502:
            return "GITEE 服务器维护中"

        #获取pr文件path
        # pathList = getPrPath(owner, repo, num)
        # if pathList == 403:
        #     return "ACCESS_TOKEN 无效、过期或已被撤销"
        # elif head == 502:
        #     return "GITEE 服务器维护中"
        
        fetchUrl = 'pull/' + num + '/head:pr_' + num 
        
        # 创建临时文件
        current_dir = os.path.dirname(os.path.abspath(__file__))
        temFileSrc = current_dir+'/temSrc'
        temFileSrc = formateUrl(temFileSrc)
        
        if os.path.exists(temFileSrc) is False:
            os.makedirs(temFileSrc) 

        repoSrc = SOURTH_PATH +'/'+owner + '/' + repo
        anlyzeSrc = SOURTH_PATH +'/'+owner
        delSrc = ''
        if os.path.exists(repoSrc) is False:
            repoSrc = temFileSrc + '/'+owner + '/' + repo
            anlyzeSrc = temFileSrc + '/'+owner
            delSrc = repoSrc
            #拉取项目
            command = shlex.split('git clone --branch=%s %s %s' % (base[0], gitUrl, repoSrc))           
            resultCode = subprocess.Popen(command)
            while subprocess.Popen.poll(resultCode) == None:
                time.sleep(1)
        #拉取pr
        command = shlex.split('git fetch %s %s' % (gitUrl, fetchUrl))           
        resultCode = subprocess.Popen(command, cwd=repoSrc)
        while subprocess.Popen.poll(resultCode) == None:
            time.sleep(1)
        #切换分支
        command = shlex.split('git checkout pr_%s' % (num))          
        resultCode = subprocess.Popen(command, cwd=repoSrc)
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
        scaJson = getPrSca(repoSrc, repo, num)
        scaResult = getScaAnalyze(anlyzeSrc, scaJson)

        #清理临时文件
        if delSrc != '':
            cleanTemp(delSrc)
            os.chmod(delSrc, stat.S_IWUSR) 
            os.rmdir(delSrc)

        return scaResult

    except Exception as e:
        print("Error on %s: %s" % (command, e.strerror))


@catch_error   
def getPrBranch(owner, repo, number):
    '''
    :param owner: 仓库所属空间地址(企业、组织或个人的地址path)
    :param repo: 仓库路径(path)
    :param number: 	第几个PR，即本仓库PR的序数
    :return:head,base
    '''
    repoStr = "Flag"
    apiJson = ''
    http = urllib3.PoolManager()           
    url = 'https://gitee.com/api/v5/repos/' +owner+ '/' +repo+ '/pulls/' +number+ '?access_token='+ACCESS_TOKEN
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

# @catch_error
# def getPrPath(owner, repo, number):
#     '''
#     :param owner: 仓库所属空间地址(企业、组织或个人的地址path)
#     :param repo: 仓库路径(path)
#     :param number: 	第几个PR，即本仓库PR的序数
#     :return:文件路径List
#     '''
#     repoStr = "Flag"
#     apiJson = ''
#     http = urllib3.PoolManager()           
#     url = 'https://gitee.com/api/v5/repos/' +owner+ '/' +repo+ '/pulls/' +number+ '/files?access_token='+ACCESS_TOKEN
#     response = http.request('GET',url)
#     resStatus = response.status

#     while resStatus == '403':
#         return 403, 403
    
#     while resStatus == '502':
#         return 502, 502

#     repoStr = response.data.decode('utf-8')
#     apiJson = json.loads(repoStr)  
#     pathList = jsonpath.jsonpath(apiJson, '$[*].filename')

#     return pathList

@catch_error
def getPrSca(repoSrc, repo, num):
    '''
    :param repoSrc: 扫描项目路径
    :param pathList: 扫描文件路径List
    :return:扫描结果json
    '''
    current_dir = os.path.dirname(os.path.abspath(__file__))
    temJsonSrc = current_dir+'/tempJson'
    temJsonSrc = formateUrl(temJsonSrc)
    if os.path.exists(temJsonSrc) is False:
        os.makedirs(temJsonSrc) 

    tempJson = temJsonSrc + '/'+repo+'.txt'
    tempJson = formateUrl(tempJson)
    if os.path.exists(tempJson) is False:
        open(tempJson,'w')

    #调用先解压文件里得压缩文件
    command = shlex.split('extractcode %s' % (repoSrc))
    resultCode = subprocess.Popen(command)
    while subprocess.Popen.poll(resultCode) == None:
        time.sleep(1)
    #调用scancode
    command = shlex.split('scancode -l -c %s --max-depth 3 --json %s -n 5 --timeout 3' % (repoSrc, tempJson))
    resultCode = subprocess.Popen(command)
    while subprocess.Popen.poll(resultCode) == None:
        time.sleep(1)
    #切回master
    command = shlex.split('git checkout master')          
    resultCode = subprocess.Popen(command, cwd=repoSrc)
    while subprocess.Popen.poll(resultCode) == None:
        time.sleep(0.5)
    #删除临时分支
    command = shlex.split('git branch -D pr_%s' % (num))          
    resultCode = subprocess.Popen(command, cwd=repoSrc)
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

    #清空文件
    os.chmod(tempJson, stat.S_IWUSR) 
    os.remove(tempJson)
    
    return scaJson

@catch_error
def getScaAnalyze(anlyzeSrc, scaJson):
    '''
    :param repoSrc: 扫描文件路径
    :param repo: 项目名
    :param scaJson: 扫描结果json
    :return:分析结果json
    '''
    sca_result = {}
    specLicenseList = []
    pathList = []

    haveLicense = "FALSE"    
    isCopyright = "FALSE"
    approved = 'YES'
    specLicense = 'YES'
    noticeLicense = '缺少项目级许可证声明文件'
    noticeScope = ''
    noticeSpec = '无spec文件'
    noticeCopyright = '缺少项目级Copyright声明文件'

    jsonData = json.loads(scaJson)
    itemPath = jsonpath.jsonpath(jsonData, '$.files[*].path')
    licenseList =jsonpath.jsonpath(jsonData, '$.files[*].licenses')
    copyrightList = jsonpath.jsonpath(jsonData, '$.files[*].copyrights')
            
    #获取所有数据
    dbObject = RepoDb()
    licenseCheck = LicenseCheck()
    licenseCheck.load_config()
 
    for i,var in enumerate(licenseList):

        path = itemPath[i]

        #判断是否含有notice文件
        if checkNotice(path) and len(copyrightList[i]) > 0 :
            if isCopyright == 'FALSE':
                isCopyright = "YES"
                noticeCopyright = ""

            noticeCopyright = noticeCopyright + "("+path + "), "
                
        if ".spec" in path and checkPath(path):
            #提取spec里的许可证声明
            fileUrl = anlyzeSrc +"/"+ itemPath[i]
            spec = Spec.from_file(fileUrl)
            if spec.license is not None:
                licenses = licenseCheck.split_license(spec.license)
                licenses = licenseCheck.translate_license(licenses)
                isSpecLicense = licenseCheck.check_license_safe(licenses)
                if isSpecLicense == 'TRUE':
                    noticeSpec = 'spec_license: '+ spec.license
                elif isSpecLicense == 'FALSE':
                    specLicense = 'FALSE'
                    noticeSpec = 'spec_license: '+ spec.license + ' 声明不规范或非认可License'
                else:
                    specLicense = 'FALSE'
                    noticeSpec = 'spec_license: '+ spec.license + ' 需要Review'

                specLicenseList.append(spec.license)

        if len(var) == 0 :
            continue                    
                                 
        for pathLicense in var:

            isLicenseText = pathLicense['matched_rule']['is_license_text']
            #判断是否有项目license
            if checkRepoLicense(path) and isLicenseText is True and path not in pathList:
                if haveLicense == "FALSE":
                    haveLicense = "YES"
                    noticeLicense = ""
                    
                noticeLicense = noticeLicense + "("+path+"), "
                pathList.append(path)
                    
            spdx_name = pathLicense['spdx_license_key']
                    
            #判断license是否属于认证
            reLicense = dbObject.Check_license(spdx_name)

            if len(reLicense) == 0 and pathLicense['start_line'] != pathLicense['end_line'] and 'LicenseRef-scancode-' not in spdx_name:
                approved = "FALSE"
                noticeScope = noticeScope + spdx_name + "("+path + ", start_line: "+str(pathLicense['start_line'])+", end_line: "+str(pathLicense['end_line'])+"), "

    noticeLicense = noticeLicense.strip(', ')
    isCopyright = isCopyright.strip( ', ' )
    approved = approved.strip(', ')
    noticeSpec = noticeSpec.strip(', ')
    noticeCopyright = noticeCopyright.strip(', ')
    if noticeScope == '':
        noticeScope = 'OSI/FSF认证许可证'
    else:
        noticeScope = '存在非OSI/FSF认证许可证：' + noticeScope

    sca_result = {
        "repo_license_legal": {
            "pass": haveLicense,
            "result_type" : "string",
            "notice" : noticeLicense
        },
        "spec_license_legal": {
            "pass": specLicense,
            "result_type" : "string",
            "notice" : noticeSpec
        },
        "license_in_scope": {
            "pass": approved,
            "result_type" : "string",
            "notice" : noticeScope        
        },
        "repo_copyright_legal": {
            "pass": isCopyright,
            "result_type" : "string",
            "notice" : noticeCopyright
        }
    }

    return sca_result




@catch_error
def formateUrl(urlData):
    return urlData.replace("\\", "/")


@catch_error
def checkPath(path):
    # 检查是notice文件
    path = path.lower()

    pathLevel = path.split("/")
    if len(pathLevel) > 3:
        return False
    
    return True

