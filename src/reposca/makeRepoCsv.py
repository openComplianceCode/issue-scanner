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
    
    #Get all data
    dbObject = RepoDb()

    repoList = dbObject.Query_RepoByOrg(pack)

    packUrl =  osUrl + pack
    
    # 1. Create file object
    f = open(pack+'.csv','w',encoding='utf_8_sig',newline='')

    # 2. Build csv write object based on file object
    csv_writer = csv.writer(f)

    # 3. Build list header
    csv_writer.writerow(["source","repo_name","repo_url","license","repo license","Spec License","Non-approved License","Copyright file"])

    sca_result = []

    fileLicenseCheck = LicenseCheck('file')
    # data processing
    for item in tqdm(repoList,desc="Write repo CSV:", total=len(repoList),colour='green'):

        reLicensePathList = []
        specLicenseList = []
        scaJson = item['sca_json']

        haveLicense = "Un"
        isCopyright = "No"
        approved = 'Yes'
        unApproved = ''
        specLicense = ''


        if scaJson is None or scaJson == '':
            isCopyright = "Not scanned"
            approved = 'Not scanned'
            unApproved = ''
        else:

            jsonData = json.loads(scaJson)

            itemPath = jsonpath.jsonpath(jsonData, '$.files[*].path')
            licenseList =jsonpath.jsonpath(jsonData, '$.files[*].licenses')
            copyrightList = jsonpath.jsonpath(jsonData, '$.files[*].copyrights')
            

            for i,var in enumerate(licenseList):

                path = itemPath[i]

                #Determine whether there is a notice file
                if checkNotice(path, 3) and len(copyrightList[i]) > 0 :
                    if isCopyright == 'No':
                        isCopyright = "Yes, "

                    isCopyright = isCopyright + "("+path + "), "
                
                if path.endswith((".spec",)) and checkPath(path, 2):
                    #Extract the license statement in the spec
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
                    #Determine whether there is a project license
                    if checkRepoLicense(path, 3) and isLicenseText is True:
                        if haveLicense == 'Un':
                             haveLicense = 'Yes'
                        
                        haveLicense = haveLicense + "("+path+"),"
      
                    #Determine whether the license belongs to certification
                    spdxLicenses = infixToPostfix(spdx_name) 
                    fileLicense = fileLicenseCheck.check_license_safe(spdxLicenses)
                    reLicense = fileLicense.get('pass')

                    if reLicense is False and path not in reLicensePathList and pathLicense['start_line'] != pathLicense['end_line']:
                        approved = 'No'
                        unApproved = unApproved + spdx_name + "("+path + ", start_line: "+str(pathLicense['start_line'])+", end_line: "+str(pathLicense['end_line'])+"), "
                        reLicensePathList.append(path)

            approved = approved +" " + unApproved

        repoLicense = item['repo_license']
        
        if repoLicense is None and haveLicense == 'Un':
            haveLicense = "No"
        elif repoLicense is not None and haveLicense == 'Un':
            haveLicense = "Yes"

        if len(specLicenseList) > 0:
            specLicense = "".join(specLicenseList)

        isCopyright.strip( ', ' )
        approved.strip(', ')

        #Update data
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

        # 4. Write csv file content
        csv_writer.writerow(csvData)


    # 5. close file
    f.close()

    sca_result.sort(key=lambda x: x['repoName'], reverse=True)

    return sca_result

if __name__ == '__main__':

    writeCsv("E:/giteeFile/","OpenHarmony")  