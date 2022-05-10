#-- coding: utf-8 --

import logging
import os
import shlex
import subprocess
import time
from tokenize import Number
import pymysql
from requests import head
from tqdm import tqdm
import urllib3
import json

from reposca.repoDb import RepoDb
from reposca.takeRepoSca import formateUrl


repoList = []
ACCESS_TOKEN = '694b8482b84b3704c70bceef66e87606'
GIT_URL = 'https://gitee.com'

PER_PAGE = 100

def catch_error(func):
    def wrapper(*args, **kw):
        try:
            return func(*args, **kw)
        except Exception as e:
            logging.exception(e)

    return wrapper

@catch_error
def refreshToken():
    # 获取token
    http = urllib3.PoolManager() 
    response = http.request('POST','https://gitee.com/oauth/token?grant_type=refresh_token&refresh_token='+ACCESS_TOKEN)
    print(response.data.decode('utf-8'))
  

@catch_error
def getRepoUrl(orgName):

    # 获取url项目下的所有项目
    start = 1
    repoStr = "Flag"
    http = urllib3.PoolManager() 
    while repoStr != '[]':            
        url = 'https://gitee.com/api/v5/orgs/'+orgName+'/repos?access_token='+ACCESS_TOKEN+'&type=all'
        response = getApiResult(url, start)
        resStatus = response.status

        while resStatus == '403':
            refreshToken()
            response = http.request('GET',url)
            resStatus = response.status

        repoStr = response.data.decode('utf-8')
        temList = json.loads(repoStr)
        repoList.extend(temList)
        start+=1

    dbObject = RepoDb()

    repoData = []
    ownerData = []
    for item in tqdm(repoList,desc="Insert repo And Owner",total=len(repoList)):
        tempReData = (item["id"], item["name"], item['namespace']['name'], item['html_url'], item['license'], item['language'], item['forks_count'], item['stargazers_count'])
        # 新增repo数据
        repoData.append(tempReData)     
        # 获取Maintainer
        maintanerList = getMiantainer(orgName, item["name"])

        for owner in tqdm(maintanerList,desc="Insert owner",total=len(maintanerList)):          
            ownerName = pymysql.escape_string(owner['name'])
            tempOwnerData = (item["id"], owner['id'], owner['login'], owner['html_url'], ownerName )
            #增加owner数据
            ownerData.append(tempOwnerData)

    dbObject.Buid_data(repoData)
    dbObject.Buid_OwnerData(ownerData)
        
@catch_error
def getMiantainer(orgName, repoName):
    maintanerList = []
    start = 1
    repoStr = "Flag"
    http = urllib3.PoolManager() 
    while repoStr != '[]':            
        url = 'https://gitee.com/api/v5/repos/'+orgName+'/'+repoName+'/collaborators?access_token='+ACCESS_TOKEN
        response = getApiResult(url, start)
        resStatus = response.status

        while resStatus == '403':
            refreshToken()
            response = http.request('GET',url)
            resStatus = response.status

        repoStr = response.data.decode('utf-8')
        temList = json.loads(repoStr)
        maintanerList.extend(temList)
        start+=1
    
    return maintanerList

@catch_error
def getApiResult(url, start):
    http = urllib3.PoolManager() 
    response = http.request('GET',url+'&page='+str(start)+'&per_page='+str(PER_PAGE))
    
    return response

@catch_error
def getRepoClone(orgName, path):

    # 下载repo
    dbObject = RepoDb()
    repoOrg = (orgName)
    allRepo = dbObject.Query_RepoByOrg(repoOrg)

    for item in tqdm(allRepo,desc="git clone repo",total=len(allRepo),colour='green'):

        try:
            repoUrl = item['repo_url']
            name_space = item['repo_name']
            repoOrg = item['repo_org']

            if os.path.exists(path+'/'+orgName+'/'+name_space):
                continue
            command = shlex.split('git clone %s %s' % (repoUrl, path+'/'+orgName+'/'+name_space))
            
            resultCode = subprocess.Popen(command)
            while subprocess.Popen.poll(resultCode) == None:
                time.sleep(5)

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

        except Exception as e:
            print("Error on %s: %s" % (repoUrl, e.strerror))


if __name__ == '__main__':
    
    # getRepoUrl('MindSpore')

    # getRepoClone('MindSpore', 'E:/giteeFile/')
    refreshToken()