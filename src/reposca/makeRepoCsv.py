#!/usr/bin/python3
# -*- coding: utf-8 -*-

import logging
from pyrpm.spec import Spec
import csv
import json
import jsonpath

from tqdm import tqdm
import sys
from reposca.analyzeSca import checkNotice, checkPath, checkRepoLicense
sys.path.append("..")
from reposca.repoDb import RepoDb
from reposca.licenseCheck import LicenseCheck
from util.postOrdered import infixToPostfix


def catch_error(func):
    def wrapper(*args, **kw):
        try:
            return func(*args, **kw)
        except Exception as e:
            logging.exception(e)

    return wrapper

@catch_error
def writeCsv(osUrl,pack):
    
    #获取所有数据
    dbObject = RepoDb()

    repoList = dbObject.Query_RepoByOrg(pack)

    packUrl =  osUrl + pack
    
    # 1. 创建文件对象
    f = open(pack+'.csv','w',encoding='utf_8_sig',newline='')

    # 2. 基于文件对象构建 csv写入对象
    csv_writer = csv.writer(f)

    # 3. 构建列表头
    csv_writer.writerow(["source","仓库名称","仓库地址","license","是否有项目License","Spec License","非认可License","Copyright文件"])

    sca_result = []

    fileLicenseCheck = LicenseCheck('file')
    # 数据处理
    for item in tqdm(repoList,desc="Write repo CSV:", total=len(repoList),colour='green'):

        reLicensePathList = []
        specLicenseList = []
        scaJson = item['sca_json']

        haveLicense = "Un"
        isCopyright = "否"
        approved = '是'
        unApproved = ''
        specLicense = ''


        if scaJson is None or scaJson == '':
            isCopyright = "未扫描"
            approved = '未扫描'
            unApproved = ''
        else:

            jsonData = json.loads(scaJson)

            itemPath = jsonpath.jsonpath(jsonData, '$.files[*].path')
            licenseList =jsonpath.jsonpath(jsonData, '$.files[*].licenses')
            copyrightList = jsonpath.jsonpath(jsonData, '$.files[*].copyrights')
            

            for i,var in enumerate(licenseList):

                path = itemPath[i]

                #判断是否含有notice文件
                if checkNotice(path, 3) and len(copyrightList[i]) > 0 :
                    if isCopyright == '否':
                        isCopyright = "是, "

                    isCopyright = isCopyright + "("+path + "), "
                
                if path.endswith((".spec",)) and checkPath(path, 2):
                    #提取spec里的许可证声明
                    fileUrl = packUrl +"/"+ path
                    spec = Spec.from_file(fileUrl)
                    if spec.license is not None:
                        specLicenseList.append(spec.license + "("+path+") ")

                if len(var) == 0 :
                    continue                    
                                 
                for pathLicense in var:
                    spdx_name = pathLicense['spdx_license_key']
                    if 'LicenseRef-scancode-' in spdx_name:
                        continue
                    isLicenseText = pathLicense['matched_rule']['is_license_text']
                    #判断是否有项目license
                    if checkRepoLicense(path, 3) and isLicenseText is True:
                        if haveLicense == 'Un':
                             haveLicense = '是'
                        
                        haveLicense = haveLicense + "("+path+"),"
      
                    #判断license是否属于认证
                    spdxLicenses = infixToPostfix(spdx_name) 
                    fileLicense = fileLicenseCheck.check_license_safe(spdxLicenses)
                    reLicense = fileLicense.get('pass')

                    if reLicense is False and path not in reLicensePathList and pathLicense['start_line'] != pathLicense['end_line']:
                        approved = '否'
                        unApproved = unApproved + spdx_name + "("+path + ", start_line: "+str(pathLicense['start_line'])+", end_line: "+str(pathLicense['end_line'])+"), "
                        reLicensePathList.append(path)

            approved = approved +" " + unApproved

        repoLicense = item['repo_license']
        
        if repoLicense is None and haveLicense == 'Un':
            haveLicense = "否"
        elif repoLicense is not None and haveLicense == 'Un':
            haveLicense = "是"

        if len(specLicenseList) > 0:
            specLicense = "".join(specLicenseList)

        isCopyright.strip( ', ' )
        approved.strip(', ')

        #更新数据
        repoData = (haveLicense, specLicense, approved, isCopyright, item['id'])
        dbObject.Modify_RepoSca(repoData)

        sca_result.append({
            'source': item['repo_org'],
            'repoName': item['repo_name'],
            'repoUrl': item['repo_url'],
            'license': repoLicense,
            'itemLicense': haveLicense,
            'specLicense': specLicense,
            'approved': approved,
            'isCopyright': isCopyright
        })

        csvData = [item['repo_org'],item['repo_name'],item['repo_url'],repoLicense,haveLicense,specLicense,approved,isCopyright]

        # 4. 写入csv文件内容
        csv_writer.writerow(csvData)


    # 5. 关闭文件
    f.close()

    sca_result.sort(key=lambda x: x['repoName'], reverse=True)

    return sca_result

if __name__ == '__main__':

    writeCsv("E:/giteeFile/","OpenHarmony")  