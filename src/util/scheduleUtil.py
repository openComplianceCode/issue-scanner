import json
import os

from reposca.repoDb import RepoDb
from apscheduler.schedulers.background import BackgroundScheduler
from reposca.scheduleSca import ScheduleSca
from util.catchUtil import catch_error

from util.authApi import AuthApi

PER_PAGE = 100

class Scheduler(object):

    def __init__(self): 
        scheduler = BackgroundScheduler()
        scheduler.start()
        
        scheduler.add_job(
            self.prSchedule,
            max_instances=10,
            trigger='cron',
            hour=19,
        )

        scheduler.add_job(
            self.sca_repo,
            max_instances=10,
            trigger='cron',
	        day='4th fri',
            hour=21
        )

    @catch_error
    def prSchedule(self):
        try:
            #Connect to the database
            dbObject = RepoDb(
                host_db = os.environ.get("MYSQL_HOST"), 
                user_db = os.environ.get("MYSQL_USER"), 
                password_db = os.environ.get("MYSQL_PASSWORD"), 
                name_db = os.environ.get("MYSQL_DB_NAME"), 
                port_db = int(os.environ.get("MYSQL_PORT")))
            
            pr_data = dbObject.Query_PR_Merge()
            apiObc = AuthApi()
            if pr_data is not None:
                for var in pr_data:
                    pr_id = var['id']
                    pr_owner = var['repo_org']
                    pr_repo = var['repo_name']
                    pr_num = var['pr_num']
                    pr_url = var['repo_url']
                    if 'gitee.com' in pr_url:
                        pr_response = apiObc.getPrInfo(pr_owner, pr_repo, pr_num)
                    else:
                        pr_response = apiObc.getPrInfoByGithub(pr_owner, pr_repo, pr_num)
                    if pr_response == 403 or pr_response == 404:
                        continue
                    prData = pr_response.data.decode('utf-8')
                    prData = json.loads(prData)
                    mergedAt = prData['merged_at']
                    if mergedAt is not None:
                        itemData = (1, pr_id)
                        dbObject.upd_PR_State(itemData)
        finally:
            dbObject.Close_Con()
        
    @catch_error    
    def sca_repo(self):
        sca_obj = ScheduleSca()
        sca_obj.sca_repo()

