import json
import logging
import os
import re
import jsonpath
import yaml
from reposca.licenseCheck import LicenseCheck
from util.catchUtil import catch_error
from util.postOrdered import infixToPostfix
from pyrpm.spec import Spec

noticeList = ['notice', 'third_party_open_source_software_notice','readme', 'copying', 'copyright']
repoList = ['license', 'readme', 'notice', 'copying', 'third_party_open_source_software_notice', 'copyright', '.spec']


@catch_error
def getSourceData(scaJson, type):
    '''
    :param scaJson: Scan result json
    :param anlyzeSrc: Scan file path
    :param type: Level
    :return:Analysis result json
    '''
    jsonData = json.loads(scaJson)
    itemPath = jsonpath.jsonpath(jsonData, '$.files[*].path')
    licenseList = jsonpath.jsonpath(jsonData, '$.files[*].licenses')

    fileLicenseCheck = LicenseCheck('file', 'indelic')
    licenseCheck = LicenseCheck('repo', 'indelic')
    pathDepth = 3
    if type == 'ref':
        pathDepth = 4
    if licenseList is False:
        licenseList = []
    for i, var in enumerate(licenseList):   
        path = itemPath[i]
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
            # Determine whether the project license
            approve_status = False
            if checkRepoLicense(path, pathDepth):
                # Determine whether the project license is approved
                itemLicCheck = licenseCheck.check_license_safe(spdxLicenses)
                approve_status = itemLicCheck.get('pass')            
            else:
                # Determine whether the license belongs to certification
                fileLicense = fileLicenseCheck.check_license_safe(spdxLicenses)
                approve_status = fileLicense.get('pass')
            pathLicense['approve_status'] = approve_status
    return jsonData


@catch_error
def checkPath(path, depth):
    path = path.lower()

    pathLevel = path.split("/")
    if len(pathLevel) > depth:
        return False

    return True


@catch_error
def checkNotice(path, depth):
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
def licenseSplit(licenses):
    license_set = re.split(r'\(|\)|\s+\,|\s+[Aa][Nn][Dd]\s+|\s+-?[Oo][Rr]-?\s+|\s+/\s+|\s+[Ww][Ii][Tt][Hh]\s+', licenses)
    for index in range(len(license_set)): 
        license_set[index] = license_set[index].strip()
    license_set = list(filter(None, license_set))
    return license_set