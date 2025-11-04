
from tkinter.messagebox import NO
from bs4 import BeautifulSoup
from pymysql import escape_string
import requests
from tqdm import tqdm
import yaml
import logging
import sys
sys.path.append("..")
from reposca.repoDb import RepoDb

def dbSyn():
    dbObject = RepoDb(name_db='license')
    try:
        with open("../reposca/config/Licenses.yaml", "r", encoding='utf-8') as f:
            data = yaml.safe_load(f)
        soft_license = data.get("Software Licenses", {})
        licenses = soft_license.get("Licenses")
        for lic in tqdm(licenses, desc="DbSyn Ing:", total=len(licenses), colour='green'):
            if lic["identifier"] == 'BSD':
                continue
            oeApprove = 1 if lic["oeApproved"] == 'Y' else 0
            lowRisk = 1 if lic["lowRisk"] == 'Y' else 0
            black = 1 if lic['black'] == 'Y' else 0
            blackReason = lic['blackReason']
            isYaml = 1
            alias = ",".join(lic["alias"])
            alias = escape_string(alias)

            repoData = (lic["identifier"])
            osiApproved = 1 if lic["osiApproved"] == 'Y' else 0
            fsfApproved = 1 if lic["fsfApproved"] == 'Y' else 0
            dcLicense = dbObject.Query_License_BySpdx(repoData)
            if dcLicense is None:

                license = crawlLicense(lic["identifier"])
                if license is None:
                    continue
                licenseData = (
                    escape_string(license.get('name')),lic["identifier"],osiApproved,fsfApproved,
                    escape_string(license.get('summary')),escape_string(license.get('fullText')),
                    escape_string(license.get('textPlan')),escape_string(license.get('summarySpdx')),
                    escape_string(license.get('webPage')),escape_string(license.get('standar')),
                    isYaml,oeApprove,lowRisk,black,blackReason,alias
                )
                dbObject.add_LicData(licenseData)
            else:
                licenseData = (isYaml, oeApprove, lowRisk, black, blackReason, alias, dcLicense['id'])
                dbObject.Modify_License(licenseData)
    except Exception as e:
        logging.exception(e)
        pass


def crawlLicense(licnese):
    try:
        licUrl = "https://spdx.org/licenses/"+licnese+".html"
        response = requests.get(licUrl, verify=False)
        if response.status_code == 404:
            return None
        demo = response.text  

        soup = BeautifulSoup(demo, "lxml")
        licName = soup.find_all(attrs={'property': 'spdx:name'})[0].get_text()
        summary = soup.find(attrs={'id': 'notes'}).find_next_sibling().get_text()
        fullText = soup.find(attrs={'property': 'spdx:licenseText'})   
        if fullText is None:
            fullText = soup.find(attrs={'property': 'spdx:licenseExceptionText'})
        fullText = str(fullText)
        fullText = fullText.replace("  ", "")
        fullText = fullText.replace("\n", "")
        textPlan = BeautifulSoup(fullText,'lxml')
        textPlan = textPlan.get_text()
        webPage = soup.find(attrs={'id': 'page'}).find_all('ul')[0]
        webPage = str(webPage)
        webPage = webPage.replace("  ", "")
        webPage = webPage.replace("\n", "")
        try:
            standar = soup.find(attrs={'property': 'spdx:standardLicenseHeader'}).find('p')
            standar = str(standar)
        except Exception as ex:
            standar = 'None'
            pass
        licensedata = {
            'name': licName, 
            'summary':summary,
            'fullText': fullText,
            'textPlan': textPlan,
            'summarySpdx': summary,
            'webPage': webPage, 
            'standar': standar
        }
        return licensedata
    except Exception as e:
        return None


if __name__ == '__main__':
    dbSyn()
