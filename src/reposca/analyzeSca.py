import json
import logging
import re
import jsonpath
from reposca.licenseCheck import LicenseCheck
from util.catchUtil import catch_error
from util.postOrdered import infixToPostfix
from pyrpm.spec import Spec

noticeList = ['notice', 'third_party_open_source_software_notice','readme', 'copying', 'copyright']
repoList = ['license', 'readme', 'notice', 'copying', 'third_party_open_source_software_notice', 'copyright', '.spec']
SOURTH_PATH = '/home/giteeFile'


@catch_error
def getScaAnalyze(scaJson, anlyzeSrc, type, copyright_type, file_array):
    '''
    :param repoSrc: scan file paths
    :param repo: repo name
    :param scaJson: scan result json
    :return:analysis result json
    '''
    sca_result = {}
    specLicenseList = []
    itemPathList = []

    haveLicense = False
    specFlag = True
    isCopyright = False
    approved = True
    specLicense = False
    itemLicense = False
    noticeItemLic = '缺少项目级License声明文件'
    itemDetial = {}
    itemLicList = []
    noticeLicense = '缺少项目级License声明文件'
    noticeScope = ''
    noticeSpec = '无spec文件'
    noticeCopyright = '缺少项目级Copyright声明文件'
    checkCopyright = ''
    failCopList = []
    loseCopList = []
    crInfoList = []
    speLicDetial = {}

    jsonData = json.loads(scaJson)
    itemPath = jsonpath.jsonpath(jsonData, '$.files[*].path')
    licenseList = jsonpath.jsonpath(jsonData, '$.files[*].licenses')
    copyrightList = jsonpath.jsonpath(jsonData, '$.files[*].copyrights')

    logging.info("===========START ANALYZE RESULT============")
    fileLicenseCheck = LicenseCheck('file', 'indelic')
    licenseCheck = LicenseCheck('repo', 'indelic')
    pathDepth = 3
    if type == 'ref':
        pathDepth = 4
    if licenseList is False:
        licenseList = []
    itemLicFlag = False
    for i, var in enumerate(licenseList):   
        path = itemPath[i]
        # Determine whether the project copyrgiht file is included
        if checkNotice(path, pathDepth) and len(copyrightList[i]) > 0:
            if isCopyright is False:
                isCopyright = True
                noticeCopyright = ""
            copyrightInfo = copyrightList[i]
            for info in copyrightInfo:
                crInfoList.append(info['copyright'])
            noticeCopyright = noticeCopyright + "(" + path + "), "
        
        #Check commit file copyright
        if is_in(path, file_array) and copyright_type == 'Huawei':
            if len(copyrightList[i]) > 0:
                copyrightInfo = copyrightList[i]
                for info in copyrightInfo:
                    if copyright_check(info['copyright']) is None:
                        isCopyright = False
                        failCopList.append(path)
            else:
                loseCopList.append(path)


        if path.endswith((".spec",)) and checkPath(path, 2):
            # Extract the license statement in the spec
            fileUrl = anlyzeSrc + "/" + itemPath[i]
            try:
                spec = Spec.from_file(fileUrl)
                specLic = spec.license
                if  specLic is not None:
                    if 'all_license' in specLic:
                        licenses = infixToPostfix(spec.all_license)
                        specLic = spec.all_license
                    else:
                        licenses = infixToPostfix(specLic)
                    isSpecLicense = licenseCheck.check_license_safe(licenses)
                    specLicense = isSpecLicense.get('pass')
                    noticeSpec = isSpecLicense.get('notice')
                    speLicDetial = isSpecLicense.get('detail')
                    specLicenseList.append(specLic)
                    if haveLicense is False or type == 'ref':
                        specFlag = False
                        haveLicense = True
                        noticeLicense = ""
                        itemLicList.clear()
                        itemPathList.clear()
                        itemLicList.append(specLic)
                        itemPathList.append(path)
                        itemLicense = specLicense
                        noticeItemLic = noticeSpec
                        itemDetial = speLicDetial
            except Exception as e:
                logging.exception(e) 
                pass

        if len(var) == 0:
            continue
        for pathLicense in var:
            spdx_name = pathLicense['spdx_license_key']
            if 'LicenseRef-scancode-' in spdx_name:
                if "public-domain" in spdx_name:
                    spdx_name = "Public Domain"
                elif "mulanpsl" in spdx_name or 'utopia' in spdx_name:
                    spdx_name = spdx_name.split("LicenseRef-scancode-")[1]
                else:
                    continue
            spdxLicenses = infixToPostfix(spdx_name)
            # Determine whether there is a repo license
            if checkRepoLicense(path, pathDepth) and specFlag:
                if haveLicense is False:
                    haveLicense = True
                    noticeLicense = ""
                    # Determine whether the repo license is approved
                    itemLicCheck = licenseCheck.check_license_safe(spdxLicenses)
                    itemLicense = itemLicCheck.get('pass')
                    noticeItemLic = itemLicCheck.get('notice')
                    itemDetial = itemLicCheck.get('detail')
                    itemLicList.append(spdx_name)
                    itemPathList.append(path)
                    if path.lower().endswith(("license",)):
                        itemLicFlag = True
                elif path.lower().endswith(("license",)) and path not in itemPathList and itemLicFlag is False:
                    # Determine whether the repo license is approved
                    itemLicCheck = licenseCheck.check_license_safe(spdxLicenses)
                    itemLicense = itemLicCheck.get('pass')
                    noticeItemLic = itemLicCheck.get('notice')
                    itemDetial = itemLicCheck.get('detail')
                    itemLicList.clear()
                    itemPathList.clear()
                    itemLicList.append(spdx_name)
                    itemPathList.append(path)
                elif path in itemPathList and spdx_name not in itemLicList:
                    # Check the same file
                    itemLicCheck = licenseCheck.check_license_safe(spdxLicenses)
                    itemLicTemp = itemLicCheck.get('pass')
                    if itemLicTemp is False:
                        itemLicense = itemLicTemp
                        if noticeItemLic != '通过':
                            noticeItemLic = noticeItemLic + "。" + itemLicCheck.get('notice')
                        else:
                            noticeItemLic = itemLicCheck.get('notice')
                        itemDetial = mergDetial(itemDetial, itemLicCheck.get('detail'))
                    itemLicList.append(spdx_name)
            else:
                # Determine whether the license belongs to certification
                fileLicense = fileLicenseCheck.check_license_safe(spdxLicenses)
                reLicense = fileLicense.get('pass')
                spdLower = spdx_name.lower()
                if reLicense is False and pathLicense['start_line'] != pathLicense['end_line'] and 'exception' not in spdLower and 'doc' != spdLower:
                    approved = False
                    noticeScope = noticeScope + spdx_name + "("+path + ", start_line: "+str(
                        pathLicense['start_line'])+", end_line: "+str(pathLicense['end_line'])+"), " 

    if len(itemPathList) == 0:
        itemPathList.append(noticeLicense)
    if len(failCopList) > 0:
        tempFail = '、'.join(failCopList)
        checkCopyright = checkCopyright + tempFail + "文件Copyright校验不通过, "
    if len(loseCopList) > 0:
        tempLose = '、'.join(loseCopList)
        checkCopyright = checkCopyright + tempLose + "文件缺失Copyright声明, "
    if checkCopyright != '':
        noticeCopyright = checkCopyright + " Copyright path：" + noticeCopyright
    noticeCopyright = noticeCopyright.strip(', ')
    noticeScope = noticeScope.strip(', ')
    if noticeScope == '':
        noticeScope = '准入License'
    else:
        noticeScope = '存在非准入License：' + noticeScope + ' License准入列表请参考 https://compliance.openeuler.org/license-list, 若需对License发起准入申请，请联系合规SIG组或chenyixiong3@huawei.com'

    sca_result = {
        "repo_license_legal": {
            "pass": haveLicense,
            "result_code": "",
            "notice": itemPathList[0],
            "is_legal": {
                "pass": itemLicense,
                "license": itemLicList,
                "notice": noticeItemLic,
                "detail": itemDetial
            }
        },
        "spec_license_legal": {
            "pass": specLicense,
            "result_code": "",
            "notice": noticeSpec,
            "detail": speLicDetial
        },
        "license_in_scope": {
            "pass": approved,
            "result_code": "",
            "notice": noticeScope
        },
        "repo_copyright_legal": {
            "pass": isCopyright,
            "result_code": "",
            "notice": noticeCopyright,
            "copyright": crInfoList
        }
    }
    logging.info("============END ANALYZE RESULT=============")

    return sca_result


