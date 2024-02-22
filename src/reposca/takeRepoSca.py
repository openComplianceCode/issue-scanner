
import logging
import os
import shlex
import stat
import subprocess
import time
import pymysql
from sqlalchemy import null

from tqdm import tqdm
import sys
sys.path.append("..")
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
    :param osUrl: Local repo path
    :param pack: Repo name
    :param isSrc: Is it a software package?  0 No  1 Yes
    '''

    packUrl =  osUrl + pack

    #Create temporary files
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
            #Check if scanned
            queryDb = RepoDb()
            repoData = (dir,pack)
            repo = queryDb.Query_Repo_ByName(repoData)

            if repo is None or (repo['sca_json'] != None and repo['sca_json'] != ''):
                continue

            #Call the compressed file in the decompressed file first
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

            #Call scancode
            command = shlex.split('scancode -l -c %s --json %s -n 5 --timeout 3 --license-score 70' % (dirUrl, tempJson))
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
            with open(tempJson, 'r+') as f:
                list = f.readlines()
                scaJson = "".join(list)
                f.truncate(0)

            scaJson = pymysql.escape_string(scaJson)
            dir = pymysql.escape_string(dir)
            repoData = (scaJson, pack, dir)
            dbObject = RepoDb()
            dbObject.Modify_Repo(repoData)
        
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

def cleanTemp(dirUrl):
        for delRoot, delDirs, delFiles in os.walk(dirUrl, topdown=False):
            for delName in delFiles: 
                try:
                    delUrl = os.path.join(delRoot, delName)
                    delUrl = formateUrl(delUrl)
                    os.chmod(delUrl, stat.S_IRWXU) 
                    os.remove(delUrl)
                except:
                    pass                
            for delName in delDirs:
                try:
                    delUrl = os.path.join(delRoot, delName)
                    delUrl = formateUrl(delUrl)
                    os.chmod(delUrl, stat.S_IRWXU) 
                    os.rmdir(delUrl)
                except:
                    pass

@catch_error
def checkMod(func, path):
    os.chmod(path, stat.S_IWRITE)
    func(path)


if __name__ == '__main__':
    scaRepo("E:/giteeFile/","OpenHarmony")