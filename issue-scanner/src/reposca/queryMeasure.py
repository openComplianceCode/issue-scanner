
import os
from reposca.repoDb import RepoDb


class QueryMeasure(object):

    def __init__(self):
        #Connect to the database
        self._dbObject_ = RepoDb(
            host_db = os.environ.get("MYSQL_HOST"), 
            user_db = os.environ.get("MYSQL_USER"), 
            password_db = os.environ.get("MYSQL_PASSWORD"), 
            name_db = os.environ.get("MYSQL_DB_NAME"), 
            port_db = int(os.environ.get("MYSQL_PORT")))
        
    def query(self, tag, org, repo, data_month):
        result = []
        metrics_switch = {
            "org": lambda: self._dbObject_.Query_measure_org((data_month, org)),
            "repo": lambda: self._dbObject_.Query_measure_repo((data_month, org, repo)),
        }
        result = metrics_switch[tag]()

        return result