@catch_error
def checkPath(path, depth):
    # Check the notice file
    path = path.lower()

    pathLevel = path.split("/")
    if len(pathLevel) > depth:
        return False

    return True


@catch_error
def checkNotice(path, depth):
    # Check the notice file
    path = path.lower()

    pathLevel = path.split("/")
    if len(pathLevel) > depth:
        return False

    for item in noticeList:
        if path.endswith((item,)):
            return True

    return False

@catch_error
def checkRepoLicense(path, depth):
    path = path.lower()

    pathLevel = path.split("/")
    if len(pathLevel) > depth:
        return False

    for item in repoList:
        if item in path:
            return True

    return False

@catch_error
def is_in(path, file_array):
    for item in file_array:
        if item in path:
            return True
    return False


@catch_error
def mergDetial(oldDetial, lastDetial):
    res = {}
    impResult = True
    impLic = []
    nstdResult = True
    nstdLic = []
    reviewResult = True
    reviewLic = []
    if oldDetial.get('is_standard').get('pass') is False or lastDetial.get('is_standard').get('pass') is False:
        nstdResult = False
        nstdLic = oldDetial.get('is_standard').get('risks') + lastDetial.get('is_standard').get('risks')

    if oldDetial.get('is_white').get('pass') is False or lastDetial.get('is_white').get('pass') is False:
        impResult = False

    impLic = oldDetial.get('is_white').get('risks') + lastDetial.get('is_white').get('risks')

    blackReason = oldDetial.get('is_white').get('blackReason') + ", " + lastDetial.get('is_white').get('blackReason')
    blackReason = blackReason.strip(", ")

    if oldDetial.get('is_review').get('pass') is False or lastDetial.get('is_review').get('pass') is False:
        reviewResult = False
        reviewLic = oldDetial.get('is_review').get('risks') + lastDetial.get('is_review').get('risks')

    res = {
        'is_standard': {
            'pass': nstdResult,
            'risks': nstdLic,
        },
        'is_white': {
            'pass': impResult,
            'risks': impLic,
            'blackReason': blackReason,
        },
        'is_review': {
            'pass': reviewResult,
            'risks': reviewLic,
        }
    }

    return res

@catch_error
def licenseSplit(licenses):
    license_set = re.split(r'\(|\)|\s+\,|\s+[Aa][Nn][Dd]\s+|\s+-?[Oo][Rr]-?\s+|\s+/\s+|\s+[Ww][Ii][Tt][Hh]\s+', licenses)
    for index in range(len(license_set)):  # Remove leading and trailing spaces from string
        license_set[index] = license_set[index].strip()
    license_set = list(filter(None, license_set))
    return license_set

@catch_error
def copyright_check(copyright):
    copyright_pattern = r'^Copyright \(c\) (\d{4}\s)*[A-Za-z\s]*(\.)*,*\s*Huawei Technologies Co., Ltd.\s*(\d{4})?(-\d{4})?(\.)?\s*(All rights reserved\.)?'
    match = re.search(copyright_pattern, copyright)
    return match 