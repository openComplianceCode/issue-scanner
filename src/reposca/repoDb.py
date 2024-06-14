# -- coding: utf-8 --
from distutils import config
from DBUtils.PooledDB import PooledDB
import logging
import traceback
import pymysql


class RepoDb(object):

    # Define initial database connection
    def __init__(self, host_db='127.0.0.1', user_db='root', password_db='root',
                 name_db='gitee', port_db=3306):
        '''
        :param host_db: Database service host IP
        :param user_db: Database connection user name
        :param password_db: Database password
        :param name_db: Name database
        :param port_db: Database port number, integer data
        :param link_type: Connection type, used to set whether the output data is a tuple or a dictionary. The default is a dictionary.，link_type=0
        :return: Cursor
        '''
        try:
            self.POOL = PooledDB(
                creator = pymysql,
                maxconnections = 30, # The maximum number of connections allowed by the connection pool. 0 and None indicate no limit on the number of connections.
                mincached = 2, # During initialization, at least the idle link created in the connection pool, 0 means not created
                maxcached = 5, # The most idle links in the link pool, 0 and None are not limited
                maxshared = 3,# The maximum number of shared links in the link pool, 0 and None indicate all sharing. PS: Useless, because the threadsafety of modules such as pymysql and MySQLdb is 1, no matter what value is set, _maxcached is always 0, so all links are always shared.
                blocking =True,# Whether to block and wait if there is no available link in the connection pool. True, wait; False, do not wait and then report an error
                maxusage = None, # The maximum number of times a link can be reused, None means unlimited
                setsession=[], # The command executed before starting the session is blank. Such as ['set datastyle to ...', 'set time zone ... ']
                ping = 0 , # Ping the MYSQL service port to check whether the service is heavy. For example: 0 = None = Never, 1 = default = whenever it is requested, 2 = when a cursor is created, 4 = when a query is excuted, 7 = always
                host=host_db,
                user=user_db,
                password=password_db,
                database=name_db,
                port=port_db,
                charset = 'utf8'
            )
        except pymysql.Error as e:
            logger = logging.getLogger(__name__)
            logger.exception("Failed to create database connection|Mysql Error %d: %s" %
                             (e.args[0], e.args[1]))
            logger.exception(e)

    def Buid_data(self, repoData):
        '''
        Add repo data
        '''
        try:
            self.conn = self.POOL.connection()
            self.cur = self.conn.cursor(cursor=pymysql.cursors.DictCursor)
            sql = "INSERT INTO gitee_repo ( gitee_id, repo_name, repo_org, repo_url, repo_license, repo_language, fork_num, star_num) VALUES (%s, %s, %s, %s, %s, %s, %s , %s )"

            self.cur.executemany(sql, repoData)
            # self.cur.execute(sql, repoData)
            self.conn.commit()

        except pymysql.Error as e:
            # Rollback in case there is any error
            # Output exception information
            logger = logging.getLogger(__name__)
            logger.exception(e)
            traceback.print_exc()
            self.conn.rollback()
        finally:
            self.Close_Con()

    def Buid_OwnerData(self, ownerData):
        '''
        Add owner data
        '''
        try:
            self.conn = self.POOL.connection()
            self.cur = self.conn.cursor(cursor=pymysql.cursors.DictCursor)
            sql = "INSERT INTO repo_owner ( repo_id, gitee_id, login, user_url, owner_name)  VALUES (%s, %s, %s, %s, %s)"
            self.cur.execute('SET character_set_connection=utf8;')
            self.cur.executemany(sql, ownerData)
            self.conn.commit()

        except pymysql.Error as e:
            logger = logging.getLogger(__name__)
            logger.exception(e)
            traceback.print_exc()
            self.conn.rollback()
        finally:
            self.Close_Con()

    def Query_AllRepo(self):
        '''
        Get repo data
        '''
        try:
            self.conn = self.POOL.connection()
            self.cur = self.conn.cursor(cursor=pymysql.cursors.DictCursor)
            sql = "SELECT id,repo_name,repo_org, repo_url, sca_json, commite FROM gitee_repo WHERE  repo_url IS NOT NULL and sca_json is null"
            self.cur.execute(sql)
            repoList = self.cur.fetchall()
            return repoList
        except pymysql.Error as e:
            logger = logging.getLogger(__name__)
            logger.exception(e)
            traceback.print_exc()
        finally:
            self.Close_Con()

    def Modify_Repo(self, repoData):
        '''
        Update repo data
        '''
        try:
            self.conn = self.POOL.connection()
            self.cur = self.conn.cursor(cursor=pymysql.cursors.DictCursor)
            sql = "UPDATE gitee_repo set sca_json = '%s' WHERE repo_org = '%s' and repo_name = '%s'"
            self.cur.execute(sql % repoData)
            self.conn.commit()
            self.conn.close()
        except pymysql.Error as e:
            logger = logging.getLogger(__name__)
            logger.exception(e)
            traceback.print_exc()
            self.conn.rollback()
        finally:
            self.Close_Con()

    def Query_Repo_ByName(self, repoData):
        '''
        Query repo data based on repo name
        '''
        try:
            self.conn = self.POOL.connection()
            self.cur = self.conn.cursor(cursor=pymysql.cursors.DictCursor)
            sql = "SELECT id,commite,repo_name, repo_org, repo_url, repo_license, is_pro_license, spec_license, \
                is_approve_license, is_copyright FROM gitee_repo WHERE repo_org ='%s' and repo_name = '%s' and deleted_at is null"
            self.cur.execute(sql % repoData)
            repoList = self.cur.fetchone()
            return repoList
        except pymysql.Error as e:
            logger = logging.getLogger(__name__)
            logger.exception(e)
            traceback.print_exc()
        finally:
            self.Close_Con()

    def Query_Repo_ByVersion(self, repoData):
        '''
        Query repo data based on repo name
        '''
        try:
            self.conn = self.POOL.connection()
            self.cur = self.conn.cursor(cursor=pymysql.cursors.DictCursor)
            sql = "SELECT id,commite,repo_name, repo_org, repo_url, repo_license, is_pro_license, spec_license, sca_json,\
                is_approve_license, is_copyright FROM gitee_repo WHERE repo_org ='%s' and repo_name = '%s' and \
                    commite = '%s' and deleted_at is null"
            self.cur.execute(sql % repoData)
            repoList = self.cur.fetchone()
            return repoList
        except pymysql.Error as e:
            logger = logging.getLogger(__name__)
            logger.exception(e)
            traceback.print_exc()
        finally:
            self.Close_Con()

    
    def Query_Repo_ByTime(self, repoData):
        '''
        Query repo data based on repo name and get the latest one
        '''
        try:
            self.conn = self.POOL.connection()
            self.cur = self.conn.cursor(cursor=pymysql.cursors.DictCursor)
            sql = "SELECT id,commite,repo_name, repo_org, repo_url, repo_license, is_pro_license, spec_license, sca_json,\
                is_approve_license, is_copyright FROM gitee_repo WHERE repo_org ='%s' and repo_name = '%s' and deleted_at is null\
                    ORDER BY updated_at DESC limit 1"
            self.cur.execute(sql % repoData)
            repoList = self.cur.fetchone()
            return repoList
        except pymysql.Error as e:
            logger = logging.getLogger(__name__)
            logger.exception(e)
            traceback.print_exc()
        finally:
            self.Close_Con()

    def Query_RepoByOrg(self, repoOrg):
        '''
        Get repo data
        '''
        try:
            self.conn = self.POOL.connection()
            self.cur = self.conn.cursor(cursor=pymysql.cursors.DictCursor)
            sql = "SELECT * FROM gitee_repo WHERE repo_org ='%s'"
            self.cur.execute(sql % repoOrg)
            repoList = self.cur.fetchall()
            return repoList
        except pymysql.Error as e:
            logger = logging.getLogger(__name__)
            logger.exception(e)
            traceback.print_exc()
        finally:
            self.Close_Con()

    def Check_license(self, repoData):
        '''
        Check whether the license is certified
        '''
        try:
            self.conn = self.POOL.connection()
            self.cur = self.conn.cursor(cursor=pymysql.cursors.DictCursor)
            sql = "SELECT spdx_name FROM spdx_license WHERE spdx_name ='%s' and (osi_approved = 1 or fsf_approved = 1)"
            self.cur.execute(sql % repoData)
            repoList = self.cur.fetchall()
            return repoList
        except pymysql.Error as e:
            logger = logging.getLogger(__name__)
            logger.exception(e)
            traceback.print_exc()
        finally:
            self.Close_Con()

    def Modify_RepoSig(self, repoData):
        '''
        Update the sig group of repo data
        '''
        try:
            self.conn = self.POOL.connection()
            self.cur = self.conn.cursor(cursor=pymysql.cursors.DictCursor)
            sql = "UPDATE gitee_repo set repo_owner = '%s' WHERE repo_org = '%s' and repo_name = '%s'"
            self.cur.execute(sql % repoData)
            self.conn.commit()
        except pymysql.Error as e:
            logger = logging.getLogger(__name__)
            logger.exception(e)
            traceback.print_exc()
            self.conn.rollback()
        finally:
            self.Close_Con()

    def Modify_RepoSca(self, repoData):
        '''
        Update scan results of repo
        '''
        try:
            self.conn = self.POOL.connection()
            self.cur = self.conn.cursor(cursor=pymysql.cursors.DictCursor)
            sql = "UPDATE gitee_repo set is_pro_license = '%s',spec_license = '%s', is_approve_license = '%s', is_copyright = '%s' WHERE id = %s"
            self.cur.execute(sql % repoData)
            self.conn.commit()
        except pymysql.Error as e:
            logger = logging.getLogger(__name__)
            logger.exception(e)
            traceback.print_exc()
            self.conn.rollback()
        finally:
            self.Close_Con

    def Query_License_BySpdx(self, repoData):
        '''
        Query license data based on spdx
        '''
        try:
            self.conn = self.POOL.connection()
            self.cur = self.conn.cursor(cursor=pymysql.cursors.DictCursor)
            sql = "SELECT id,name,spdx_name FROM licenses WHERE spdx_name = '%s'"
            self.cur.execute(sql % repoData)
            repoList = self.cur.fetchone()
            return repoList
        except pymysql.Error as e:
            logger = logging.getLogger(__name__)
            logger.exception(e)
            traceback.print_exc()
        finally:
            self.Close_Con()

    def Modify_License(self, repoData):
        '''
        Update license information
        '''
        try:
            self.conn = self.POOL.connection()
            self.cur = self.conn.cursor(cursor=pymysql.cursors.DictCursor)
            sql = "UPDATE licenses set is_yaml = '%s',oe_approved = '%s', low_risk = '%s', black = '%s', blackReason = '%s' , alias = '%s' WHERE id = %s"
            self.cur.execute(sql % repoData)
            self.conn.commit()
        except pymysql.Error as e:
            logger = logging.getLogger(__name__)
            logger.exception(e)
            traceback.print_exc()
            self.conn.rollback()
        finally:
            self.Close_Con()

    def add_LicData(self, licData):
        '''
        Add license data
        '''
        try:
            self.conn = self.POOL.connection()
            self.cur = self.conn.cursor(cursor=pymysql.cursors.DictCursor)
            sql = "INSERT INTO licenses (created_at, updated_at, name, spdx_name, osi_approved, fsf_approved, summary,\
                 full_text, full_text_plain, summary_from_spdx, web_page_from_spdx, standard_license_header_from_spdx, \
                 is_yaml, oe_approved, low_risk, black, blackReason, alias)  \
                 VALUES (SYSDATE(), SYSDATE(), '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s'\
                     , '%s', '%s', '%s')"
            self.cur.execute(sql % licData)
            self.conn.commit()
        except pymysql.Error as e:
            logger = logging.getLogger(__name__)
            logger.exception(e)
            traceback.print_exc()
            self.conn.rollback()
        finally:
            self.Close_Con()
    
    def get_ItemLic(self, itemData):
        '''
        Query project data based on url
        '''
        try:
            self.conn = self.POOL.connection()
            self.cur = self.conn.cursor(cursor=pymysql.cursors.DictCursor)
            sql = "SELECT id,commite,repo_name, repo_org, repo_url, repo_license, is_pro_license FROM item_lic WHERE \
                repo_org = '%s' and repo_name = '%s' and deleted_at is null"
            self.cur.execute(sql % itemData)
            repoList = self.cur.fetchone()
            return repoList
        except pymysql.Error as e:
            logger = logging.getLogger(__name__)
            logger.exception(e)
            traceback.print_exc()
        finally:
            self.Close_Con()

    def add_ItemLic(self, licData):
        '''
        Add item_lic data
        '''
        try:
            self.conn = self.POOL.connection()
            self.cur = self.conn.cursor(cursor=pymysql.cursors.DictCursor)
            sql = "INSERT INTO gitee_repo (repo_name, repo_org, repo_url, repo_license, sca_json, is_pro_license, \
                spec_license, is_approve_license, is_copyright, commite, purl, created_at, updated_at)\
                 VALUES ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s','%s','%s','%s',SYSDATE(), SYSDATE())"
            self.cur.execute(sql % licData)
            self.conn.commit()
        except pymysql.Error as e:
            logger = logging.getLogger(__name__)
            logger.exception(e)
            traceback.print_exc()
            self.conn.rollback()
        finally:
            self.Close_Con()
    
    def upd_ItemLic(self, licData):
        '''
        Update item_lic data
        '''
        try:
            self.conn = self.POOL.connection()
            self.cur = self.conn.cursor(cursor=pymysql.cursors.DictCursor)
            sql = "UPDATE gitee_repo set commite = '%s', repo_license = '%s', sca_json = '%s', is_pro_license = '%s', \
                spec_license = '%s', is_approve_license = '%s', is_copyright = '%s', updated_at = SYSDATE()\
                 WHERE id = %s"
            self.cur.execute(sql % licData)
            self.conn.commit()
        except pymysql.Error as e:
            logger = logging.getLogger(__name__)
            logger.exception(e)
            traceback.print_exc()
            self.conn.rollback()
        finally:
            self.Close_Con()
    
    def add_PR(self, licData):
        '''
        Add PR data
        '''
        try:
            self.conn = self.POOL.connection()
            self.cur = self.conn.cursor(cursor=pymysql.cursors.DictCursor)
            sql = "INSERT INTO repo_pr (repo_name, repo_org, repo_url, repo_license, pr_num, sca_json, is_pro_license, spec_license,\
                is_approve_license, is_copyright, commite, is_pass, is_merg, pr_url, created_at, updated_at, status, message) VALUES\
                ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', SYSDATE(), SYSDATE(), '%s', '%s')"
            self.cur.execute(sql % licData)
            self.conn.commit()
        except pymysql.Error as e:
            logger = logging.getLogger(__name__)
            logger.exception(e)
            traceback.print_exc()
            self.conn.rollback()
        finally:
            self.Close_Con()
    
    def upd_PR(self, licData):
        '''
        Update pr data
        '''
        try:
            self.conn = self.POOL.connection()
            self.cur = self.conn.cursor(cursor=pymysql.cursors.DictCursor)
            sql = "UPDATE repo_pr set  repo_license = '%s', sca_json = '%s', is_pro_license = '%s', spec_license = '%s',\
                is_approve_license = '%s', is_copyright = '%s', is_pass = '%s', is_merg = '%s', status = '%s', \
                message = '%s', updated_at = SYSDATE() WHERE id = %s"
            self.cur.execute(sql % licData)
            self.conn.commit()
        except pymysql.Error as e:
            logger = logging.getLogger(__name__)
            logger.exception(e)
            traceback.print_exc()
            self.conn.rollback()
        finally:
            self.Close_Con()

    def Query_PR(self, repoData):
        '''
        Query PR data based on repo pr_num
        '''
        try:
            self.conn = self.POOL.connection()
            self.cur = self.conn.cursor(cursor=pymysql.cursors.DictCursor)
            sql = "SELECT id,commite,repo_name, repo_org, repo_url, repo_license, is_pro_license, spec_license, sca_json,\
                is_approve_license, is_copyright FROM repo_pr WHERE repo_org ='%s' and repo_name = '%s' and \
                    pr_num = '%s' and deleted_at is null"
            self.cur.execute(sql % repoData)
            repoList = self.cur.fetchone()
            return repoList
        except pymysql.Error as e:
            logger = logging.getLogger(__name__)
            logger.exception(e)
            traceback.print_exc()
        finally:
            self.Close_Con()
    
    def Close_Con(self):
        '''
        close connection
        '''
        try:
            self.cur.close()
            self.conn.close()           
        except pymysql.Error as e:
            logger = logging.getLogger(__name__)
            logger.exception(e)
            traceback.print_exc()
    
    def Query_PR_Merge(self):
        '''
        Query unmerged PR data
        '''
        try:
            self.conn = self.POOL.connection()
            self.cur = self.conn.cursor(cursor=pymysql.cursors.DictCursor)
            sql = "SELECT id,commite, repo_name, repo_org, repo_url, pr_num FROM repo_pr WHERE is_merg = 0 and deleted_at is null \
                 and updated_at <= DATE_SUB(NOW(),INTERVAL 1 day)"
            self.cur.execute(sql)
            repoList = self.cur.fetchall()
            return repoList
        except pymysql.Error as e:
            logger = logging.getLogger(__name__)
            logger.exception(e)
            traceback.print_exc()
        finally:
            self.Close_Con()
    
    def upd_PR_State(self, licData):
        '''
        Update pr merged data
        '''
        try:
            self.conn = self.POOL.connection()
            self.cur = self.conn.cursor(cursor=pymysql.cursors.DictCursor)
            sql = "UPDATE repo_pr set  is_merg = '%s', updated_at = SYSDATE() WHERE id = %s"
            self.cur.execute(sql % licData)
            self.conn.commit()
        except pymysql.Error as e:
            logger = logging.getLogger(__name__)
            logger.exception(e)
            traceback.print_exc()
            self.conn.rollback()
        finally:
            self.Close_Con()

    def Get_Licenses(self):
        '''
        Get License
        '''
        try:
            self.conn = self.POOL.connection()
            self.cur = self.conn.cursor(cursor=pymysql.cursors.DictCursor)
            sql = "SELECT name,spdx_name,osi_approved,fsf_approved,oe_approved,low_risk,black,blackReason,alias \
                FROM licenses deleted_at IS NULL"
            self.cur.execute(sql)
            repoList = self.cur.fetchall()
            return repoList
        except pymysql.Error as e:
            logger = logging.getLogger(__name__)
            logger.exception(e)
            traceback.print_exc()
        finally:
            self.Close_Con()
        
    
    def Query_License_Enter(self):
        '''
        Non-admission license statistics
        '''
        try:
            self.conn = self.POOL.connection()
            self.cur = self.conn.cursor(cursor=pymysql.cursors.DictCursor)
            sql = "SELECT repo_name,repo_org,pr_num,is_pass,is_merg FROM repo_pr WHERE is_pass = 0 \
                AND (is_pro_license LIKE '%非OSI/FSF%' OR spec_license LIKE '%非OSI/FSF%' OR \
                    is_approve_license LIKE '%非OSI/FSF%' OR is_pro_license LIKE '%缺少项目%')"
            self.cur.execute(sql)
            repoList = self.cur.fetchall()
            return repoList
        except pymysql.Error as e:
            logger = logging.getLogger(__name__)
            logger.exception(e)
            traceback.print_exc()
        finally:
            self.Close_Con()
    
    def Query_License_Enter_org(self, licData):
        '''
        Non-admission license statistics community
        '''
        try:
            self.conn = self.POOL.connection()
            self.cur = self.conn.cursor(cursor=pymysql.cursors.DictCursor)
            sql = "SELECT repo_name,repo_org,pr_num,is_pass,is_merg FROM repo_pr WHERE is_pass = 0 and repo_org = '%s' AND \
                (is_pro_license LIKE '%%非OSI/FSF%%' OR spec_license LIKE '%%非OSI/FSF%%' OR \
                    is_approve_license LIKE '%%非OSI/FSF%%' OR is_pro_license LIKE '%%缺少项目%%')"
            self.cur.execute(sql % licData)
            repoList = self.cur.fetchall()
            return repoList
        except pymysql.Error as e:
            logger = logging.getLogger(__name__)
            logger.exception(e)
            traceback.print_exc()
        finally:
            self.Close_Con()
            
    def Query_License_Enter_repo(self, licData):
        '''
        Non-admission license statistics single warehouse
        '''
        try:
            self.conn = self.POOL.connection()
            self.cur = self.conn.cursor(cursor=pymysql.cursors.DictCursor)
            sql = "SELECT repo_name,repo_org,pr_num,is_pass,is_merg,is_pro_license,spec_license,is_approve_license FROM \
                  repo_pr WHERE is_pass = 0 and repo_org = '%s' and repo_name = '%s'AND (is_pro_license LIKE '%%非OSI/FSF%%' \
                    OR spec_license LIKE '%%非OSI/FSF%%' OR is_approve_license LIKE '%%非OSI/FSF%%'  OR is_pro_license LIKE '%%缺少项目%%')"
            self.cur.execute(sql % licData)
            repoList = self.cur.fetchall()
            return repoList
        except pymysql.Error as e:
            logger = logging.getLogger(__name__)
            logger.exception(e)
            traceback.print_exc()
        finally:
            self.Close_Con()
    
    def Query_License_Spec(self):
        '''
        spec License verification
        '''
        try:
            self.conn = self.POOL.connection()
            self.cur = self.conn.cursor(cursor=pymysql.cursors.DictCursor)
            sql = "SELECT repo_name, repo_org, pr_num, is_pass, is_merg FROM repo_pr WHERE repo_org = 'src-openeuler' \
	            and is_pass = 0 and spec_license LIKE '%''pass'': False%'"
            self.cur.execute(sql)
            repoList = self.cur.fetchall()
            return repoList
        except pymysql.Error as e:
            logger = logging.getLogger(__name__)
            logger.exception(e)
            traceback.print_exc()
        finally:
            self.Close_Con()
    
    def Query_License_Spec_repo(self, licData):
        '''
        spec License verification repo dimensions
        '''
        try:
            self.conn = self.POOL.connection()
            self.cur = self.conn.cursor(cursor=pymysql.cursors.DictCursor)
            sql = "SELECT repo_name, repo_org, pr_num, is_pass, is_merg, spec_license FROM repo_pr WHERE repo_org = 'src-openeuler' \
	            and repo_name = '%s' and is_pass = 0 and spec_license LIKE '%%''pass'': False%%'"
            self.cur.execute(sql % licData)
            repoList = self.cur.fetchall()
            return repoList
        except pymysql.Error as e:
            logger = logging.getLogger(__name__)
            logger.exception(e)
            traceback.print_exc()
        finally:
            self.Close_Con()
    
    def Query_License_Un(self):
        '''
        License specification verification
        '''
        try:
            self.conn = self.POOL.connection()
            self.cur = self.conn.cursor(cursor=pymysql.cursors.DictCursor)
            sql = "SELECT repo_name,repo_org,pr_num,is_pass,is_merg FROM repo_pr WHERE is_pass = 0 \
                AND (is_pro_license LIKE '%不规范%' OR spec_license LIKE '%不规范%')"
            self.cur.execute(sql)
            repoList = self.cur.fetchall()
            return repoList
        except pymysql.Error as e:
            logger = logging.getLogger(__name__)
            logger.exception(e)
            traceback.print_exc()
        finally:
            self.Close_Con()

    def Query_License_Un_org(self, licData):
        '''
        License Specification Verification Community Dimension
        '''
        try:
            self.conn = self.POOL.connection()
            self.cur = self.conn.cursor(cursor=pymysql.cursors.DictCursor)
            sql = "SELECT repo_name,repo_org,pr_num,is_pass,is_merg FROM repo_pr WHERE is_pass = 0 and repo_org = '%s' \
                AND (is_pro_license LIKE '%%不规范%%' OR spec_license LIKE '%%不规范%%')"
            self.cur.execute(sql % licData)
            repoList = self.cur.fetchall()
            return repoList
        except pymysql.Error as e:
            logger = logging.getLogger(__name__)
            logger.exception(e)
            traceback.print_exc()
        finally:
            self.Close_Con()
    
    def Query_License_Un_repo(self, licData):
        '''
        License specification verification repo dimensions
        '''
        try:
            self.conn = self.POOL.connection()
            self.cur = self.conn.cursor(cursor=pymysql.cursors.DictCursor)
            sql = "SELECT repo_name,repo_org,pr_num,is_pass,is_merg,is_pro_license,spec_license FROM repo_pr WHERE is_pass = 0 \
                and repo_org = '%s' and repo_name = '%s' AND (is_pro_license LIKE '%%不规范%%' OR spec_license LIKE '%%不规范%%')"
            self.cur.execute(sql % licData)
            repoList = self.cur.fetchall()
            return repoList
        except pymysql.Error as e:
            logger = logging.getLogger(__name__)
            logger.exception(e)
            traceback.print_exc()
        finally:
            self.Close_Con()
    

    def Query_Copyright(self):
        '''
        Copyright Risk Statistics
        '''
        try:
            self.conn = self.POOL.connection()
            self.cur = self.conn.cursor(cursor=pymysql.cursors.DictCursor)
            sql = "SELECT repo_name,repo_org,pr_num,is_pass,is_merg FROM repo_pr WHERE is_pass = 0 \
                AND is_copyright LIKE '%%''pass'': False%%'"
            self.cur.execute(sql)
            repoList = self.cur.fetchall()
            return repoList
        except pymysql.Error as e:
            logger = logging.getLogger(__name__)
            logger.exception(e)
            traceback.print_exc()
        finally:
            self.Close_Con()
    
    def Query_Copyright_Org(self, licData):
        '''
        Copyright Risk Statistics-Community
        '''
        try:
            self.conn = self.POOL.connection()
            self.cur = self.conn.cursor(cursor=pymysql.cursors.DictCursor)
            sql = "SELECT repo_name,repo_org,pr_num,is_pass,is_merg FROM repo_pr WHERE is_pass = 0 AND repo_org = '%s'\
                AND is_copyright LIKE '%%''pass'': False%%'"
            self.cur.execute(sql % licData)
            repoList = self.cur.fetchall()
            return repoList
        except pymysql.Error as e:
            logger = logging.getLogger(__name__)
            logger.exception(e)
            traceback.print_exc()
        finally:
            self.Close_Con()
    
    def Query_Copyright_Repo(self, licData):
        '''
        Copyright Risk Statistics-repo
        '''
        try:
            self.conn = self.POOL.connection()
            self.cur = self.conn.cursor(cursor=pymysql.cursors.DictCursor)
            sql = "SELECT repo_name,repo_org,pr_num,is_pass,is_merg, is_copyright FROM repo_pr WHERE is_pass = 0 AND repo_org = '%s'\
                AND repo_name = '%s' AND is_copyright LIKE '%%''pass'': False%%'"
            self.cur.execute(sql % licData)
            repoList = self.cur.fetchall()
            return repoList
        except pymysql.Error as e:
            logger = logging.getLogger(__name__)
            logger.exception(e)
            traceback.print_exc()
        finally:
            self.Close_Con()

    def Query_PR_All(self, org):
        '''
        Get PR information
        '''
        try:
            self.conn = self.POOL.connection()
            self.cur = self.conn.cursor(cursor=pymysql.cursors.DictCursor)
            sql = "SELECT repo_name,repo_org,pr_num,is_pass,is_merg,is_pro_license,spec_license,is_approve_license, is_copyright \
                  FROM  repo_pr WHERE repo_org = '%s'"
            self.cur.execute(sql % org)
            repoList = self.cur.fetchall()
            return repoList
        except pymysql.Error as e:
            logger = logging.getLogger(__name__)
            logger.exception(e)
            traceback.print_exc()
        finally:
            self.Close_Con()

    def add_repo_sca(self, licData):
        '''
        Add sca data
        '''
        try:
            self.conn = self.POOL.connection()
            self.cur = self.conn.cursor(cursor=pymysql.cursors.DictCursor)
            sql = "INSERT INTO repo_sca (repo_name, repo_org, repo_url, repo_license, is_pro_license, \
                spec_license, is_approve_license, is_copyright, commite, created_at, updated_at, data_month, \
                    repo_lic_score, repo_approve_score, repo_cop_score)\
                 VALUES ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s','%s',SYSDATE(), SYSDATE(),\
                    '%s', '%s', '%s', '%s')"
            self.cur.execute(sql % licData)
            self.conn.commit()
        except pymysql.Error as e:
            logger = logging.getLogger(__name__)
            logger.exception(e)
            traceback.print_exc()
            self.conn.rollback()
        finally:
            self.Close_Con()
    
    def Query_Repo_Sca(self, repoData):
        try:
            self.conn = self.POOL.connection()
            self.cur = self.conn.cursor(cursor=pymysql.cursors.DictCursor)
            sql = "SELECT id,repo_name FROM repo_sca WHERE repo_org ='%s' and repo_name = '%s' and data_month = '%s'"
            self.cur.execute(sql % repoData)
            repoList = self.cur.fetchone()
            return repoList
        except pymysql.Error as e:
            logger = logging.getLogger(__name__)
            logger.exception(e)
            traceback.print_exc()
        finally:
            self.Close_Con()
    
    def Query_measure_org(self, repoData):
        try:
            self.conn = self.POOL.connection()
            self.cur = self.conn.cursor(cursor=pymysql.cursors.DictCursor)
            sql = "SELECT repo_name, repo_org, repo_lic_score, repo_approve_score, repo_cop_score,\
	                SUM(repo_lic_score+repo_approve_score+repo_cop_score) as repo_score FROM repo_sca\
                    WHERE data_month = '%s' AND repo_org = '%s' GROUP BY repo_name,repo_org,repo_lic_score,\
	                repo_approve_score, repo_cop_score"
            self.cur.execute(sql % repoData)
            repoList = self.cur.fetchall()
            return repoList
        except pymysql.Error as e:
            logger = logging.getLogger(__name__)
            logger.exception(e)
            traceback.print_exc()
        finally:
            self.Close_Con()

    
    def Query_measure_repo(self, repoData):
        try:
            self.conn = self.POOL.connection()
            self.cur = self.conn.cursor(cursor=pymysql.cursors.DictCursor)
            sql = "SELECT repo_name, repo_org, CAST(created_at AS CHAR) AS created_at, repo_lic_score, repo_approve_score, repo_cop_score,\
	                SUM(repo_lic_score+repo_approve_score+repo_cop_score) as repo_score FROM repo_sca\
                    WHERE data_month = '%s' AND repo_org = '%s' AND repo_name = '%s' GROUP BY repo_name,repo_org, created_at, \
                    repo_lic_score, repo_approve_score, repo_cop_score"
            self.cur.execute(sql % repoData)
            repoList = self.cur.fetchall()
            return repoList
        except pymysql.Error as e:
            logger = logging.getLogger(__name__)
            logger.exception(e)
            traceback.print_exc()
        finally:
            self.Close_Con()

    def add_repo_scaJson(self, licData):
        '''
        Add sca data
        '''
        try:
            self.conn = self.POOL.connection()
            self.cur = self.conn.cursor(cursor=pymysql.cursors.DictCursor)
            sql = "INSERT INTO repo_sca (repo_name, repo_org, repo_url, repo_license, sca_json, is_pro_license, \
                spec_license, is_approve_license, is_copyright, commite, created_at, updated_at, data_month, \
                    repo_lic_score, repo_approve_score, repo_cop_score)\
                 VALUES ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s','%s',SYSDATE(), SYSDATE(),\
                    '%s', '%s', '%s', '%s')"
            self.cur.execute(sql % licData)
            self.conn.commit()
        except pymysql.Error as e:
            logger = logging.getLogger(__name__)
            logger.exception(e)
            traceback.print_exc()
            self.conn.rollback()
        finally:
            self.Close_Con()

    def Query_sca_json(self, repoData):
        try:
            self.conn = self.POOL.connection()
            self.cur = self.conn.cursor(cursor=pymysql.cursors.DictCursor)
            sql = "SELECT repo_name, repo_org, sca_json FROM repo_sca WHERE repo_org = '%s' and commite = '%s'"
            self.cur.execute(sql % repoData)
            repoList = self.cur.fetchall()
            return repoList
        except pymysql.Error as e:
            logger = logging.getLogger(__name__)
            logger.exception(e)
            traceback.print_exc()
        finally:
            self.Close_Con()