
from genericpath import getsize
import logging
from ntpath import join
import os
import shlex
import stat
import subprocess
import tarfile
import time
import traceback
from isort import file
import pymysql
from sqlalchemy import null

from tqdm import tqdm

from reposca.repoDb import RepoDb

def catch_error(func):
    def wrapper(*args, **kw):
        try:
            return func(*args, **kw)
        except Exception as e:
            logging.exception(e)

    return wrapper

@catch_error
def scaRepo(osUrl,pack):
    
    '''
    :param osUrl: 本地存仓库目录
    :param pack: 仓库命
    :param isSrc: 是否是软件包  0 不是  1 是
    '''

    packUrl =  osUrl + pack

    #创建临时文件
    current_dir = os.path.dirname(os.path.abspath(__file__))
    temFileSrc = current_dir+'/temp'
    temFileSrc = formateUrl(temFileSrc)
    tempJson = current_dir+'/json.txt'
    tempJson = formateUrl(tempJson)

    if os.path.exists(temFileSrc) is False:
        os.makedirs(temFileSrc)

    if os.path.exists(tempJson) is False:
        open(tempJson,'w')

    for root,dirs,files in os.walk(packUrl): 
        for dir in tqdm(dirs,desc="SCANING REPO:",total=len(dirs),colour='green'):

            dirUrl = os.path.join(root,dir)
            dirUrl = formateUrl(dirUrl)
            #检查是否已扫描
            queryDb = RepoDb()
            repoData = (dir,pack)
            repo = queryDb.Query_Repo_ByName(repoData)

            if repo is None or (repo['sca_json'] != None and repo['sca_json'] != ''):
                continue

            #调用先解压文件里得压缩文件
            command = shlex.split('extractcode %s' % (dirUrl))
            resultCode = subprocess.Popen(command)
            while subprocess.Popen.poll(resultCode) == None:
                time.sleep(1)
            
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

            #调用scancode
            command = shlex.split('scancode -l -c %s --json %s -n 5 --timeout 3' % (dirUrl, tempJson))
            resultCode = subprocess.Popen(command)
            while subprocess.Popen.poll(resultCode) == None:
                time.sleep(10)
            
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
                f.truncate(0)

            #修改数据库
            scaJson = pymysql.escape_string(scaJson)
            dir = pymysql.escape_string(dir)
            repoData = (scaJson, pack, dir)
            dbObject = RepoDb()
            dbObject.Modify_Repo(repoData)
        
        #停止遍历子目录
        break

@catch_error
def formateUrl(urlData):
    return urlData.replace("\\", "/")

@catch_error
def checkWrar(filePath):
    if 'tar.gz' in filePath:
        return True
    elif 'tar.bz2' in filePath:
        return True
    elif 'tar.xz' in filePath:
        return True
    elif '.tgz' in filePath:
        return True
    else:
        return False

@catch_error
def cleanTemp(dirUrl):
    #清空临时解压目录   
    for delRoot, delDirs, delFiles in os.walk(dirUrl, topdown=False):
        for delName in delFiles:
            delUrl = os.path.join(delRoot, delName)
            delUrl = formateUrl(delUrl)
            #防止文件拒绝访问
            os.chmod(delUrl, stat.S_IWUSR) 
            os.remove(delUrl) 
                            
        for delName in delDirs:
            delUrl = os.path.join(delRoot, delName)
            delUrl = formateUrl(delUrl)
            #防止文件拒绝访问
            os.chmod(delUrl, stat.S_IWUSR) 
            os.rmdir(delUrl)

if __name__ == '__main__':
    scaRepo("E:/giteeFile/","openEuler")