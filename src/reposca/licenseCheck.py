# -*- coding: utf-8 -*-
import logging
import os
import re

import yaml

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


    def __init__(self):
        self._white_black_list = {}
        self._license_translation = {}
        self._later_support_license = {}
    

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
            self._parse_tag_license(soft_license.get("Not Free Licenses"), "black")
            self._parse_tag_license(soft_license.get("Free Licenses"), "white")
            self._parse_tag_license(soft_license.get("Need Review Licenses"), "need review")
        else:
            logger.error("yaml format error")
            return

    @catch_error
    def _parse_tag_license(self, licenses, tag):
        """
        add friendly list to self._white_black_list :
        {
            license_id: tag,
            ...
        }
        add license translation into self._license_translation
        {
            alias: license_id
        }
        """
        for lic in licenses:
            if lic["identifier"] not in self._white_black_list:
                self._white_black_list[lic["identifier"]] = tag
            for oname in lic["alias"]:
                if oname not in self._license_translation:
                    self._license_translation[oname] = lic["identifier"]

    @catch_error
    def check_license_safe(self, licenses):
        """
        Check if the license is in the blacklist
        """
        result = 'TRUE'
        for lic in licenses:
            res = self._white_black_list.get(lic, "unknow")
            if res == "white":
                logger.info("This license: %s is free", lic)
            elif res == "black":
                logger.error("This license: %s is not free", lic)
                result = 'FALSE'
            else: 
                logger.warning("This license: %s need to be review", lic)
                result = 'REVIEW'
        return result

    @catch_error
    def translate_license(self, licenses):
        """
        Convert license to uniform format
        """
        result = set()
        for lic in licenses:
            real_license = self._license_translation.get(lic, lic)
            result.add(real_license)
        return result

    @staticmethod
    def split_license(licenses):
        """
        分割spec license字段的license 按() and -or- or / 进行全字匹配进行分割
        """
        license_set = re.split(r'\(|\)|\s+\,|\s+[Aa][Nn][Dd]\s+|\s+-?or-?\s+|\s+/\s+', licenses)
        for index in range(len(license_set)):  # 去除字符串首尾空格
            license_set[index] = license_set[index].strip()
        return set(filter(None, license_set))  # 去除list中空字符串
