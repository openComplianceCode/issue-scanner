import logging
import os
from util.catchUtil import catch_error
from reposca.repoDb import RepoDb


logging.getLogger().setLevel(logging.INFO)

class QueryBoard(object):
    
    def __init__(self):
        #Connect to the database
        self._dbObject_ = RepoDb(
            host_db = os.environ.get("MYSQL_HOST"), 
            user_db = os.environ.get("MYSQL_USER"), 
            password_db = os.environ.get("MYSQL_PASSWORD"), 
            name_db = os.environ.get("MYSQL_DB_NAME"), 
            port_db = int(os.environ.get("MYSQL_PORT")))

    @catch_error   
    def query(self, tag, org, repo):
        result = []
        metrics_switch = {
            "admittance": lambda: self._dbObject_.Query_License_Enter(),
            "admittanceOrg": lambda: self._dbObject_.Query_License_Enter_org(org),
            "admittanceRepo": lambda: self._dbObject_.Query_License_Enter_repo(queryData = (org, repo)),
            "spec": lambda: self._dbObject_.Query_License_Spec(),
            "specRepo": lambda: self._dbObject_.Query_License_Spec_repo(repo),
            "standard": lambda: self._dbObject_.Query_License_Un(),
            "standardOrg": lambda: self._dbObject_.Query_License_Un_org(org),
            "standardRepo": lambda: self._dbObject_.Query_License_Un_repo(queryData = (org, repo)),
            "copyright": lambda: self._dbObject_.Query_Copyright(),
            "copyrightOrg": lambda: self._dbObject_.Query_Copyright_Org(org),
            "copyrightRepo": lambda: self._dbObject_.Query_Copyright_Repo(queryData = (org, repo)),
            "pr": lambda: self._dbObject_.Query_PR_All(org),
        }
        result = metrics_switch[tag]()

        return result