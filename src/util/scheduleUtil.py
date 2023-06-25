import json
import os
from reposca.repoDb import RepoDb
from apscheduler.schedulers.background import BackgroundScheduler
from util.catchUtil import catch_error

from util.authApi import AuthApi

class Scheduler(object):

    def __init__(self):
        #连接数据库
        self._dbObject_ = RepoDb(
            host_db = os.environ.get("MYSQL_HOST"), 
            user_db = os.environ.get("MYSQL_USER"), 
            password_db = os.environ.get("MYSQL_PASSWORD"), 
            name_db = os.environ.get("MYSQL_DB_NAME"), 
            port_db = int(os.environ.get("MYSQL_PORT")))
        
        scheduler = BackgroundScheduler()
        scheduler.start()
        
        scheduler.add_job(
            self.prSchedule,
            trigger='cron',
            hour=19,
        )

    @catch_error
    def prSchedule(self):
        try:
            pr_data = self._dbObject_.Query_PR_Merge()
            apiObc = AuthApi()
            if pr_data is not None:
                for var in pr_data:
                    pr_id = var['id']
                    pr_owner = var['repo_org']
                    pr_repo = var['repo_name']
                    pr_num = var['pr_num']
                    pr_response = apiObc.getPrInfo(pr_owner, pr_repo, pr_num)
                    if pr_response == 403 or pr_response == 404:
                        continue
                    prData = pr_response.data.decode('utf-8')
                    prData = json.loads(prData)
                    mergedAt = prData['merged_at']
                    if mergedAt is not None:
                        itemData = (1, pr_id)
                        self._dbObject_.upd_PR_State(itemData)
        finally:
            self._dbObject_.Close_Con()
        
        