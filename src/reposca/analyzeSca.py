import json
import logging
import re
import jsonpath
from reposca.licenseCheck import LicenseCheck
from util.catchUtil import catch_error
from util.postOrdered import infixToPostfix
from pyrpm.spec import Spec

noticeList = ['notice', 'third_party_open_source_software_notice','readme', 'license', 'copyright']
repoList = ['license', 'readme', 'notice', 'copying']
SOURTH_PATH = '/home/giteeFile'


@catch_error
def getScaAnalyze(scaJson, anlyzeSrc, type):
    '''
    :param repoSrc: 扫描文件路径
    :param repo: 项目名
    :param scaJson: 扫描结果json
    :return:分析结果json
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
    crInfoList = []
    speLicDetial = {}

    jsonData = json.loads(scaJson)
    itemPath = jsonpath.jsonpath(jsonData, '$.files[*].path')
    licenseList = jsonpath.jsonpath(jsonData, '$.files[*].licenses')
    copyrightList = jsonpath.jsonpath(jsonData, '$.files[*].copyrights')

    logging.info("===========START ANALYZE RESULT============")
    fileLicenseCheck = LicenseCheck('file')
    licenseCheck = LicenseCheck('reference')
    indeLicChck = LicenseCheck('independent')
    pathDepth = 3
    if type == 'ref':
        pathDepth = 4
    if licenseList is False:
        licenseList = []
    itemLicFlag = False
    for i, var in enumerate(licenseList):   
        path = itemPath[i]
        # 判断是否含有notice文件
        if checkNotice(path, pathDepth) and len(copyrightList[i]) > 0:
            if isCopyright is False:
                isCopyright = True
                noticeCopyright = ""
            copyrightInfo = copyrightList[i]
            for info in copyrightInfo:
                crInfoList.append(info['copyright'])
            noticeCopyright = noticeCopyright + "(" + path + "), "

        if path.endswith((".spec",)) and checkPath(path, 2):
            # 提取spec里的许可证声明
            fileUrl = anlyzeSrc + "/" + itemPath[i]
            try:
                spec = Spec.from_file(fileUrl)
                if spec.license is not None:
                    licenses = infixToPostfix(spec.license)
                    isSpecLicense = licenseCheck.check_license_safe(licenses)
                    specLicense = isSpecLicense.get('pass')
                    noticeSpec = isSpecLicense.get('notice')
                    speLicDetial = isSpecLicense.get('detail')
                    specLicenseList.append(spec.license)
                    if haveLicense is False or type == 'ref':
                        specFlag = False
                        haveLicense = True
                        noticeLicense = ""
                        itemLicList.clear()
                        itemPathList.clear()
                        # itemLicList = licenseSplit(spec.license)
                        itemLicList.append(spec.license)
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
                if "mulanpsl" in spdx_name:
                    spdx_name = spdx_name.split("LicenseRef-scancode-")[1]
                else:
                    continue
            spdxLicenses = infixToPostfix(spdx_name)
            # 判断是否有项目license
            if checkRepoLicense(path, pathDepth) and specFlag:
                if haveLicense is False:
                    haveLicense = True
                    noticeLicense = ""
                    # 判断项目License是否准入
                    if type == 'ref':
                        itemLicCheck = licenseCheck.check_license_safe(spdxLicenses)
                    else:
                        itemLicCheck = indeLicChck.check_license_safe(spdxLicenses)
                    itemLicense = itemLicCheck.get('pass')
                    noticeItemLic = itemLicCheck.get('notice')
                    itemDetial = itemLicCheck.get('detail')
                    itemLicList.append(spdx_name)
                    itemPathList.append(path)
                    if path.lower().endswith(("license",)):
                        itemLicFlag = True
                elif path.lower().endswith(("license",)) and path not in itemPathList and itemLicFlag is False:
                    # 判断项目License是否准入
                    if type == 'ref':
                        itemLicCheck = licenseCheck.check_license_safe(spdxLicenses)
                    else:
                        itemLicCheck = indeLicChck.check_license_safe(spdxLicenses)
                    itemLicense = itemLicCheck.get('pass')
                    noticeItemLic = itemLicCheck.get('notice')
                    itemDetial = itemLicCheck.get('detail')
                    itemLicList.clear()
                    itemPathList.clear()
                    itemLicList.append(spdx_name)
                    itemPathList.append(path)
                elif path in itemPathList and spdx_name not in itemLicList:
                    # 同一个文件的做检查
                    if type == 'ref':
                        itemLicCheck = licenseCheck.check_license_safe(spdxLicenses)
                    else:
                        itemLicCheck = indeLicChck.check_license_safe(spdxLicenses)
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
                # 判断license是否属于认证
                fileLicense = fileLicenseCheck.check_license_safe(spdxLicenses)
                reLicense = fileLicense.get('pass')
                spdLower = spdx_name.lower()
                if reLicense is False and pathLicense['start_line'] != pathLicense['end_line'] and 'exception' not in spdLower and 'doc' != spdLower:
                    approved = False
                    noticeScope = noticeScope + spdx_name + "("+path + ", start_line: "+str(
                        pathLicense['start_line'])+", end_line: "+str(pathLicense['end_line'])+"), "

    if len(itemPathList) == 0:
        itemPathList.append(noticeLicense)
    noticeCopyright = noticeCopyright.strip(', ')
    noticeScope = noticeScope.strip(', ')
    if noticeScope == '':
        noticeScope = 'OSI/FSF认证License'
    else:
        noticeScope = '存在非OSI/FSF认证的License：' + noticeScope + ' License准入列表请参考 https://compliance.openeuler.org/license-list, 若需对License发起准入申请，请联系合规SIG组或chenyixiong3@huawei.com'
    #关闭copyright
    isCopyright = True
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
    # 检查是notice文件
    path = path.lower()

    pathLevel = path.split("/")
    if len(pathLevel) > depth:
        return False

    return True


@catch_error
def checkNotice(path, depth):
    # 检查是notice文件
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
    for index in range(len(license_set)):  # 去除字符串首尾空格
        license_set[index] = license_set[index].strip()
    license_set = list(filter(None, license_set))
    return license_set