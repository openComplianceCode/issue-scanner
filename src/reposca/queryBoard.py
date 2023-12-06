import logging
import os
from util.catchUtil import catch_error
from reposca.repoDb import RepoDb


logging.getLogger().setLevel(logging.INFO)

class QueryBoard(object):
    
    def __init__(self):
        #连接数据库
        self._dbObject_ = RepoDb(
            host_db = os.environ.get("MYSQL_HOST"), 
            user_db = os.environ.get("MYSQL_USER"), 
            password_db = os.environ.get("MYSQL_PASSWORD"), 
            name_db = os.environ.get("MYSQL_DB_NAME"), 
            port_db = int(os.environ.get("MYSQL_PORT")))

    @catch_error   
    def query(self, tag, org, repo):
        result = []
        if tag == 'admittance':
            result = self._dbObject_.Query_License_Enter()
        elif tag == 'admittanceOrg':
            result = self._dbObject_.Query_License_Enter_org(org)
        elif tag == 'admittanceRepo':
            queryData = (org, repo)
            result = self._dbObject_.Query_License_Enter_repo(queryData)
        elif tag == 'spec':
            result = self._dbObject_.Query_License_Spec()
        elif tag == 'specRepo':
            result = self._dbObject_.Query_License_Spec_repo(repo)
        elif tag == 'standard':
            result = self._dbObject_.Query_License_Un()
        elif tag == 'standardOrg':
            result = self._dbObject_.Query_License_Un_org(org)
        else:
            queryData = (org, repo)
            result = self._dbObject_.Query_License_Un_repo(queryData)

        return result