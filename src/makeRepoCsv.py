#!/usr/bin/python3
# -*- coding: utf-8 -*-

# 导入CSV安装包
import csv
import json

from tqdm import tqdm

from repoDb import RepoDb

def writeCsv():
    
    #获取所有数据
    dbObject = RepoDb()

    repoList = dbObject.Query_RepoByOrg('oepnEuler')
    
    # 1. 创建文件对象
    f = open('openEuler.csv','w',encoding='utf-8',newline='')

    # 2. 基于文件对象构建 csv写入对象
    csv_writer = csv.writer(f)

    # 3. 构建列表头
    csv_writer.writerow(["source","仓库名称","仓库地址","license","Fork数量","Star数量","是否有项目License","License是否不规范","非认可License","notice文件"])

    # 数据处理
    for item in tqdm(repoList,desc="Write repo CSV:", total=len(repoList),colour='green'):
        scaJson = item['sca_json']

        if scaJson is None:
            continue

        jsonData = json.loads(scaJson)
        licenseList =jsonData['files']

        for var in licenseList[:]:
             # 去除扫描空结果集
            if len(var['licenses']) == 0 :
                continue

            
            #判断license是否属于认证



        # 4. 写入csv文件内容
        csv_writer.writerow(["l",'18','男'])
        csv_writer.writerow(["c",'20','男'])
        csv_writer.writerow(["w",'22','女'])

    # 5. 关闭文件
    f.close()

if __name__ == '__main__':

    writeCsv()  