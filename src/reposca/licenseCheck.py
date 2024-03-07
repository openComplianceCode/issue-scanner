# -*- coding: utf-8 -*-
import logging
import os

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

    def __init__(self, type, accesstype):
        """
        type :  repo -  repo-level
                file -  file-level
        accesstype:  osf - osi/fsf approve
                     indelic - Custom access
        """
        self._white_black_list = {}
        self._license_translation = {}
        self.load_config()
        self._type_ = type
        self._accessType_ = accesstype
    

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
                'ohApproved': ohApproved,
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
                    'ohApproved': lic["ohApproved"],
                    'lowRisk': lic["lowRisk"],
                    'black': lic["black"],
                    'blackReason': lic["blackReason"],
                    'exception': lic["exception"]
                }
            for oname in lic["alias"]:
                loOname = oname.lower()
                if loOname not in self._white_black_list:
                    self._white_black_list[loOname] = {
                        'tag': tag,
                        'fsfApproved': lic["fsfApproved"],
                        'osiApproved': lic["osiApproved"],
                        'oeApproved': lic["oeApproved"],
                        'ohApproved': lic["ohApproved"],
                        'lowRisk': lic["lowRisk"],
                        'black': lic["black"],
                        'blackReason': lic["blackReason"],
                        'exception': lic["exception"]
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
            if result_stack.size() > 1:
                res = self.analyze_detial(result_stack.pop(), result_stack.pop(), 'and')
                result_stack.push(res)
            else:    
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
            elif res['exception'] == 'Y':
                impResult = True
            else:
                if self._accessType_ == 'osf':
                    if res['oeApproved'] == 'Y' or res['fsfApproved'] == 'Y':
                        impResult = True
                    else:
                        impResult = False
                        impLic.append(license)
                else:
                    if self._type_ == 'repo':
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

    @catch_error
    def check_exception(self, license):
        result = False
        lowLic = license.lower()
        res = self._white_black_list.get(lowLic, "unknow")
        if res == 'unknow':
            result = False
        elif res['tag'] == "licenses":
            if res['exception'] == 'Y':
                result = True
        
        return result

    @catch_error
    def check_approve(self, license):
        result = False
        lowLic = license.lower()
        res = self._white_black_list.get(lowLic, "unknow")
        if res == 'unknow':
            result = False
        elif res['tag'] == "licenses":
            if res['fsfApproved'] == 'Y' or res['osiApproved'] == 'Y':
                result = True
        
        return result
                       
    
    @catch_error
    def check_admittance(self, license):
        result = "NOT_ALLOW"
        lowLic = license.lower()
        res = self._white_black_list.get(lowLic, "unknow")
        if res == 'unknow':
            result = "UNKNOW"
        elif res['tag'] == "licenses":
            if res['fsfApproved'] == 'Y' or res['osiApproved'] == 'Y' or res['oeApproved'] == 'Y':
                result = "ALLOW"
            elif res['lowRisk'] == 'Y':
                result = "LIMIT"
        
        return result