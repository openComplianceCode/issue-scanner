
from genericpath import getsize
from ntpath import join
import os
import shlex
import stat
import subprocess
import tarfile
import time
import traceback
import pymysql
from sqlalchemy import null

from tqdm import tqdm

from repoDb import RepoDb


def scaRepo(osUrl,pack,isSrc):
    
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

            if dir == 'ovirt-ansible-cluster-upgrade':
                continue

            #检查是否已扫描
            queryDb = RepoDb()

            repoData = (dir,pack)
            repo = queryDb.Query_Repo_ByName(repoData)

            if repo is None or repo['sca_json'] != None :
                continue

            dirUrl = os.path.join(root,dir)
            dirUrl = formateUrl(dirUrl)

            if isSrc == 1:
                flag = 0
                #解压扫描
                for deRoot,deDir,deFiles in os.walk(dirUrl):  
                    for defile in deFiles:
                        
                        dePath = os.path.join(deRoot,defile)
                        dePath = formateUrl(dePath)

                        #判断压缩文件
                        gzfile = defile.split(".")
                        if gzfile[len(gzfile) - 1] == 'gz':
                            flag = 1

                            try:
                                t = tarfile.open(dePath)
                                t.extractall(path = temFileSrc)
                                
                            except Exception as e:
                                traceback.print_exc()
                            
                            finally:
                                t.close()

                
                if flag == 0:
                    continue

                dirUrl = temFileSrc
            

            size = 0
            for r,currDir,curFiles in os.walk(dirUrl):  
                size += sum([getsize(join(r, name)) for name in curFiles])

            #过滤大文件
            if size > 200000000:

                cleanTemp(dirUrl)
                continue

            

            #调用scancode
            command = shlex.split('scancode -l -c %s --json %s' % (dirUrl, tempJson))
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
                
                if isSrc == 1:
                    cleanTemp(dirUrl)

            #修改数据库
            scaJson = pymysql.escape_string(scaJson)
            dir = pymysql.escape_string(dir)
            repoData = (scaJson, pack, dir)
            dbObject = RepoDb()
            dbObject.Modify_Repo(repoData)


def formateUrl(urlData):
    return urlData.replace("\\", "/")

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

    # scaRepo("E:/giteeFile/","openEuler",0)

    scaRepo("E:/giteeFile/","src-openEuler",1)