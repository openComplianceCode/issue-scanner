#!/usr/bin/python3
# -*- coding: utf-8 -*-

# 导入CSV安装包
import csv
import json
import jsonpath

from tqdm import tqdm

from repoDb import RepoDb

def writeCsv():
    
    #获取所有数据
    dbObject = RepoDb()
    checkDb = RepoDb(name_db='license')

    repoList = dbObject.Query_RepoByOrg('openEuler')
    
    # 1. 创建文件对象
    f = open('openEuler.csv','w',encoding='utf-8',newline='')

    # 2. 基于文件对象构建 csv写入对象
    csv_writer = csv.writer(f)

    # 3. 构建列表头
    csv_writer.writerow(["source","仓库名称","仓库地址","license","Fork数量","Star数量","是否有项目License","License是否不规范","非认可License","notice文件","scancode_License_key"])

    # 数据处理
    for item in tqdm(repoList,desc="Write repo CSV:", total=len(repoList),colour='green'):

        tempLicense = []
        tempScaLicense = []
        scaJson = item['sca_json']

        isNotice = "否"
        approved = '是'
        unApproved = ''
        scaLicense = ''

        if scaJson is None:
            isNotice = "未扫描"
            approved = '未扫描'
            unApproved = ''
            scaLicense = '未扫描'
        else:

            jsonData = json.loads(scaJson)

            itemPath = jsonpath.jsonpath(jsonData, '$.files[*].path')
            licenseList =jsonpath.jsonpath(jsonData, '$.files[*].licenses')

            

            for i,var in tqdm(enumerate(licenseList),desc=item['repo_name']+"do license json:", total=len(licenseList),colour='blue') :

                path = itemPath[i]
                #判断是否含有notice文件
                if 'Notice' in path or 'Third_Party_Open_Source_Software_Notice' in path or 'notice' in path:
                    isNotice = "是, " + path
                
                if len(var) == 0 :
                    continue            
                
                for pathLicense in var:
                    
                    spdx_name = pathLicense['spdx_license_key']

                    #判断是否含有scancode标识
                    if 'LicenseRef-scancode' in spdx_name and spdx_name not in tempScaLicense:
                        scaLicense = scaLicense + spdx_name + "(" + path + "), "
                        tempScaLicense.append(spdx_name)
                        continue 

                    
                    #判断license是否属于认证
                    reLicense = checkDb.Check_license(spdx_name)

                    if len(reLicense) == 0 and spdx_name not in tempLicense:
                        approved = '否'
                        unApproved = unApproved + spdx_name + "("+path + "), "
                        tempLicense.append(spdx_name)

            approved = approved +" " + unApproved

        repoLicense = item['repo_license']
        haveLicense = "是"
        if repoLicense is None:
            haveLicense = "否"

        csvData = [item['repo_org'],item['repo_name'],item['repo_url'],repoLicense,item['fork_num'],item['star_num'],haveLicense,"",approved,isNotice,scaLicense]

        # 4. 写入csv文件内容
        csv_writer.writerow(csvData)

    # 5. 关闭文件
    f.close()

if __name__ == '__main__':

    writeCsv()  