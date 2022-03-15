

from genericpath import getsize
from ntpath import join
import os
import shlex
import subprocess
import time
import pymysql
from sqlalchemy import null

from tqdm import tqdm

from repoDb import RepoDb


def scaRepo(pack):
    

    packUrl = "E:/giteeFile/" + pack
    for root,dirs,files in os.walk(packUrl): 
        for dir in tqdm(dirs,desc="SCANING REPO:",total=len(dirs),colour='green'):

            dirUrl = os.path.join(root,dir)
            dirUrl = dirUrl.replace("\\", "/")

            size = 0
            for r,currDir,curFiles in os.walk(dirUrl):  
                size += sum([getsize(join(r, name)) for name in curFiles])

            #过滤大文件
            if size > 500000000:
                continue

            #检查是否已扫描
            queryDb = RepoDb()
            repo = queryDb.Query_Repo_ByName(dir)
            if repo['sca_json'] != None:
                continue

            #调用scancode
            command = shlex.split('scancode -l -c %s --json %s' % (dirUrl, 'C:/Users/ASUS/Desktop/json.txt'))
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
            with open('C:/Users/ASUS/Desktop/json.txt', 'r+') as f:
                list = f.readlines()
                scaJson = "".join(list)

                #清空文件
                f.truncate(0)
            

            #修改数据库
            scaJson = pymysql.escape_string(scaJson)
            dir = pymysql.escape_string(dir)
            if pack == 'srcOpenEuler':
                pack = 'src-openEuler'
            repoData = (scaJson, pack, dir)
            dbObject = RepoDb()
            dbObject.Modify_Repo(repoData)




if __name__ == '__main__':

    scaRepo("openEuler")

    scaRepo("srcOpenEuler")