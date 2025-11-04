
import sys
sys.path.append("..")
import os
from reposca.itemLicSca import ItemLicSca
from reposca.repoDb import RepoDb
from tqdm import tqdm

noticeList = ['notice', 'third_party_open_source_software_notice','readme', 'license', 'copyright']
repoList = ['license', 'readme', 'notice', 'copying']

def fixSca():
    dbOb = RepoDb(
        host_db = os.environ.get("MYSQL_HOST"), 
        user_db = os.environ.get("MYSQL_USER"), 
        password_db = os.environ.get("MYSQL_PASSWORD"), 
        name_db = os.environ.get("MYSQL_DB_NAME"), 
        port_db = int(os.environ.get("MYSQL_PORT")))
    
    repoList = dbOb.Query_AllRepo()

    for item in tqdm(repoList,desc="Fix Data:", total=len(repoList),colour='green'):
        repoOrg = item['repo_org']
        repoName = item['repo_name']
        commite = item['commite']
        purl = "pkg:gitee/"+repoOrg+"/"+repoName + "@"+commite
        itemLic = ItemLicSca()
        result = itemLic.licSca(purl)
    return "F1"


if __name__ == '__main__': 
    fixSca()