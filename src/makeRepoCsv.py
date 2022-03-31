#!/usr/bin/python3
# -*- coding: utf-8 -*-

from pyrpm.spec import Spec
import csv
import json
import jsonpath

from tqdm import tqdm

from repoDb import RepoDb

noticeList = ['notice','Third_Party_Open_Source_Software_Notice','readme','license','copyright']
repoList = ['license','readme','notice']

def writeCsv(osUrl,pack):
    
    #获取所有数据
    dbObject = RepoDb()

    repoList = dbObject.Query_RepoByOrg('src-openEuler')

    packUrl =  osUrl + pack
    
    # 1. 创建文件对象
    f = open(pack+'.csv','w',encoding='utf-8',newline='')

    # 2. 基于文件对象构建 csv写入对象
    csv_writer = csv.writer(f)

    # 3. 构建列表头
    csv_writer.writerow(["source","仓库名称","仓库地址","license","Fork数量","Star数量","是否有项目License","Spec License","非认可License","notice文件"])

    # 数据处理
    for item in tqdm(repoList,desc="Write repo CSV:", total=len(repoList),colour='green'):

        reLicensePathList = []
        specLicenseList = []
        scaJson = item['sca_json']

        haveLicense = "Un"
        isNotice = "否"
        approved = '是'
        unApproved = ''
        scaLicense = ''
        specLicense = ''


        if scaJson is None:
            isNotice = "未扫描"
            approved = '未扫描'
            unApproved = ''
            scaLicense = '未扫描'
        else:

            jsonData = json.loads(scaJson)

            itemPath = jsonpath.jsonpath(jsonData, '$.files[*].path')
            licenseList =jsonpath.jsonpath(jsonData, '$.files[*].licenses')
            copyrightList = jsonpath.jsonpath(jsonData, '$.files[*].copyrights')
            

            for i,var in tqdm(enumerate(licenseList),desc=item['repo_name']+"do license json:", total=len(licenseList),colour='blue') :

                path = itemPath[i]

                #判断是否含有notice文件
                if checkNotice(path) and len(copyrightList[i]) > 0 :
                    if isNotice == '否':
                        isNotice = "是, "

                    isNotice = isNotice + "("+path + "), "
                
                if ".spec" in path:
                    #提取spec里的许可证声明
                    fileUrl = packUrl +"/"+ path
                    spec = Spec.from_file(fileUrl)
                    if spec.license is not None:
                        specLicenseList.append(spec.license + "("+path+") ")

                if len(var) == 0 :
                    continue                    
                                 
                for pathLicense in var:

                    isLicenseText = pathLicense['matched_rule']['is_license_text']
                    #判断是否有项目license
                    if checkRepoLicense(path) and isLicenseText is True:
                        if haveLicense == 'Un':
                             haveLicense = '是'
                        
                        haveLicense = haveLicense + "("+path+")"
                    
                    spdx_name = pathLicense['spdx_license_key']
                    
                    #判断license是否属于认证
                    reLicense = dbObject.Check_license(spdx_name)

                    if len(reLicense) == 0 and path not in reLicensePathList:
                        approved = '否'
                        unApproved = unApproved + spdx_name + "("+path + "), "
                        reLicensePathList.append(path)

            approved = approved +" " + unApproved

        repoLicense = item['repo_license']
        
        if repoLicense is None and haveLicense == 'Un':
            haveLicense = "否"
        elif reLicense is not None:
            haveLicense = "是"

        if len(specLicenseList) > 0:
            specLicense = "".join(specLicenseList)

        csvData = [item['repo_org'],item['repo_name'],item['repo_url'],repoLicense,item['fork_num'],item['star_num'],haveLicense,specLicense,approved,isNotice]

        # 4. 写入csv文件内容
        csv_writer.writerow(csvData)

    # 5. 关闭文件
    f.close()


def checkNotice(path):
    # 检查是notice文件
    path = path.lower()

    pathLevel = path.split("/")
    if len(pathLevel) > 3:
        return False

    for item in noticeList:
        if item in path:
            return True
    
    return False

def checkRepoLicense(path):
    # 检查是项目许可证
    path = path.lower()

    pathLevel = path.split("/")
    if len(pathLevel) > 3:
        return False

    for item in repoList:
        if item in path:
            return True
    
    return False

if __name__ == '__main__':

    writeCsv("E:/giteeFile/","src-openEuler")  