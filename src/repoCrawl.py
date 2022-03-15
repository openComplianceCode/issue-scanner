#-- coding: utf-8 --

import os
import shlex
import subprocess
import time
import pymysql
from tqdm import tqdm
import urllib3
import json

from repoDb import RepoDb


repoList = []
ACCESS_TOKEN = '694b8482b84b3704c70bceef66e87606'

PER_PAGE = 100

def refreshToken():
    # 获取token
    http = urllib3.PoolManager() 
    response = http.request('POST','https://gitee.com/oauth/token?grant_type=refresh_token&refresh_token='+ACCESS_TOKEN)
    print(response.data.decode('utf-8'))

    


def getRepoUrl(orgName):

    # 获取url项目下的所有相信
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
        # dbObject.Buid_data(tempReData)
        

        # 获取Maintainer
        maintanerList = getMiantainer(orgName, item["name"])

        for owner in tqdm(maintanerList,desc="Insert owner",total=len(maintanerList)):          
            ownerName = pymysql.escape_string(owner['name'])
            tempOwnerData = (item["id"], owner['id'], owner['login'], owner['html_url'], ownerName )

            #增加owner数据
            ownerData.append(tempOwnerData)
            # dbObject.Buid_OwnerData(tempOwnerData)

    dbObject.Buid_data(repoData)
    dbObject.Buid_OwnerData(ownerData)
        


def getRepoDetail():

    # 爬虫
    print()

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

def getApiResult(url, start):
    http = urllib3.PoolManager() 
    response = http.request('GET',url+'&page='+str(start)+'&per_page='+str(PER_PAGE))
    
    return response


def getRepoClone():

    # 下载repo
    dbObject = RepoDb()
    allRepo = dbObject.Query_AllRepo()

    for item in tqdm(allRepo,desc="git clone repo",total=len(allRepo),colour='green'):

        try:
            repoUrl = item['repo_url']
            name_space = item['repo_name']
            repoOrg = item['repo_org']

            if 'kernel' in name_space:
                continue

            if repoOrg == 'openEuler':
                if os.path.exists('E:/giteeFile/openEuler/'+name_space):
                    continue
                command = shlex.split('git clone %s %s' % (repoUrl, 'E:/giteeFile/openEuler/'+name_space))
            else:
                if os.path.exists('E:/giteeFile/srcOpenEuler/'+name_space):
                    continue
                command = shlex.split('git clone %s %s' % (repoUrl, 'E:/giteeFile/srcOpenEuler/'+name_space))
            
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
    
    # getRepoUrl('src-openEuler')

    getRepoClone()