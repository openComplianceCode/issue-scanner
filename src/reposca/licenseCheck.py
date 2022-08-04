# -*- coding: utf-8 -*-
from email import message
import logging
import os
import re

import yaml

from util.stack import Stack

logger = logging.getLogger("reposca")

class LicenseCheck(object):

    def catch_error(func):
        def wrapper(*args, **kw):
            try:
                return func(*args, **kw)
            except Exception as e:
                logging.exception(e)

        return wrapper

    LICENSE_YAML_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                   "config",
                                   "Licenses.yaml")
    LATER_SUPPORT_LICENSE_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                   "config",
                                   "later_support_license.yaml")


    def __init__(self, type):
        """
        type :  independent - 自研    
                reference - 引用    
                file -  文件级
        """
        self._white_black_list = {}
        self._license_translation = {}
        self._later_support_license = {}
        self.load_config()
        self._type_ = type
    

    @catch_error
    def load_config(self):
        """
        load licenses' alias and id from Licenses.yaml
        Software License:
            Bad Licenses:
                - alias: []
                  identifier: str
                ...
            Good Licenses: []
            Need Review Licenses: []
        """
        if not os.path.exists(self.LICENSE_YAML_PATH):
            logger.warning("not found License config: %s", self.LICENSE_YAML_PATH)
            return
        data = {}
        with open(self.LICENSE_YAML_PATH, "r", encoding='utf-8') as f:
            try:
                data = yaml.safe_load(f)
            except yaml.YAMLError as e:
                logger.exception("yaml load error: %s", str(e))
                return
        with open(self.LATER_SUPPORT_LICENSE_PATH, "r", encoding='utf-8') as f:
            try:
                self._later_support_license = yaml.safe_load(f)
            except yaml.YAMLError as e:
                logger.exception("yaml load error: %s", str(e))
                return
        soft_license = data.get("Software Licenses", {})
        if soft_license:
            self._parse_tag_license(soft_license.get("Nonstandard Licenses"), "nonstandard")
            self._parse_tag_license(soft_license.get("Licenses"), "licenses")
        else:
            logger.error("yaml format error")
            return

    @catch_error
    def _parse_tag_license(self, licenses, tag):
        """
        add friendly list to self._white_black_list :
        {
            license_id: {
                'tag': tag,
                'fsfApproved': fsfApproved,
                'osiApproved': osiApproved,
                'oeApproved': oeApproved,
                'lowRisk': lowRisk,
                'black': black,
                'blackReason': blackReason
            },
            ...
        }
        """
        for lic in licenses:
            identi = lic["identifier"].lower()
            if identi not in self._white_black_list:
                self._white_black_list[identi] = {
                    'tag': tag,
                    'fsfApproved': lic["fsfApproved"],
                    'osiApproved': lic["osiApproved"],
                    'oeApproved': lic["oeApproved"],
                    'lowRisk': lic["lowRisk"],
                    'black': lic["black"],
                    'blackReason': lic["blackReason"]
                }
            for oname in lic["alias"]:
                loOname = oname.lower()
                if loOname not in self._white_black_list:
                    self._white_black_list[loOname] = {
                        'tag': tag,
                        'fsfApproved': lic["fsfApproved"],
                        'osiApproved': lic["osiApproved"],
                        'oeApproved': lic["oeApproved"],
                        'lowRisk': lic["lowRisk"],
                        'black': lic["black"],
                        'blackReason': lic["blackReason"]
                    }

    @catch_error
    def check_license_safe(self, licenses):
        """
        Check if the license is in the blacklist
        """
        result = {}
        result_stack = Stack()
        for lic in licenses:
            if lic.lower() in ['and', 'or', 'with']:
                licBack = result_stack.pop()
                licHead = result_stack.pop()
                if isinstance(licHead, dict):
                    reHead = licHead
                else:
                    reHead = self.check_license(licHead)
                if isinstance(licBack, dict):
                    reBack = licBack
                else:
                    reBack = self.check_license(licBack)
                res = self.analyze_detial(reHead, reBack, lic.lower())
                result_stack.push(res)
            else:
                reLic = self.check_license(lic)
                result_stack.push(reLic)

        while not result_stack.is_empty():
            result = result_stack.pop()

        result = self.analyze_result(result)
        
        return result


    @catch_error
    def analyze_result(self, result):
        resImp = result.get('is_white')
        resNstd = result.get('is_standard')
        resReivew = result.get('is_review')

        notice = ''
        res = resImp.get('pass') & resNstd.get('pass') & resReivew.get('pass')
    
        nstdRisks = '、'.join(resNstd.get('risks'))
        revRisks = '、'.join(resReivew.get('risks'))
        impRisks = '、'.join(resImp.get('risks'))

        if res is False:
            if impRisks != '':
                notice += impRisks + " 不可引入, "              
            if nstdRisks != '':
                notice += nstdRisks + " 声明不规范, "
            if revRisks != '':
                notice += revRisks + " 需要Review, "
            notice += 'License准入列表请参考 https://compliance.openeuler.org/license-list, 若需对License发起准入申请，请联系合规SIG组或chenyixiong3@huawei.com'
        else:
            notice = '通过'

        finalResult = {
            "pass": res,
            "notice": notice,
            "detail": result
        }

        return finalResult

    @catch_error
    def check_license(self, license):
        impResult = True
        impLic = []
        blackReason = ""
        nstdResult = True
        nstdLic = []
        reviewResult = True
        reviewLic = []
        lowLic = license.lower()
        res = self._white_black_list.get(lowLic, "unknow")
        if res == 'unknow':
            reviewResult = False
            reviewLic.append(license) 
        elif res['tag'] == "licenses":
            if res['black'] == 'Y':
                impResult = False
                impLic.append(license) 
                blackReason = license + " " + res['blackReason']
            else:
                if self._type_ == 'independent':
                    if (res['fsfApproved'] == 'Y' or res['osiApproved'] == 'Y') and res['lowRisk'] == 'N':
                        impResult = True
                    else:
                        impResult = False
                        impLic.append(license)  
                elif self._type_ == 'reference':
                    if (res['oeApproved'] == 'Y' or res['fsfApproved'] == 'Y' or res['osiApproved'] == 'Y') and res['lowRisk'] == 'N':
                        impResult = True
                    else:
                        impResult = False
                        impLic.append(license)
                else:
                    if res['oeApproved'] == 'Y' or res['fsfApproved'] == 'Y' or res['osiApproved'] == 'Y' or res['lowRisk'] == 'Y':
                        impResult = True
                    else:
                        impResult = False
                        impLic.append(license)
        elif res['tag'] == "nonstandard":
            nstdResult = False    
            nstdLic.append(license)
                       

        detail = {
            'is_standard' : {
                'pass': nstdResult,
                'risks' : nstdLic,
            },
            'is_white' : {
                'pass': impResult,
                'risks' : impLic,
                'blackReason' : blackReason
            },
            'is_review' : {
                'pass': reviewResult,
                'risks' : reviewLic,
            }
        }

        return detail
    
    @catch_error
    def analyze_detial(self, reHead, reBack, connector):
        res = {}
        impResult = True
        impLic = []
        nstdResult = True
        nstdLic = []
        reviewResult = True
        reviewLic = []
        if reHead.get('is_standard').get('pass') is False or reBack.get('is_standard').get('pass') is False:
            nstdResult = False
            nstdLic = reHead.get('is_standard').get('risks') + reBack.get('is_standard').get('risks')

        if connector == 'and' and (reHead.get('is_white').get('pass') is False or reBack.get('is_white').get('pass') is False):
            impResult = False
        elif connector == 'or' and (reHead.get('is_white').get('pass') is False and reBack.get('is_white').get('pass') is False):
            impResult = False
        elif connector == 'with' and reHead.get('is_white').get('pass') is False:
            impResult = False
        impLic = reHead.get('is_white').get('risks') + reBack.get('is_white').get('risks')
        blackReason = reHead.get('is_white').get('blackReason') + ", " + reBack.get('is_white').get('blackReason')
        blackReason = blackReason.strip(", ")
                
        if reHead.get('is_review').get('pass') is False or reBack.get('is_review').get('pass') is False:
            reviewResult = False
            reviewLic = reHead.get('is_review').get('risks') + reBack.get('is_review').get('risks')

        res = {
            'is_standard' : {
                'pass': nstdResult,
                'risks' : nstdLic,
            },
            'is_white' : {
                'pass': impResult,
                'risks' : impLic,
                'blackReason' : blackReason,
            },
            'is_review' : {
                'pass': reviewResult,
                'risks' : reviewLic,
            }
        }

        return res
