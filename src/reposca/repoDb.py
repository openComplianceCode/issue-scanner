# -- coding: utf-8 --
from distutils import config
from DBUtils.PooledDB import PooledDB
import logging
import traceback
import pymysql


class RepoDb(object):

    # 定义初始化数据库连接
    def __init__(self, host_db='127.0.0.1', user_db='root', password_db='root',
                 name_db='gitee', port_db=3306):
        '''
        :param host_db: 数据库服务主机IP
        :param user_db: 数据库连接用户名
        :param password_db: 数据库密码
        :param name_db: 数据库名称
        :param port_db: 数据库端口号，整型数据
        :param link_type: 连接类型，用于设置输出数据是元祖还是字典，默认是字典，link_type=0
        :return:游标
        '''
        try:
            self.POOL = PooledDB(
                creator = pymysql,
                maxconnections = 30, #连接池允许的最大连接数，0和None表示不限制连接数
                mincached = 2, #初始化时候，连接池中至少创建的空闲的链接，0表示不创建
                maxcached = 5, # 链接池中最多闲置的链接，0和None不限制
                maxshared = 3,# 链接池中最多共享的链接数量，0和None表示全部共享。PS: 无用，因为pymysql和MySQLdb等模块的 threadsafety都为1，所有值无论设置为多少，_maxcached永远为0，所以永远是所有链接都共享。
                blocking =True,#连接池中如果没有可用链接后，是否阻塞等待。True，等待；False，不等待然后报错
                maxusage = None, #一个链接最多被重复使用的次数，None表示无限制
                setsession=[], #开始会话前执行的命令咧白哦。如['set datastyle to ...','set time zone ... ']
                ping = 0 , #ping MYSQL 服务端口，检查是否服务克重。 如：0 = None = Never， 1 = default = whenever it is requested, 2 = when a cursor is created，4 = when a query is excuted , 7 =always
                host=host_db,
                user=user_db,
                password=password_db,
                database=name_db,
                port=port_db,
                charset = 'utf8'
            )
            self.conn = self.POOL.connection()
            self.cur = self.conn.cursor(cursor=pymysql.cursors.DictCursor)
        except pymysql.Error as e:
            logger = logging.getLogger(__name__)
            logger.exception("创建数据库连接失败|Mysql Error %d: %s" %
                             (e.args[0], e.args[1]))
            logger.exception(e)

    def Buid_data(self, repoData):
        '''
        新增repo数据
        '''
        try:
            sql = "INSERT INTO gitee_repo ( gitee_id, repo_name, repo_org, repo_url, repo_license, repo_language, fork_num, star_num) VALUES (%s, %s, %s, %s, %s, %s, %s , %s )"

            self.cur.executemany(sql, repoData)
            # self.cur.execute(sql, repoData)
            self.conn.commit()

        except pymysql.Error as e:
            # Rollback in case there is any error
            # 输出异常信息
            logger = logging.getLogger(__name__)
            logger.exception(e)
            traceback.print_exc()
            self.conn.rollback()

    def Buid_OwnerData(self, ownerData):
        '''
        新增owner数据
        '''
        try:

            sql = "INSERT INTO repo_owner ( repo_id, gitee_id, login, user_url, owner_name)  VALUES (%s, %s, %s, %s, %s)"
            self.cur.execute('SET character_set_connection=utf8;')
            self.cur.executemany(sql, ownerData)
            self.conn.commit()

        except pymysql.Error as e:
            logger = logging.getLogger(__name__)
            logger.exception(e)
            traceback.print_exc()
            self.conn.rollback()

    def Query_AllRepo(self):
        '''
        获取repo数据
        '''
        try:
            sql = "SELECT id,repo_name,repo_org, repo_url, sca_json, commite FROM gitee_repo WHERE  repo_url IS NOT NULL and sca_json is null"
            self.cur.execute(sql)
            repoList = self.cur.fetchall()
            return repoList
        except pymysql.Error as e:
            logger = logging.getLogger(__name__)
            logger.exception(e)
            traceback.print_exc()

    def Modify_Repo(self, repoData):
        '''
        更新repo数据
        '''
        try:
            sql = "UPDATE gitee_repo set sca_json = '%s' WHERE repo_org = '%s' and repo_name = '%s'"
            self.cur.execute(sql % repoData)
            self.conn.commit()
            self.conn.close()
        except pymysql.Error as e:
            logger = logging.getLogger(__name__)
            logger.exception(e)
            traceback.print_exc()
            self.conn.rollback()

    def Query_Repo_ByName(self, repoData):
        '''
        根据repo name 查询repo数据
        '''
        try:
            sql = "SELECT id,commite,repo_name, repo_org, repo_url, repo_license, is_pro_license, spec_license, \
                is_approve_license, is_copyright FROM gitee_repo WHERE repo_org ='%s' and repo_name = '%s' and deleted_at is null"
            self.cur.execute(sql % repoData)
            repoList = self.cur.fetchone()
            return repoList
        except pymysql.Error as e:
            logger = logging.getLogger(__name__)
            logger.exception(e)
            traceback.print_exc()

    def Query_Repo_ByVersion(self, repoData):
        '''
        根据repo name 查询repo数据
        '''
        try:
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

    
    def Query_Repo_ByTime(self, repoData):
        '''
        根据repo name 查询repo数据 获取最新一次
        '''
        try:
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

    def Query_RepoByOrg(self, repoOrg):
        '''
        获取repo数据
        '''
        try:
            sql = "SELECT * FROM gitee_repo WHERE repo_org ='%s'"
            self.cur.execute(sql % repoOrg)
            repoList = self.cur.fetchall()
            return repoList
        except pymysql.Error as e:
            logger = logging.getLogger(__name__)
            logger.exception(e)
            traceback.print_exc()

    def Check_license(self, repoData):
        '''
        检查license是否认证
        '''
        try:
            sql = "SELECT spdx_name FROM spdx_license WHERE spdx_name ='%s' and (osi_approved = 1 or fsf_approved = 1)"
            self.cur.execute(sql % repoData)
            repoList = self.cur.fetchall()
            return repoList
        except pymysql.Error as e:
            logger = logging.getLogger(__name__)
            logger.exception(e)
            traceback.print_exc()

    def Modify_RepoSig(self, repoData):
        '''
        更新repo数据的sig组
        '''
        try:
            sql = "UPDATE gitee_repo set repo_owner = '%s' WHERE repo_org = '%s' and repo_name = '%s'"
            self.cur.execute(sql % repoData)
            self.conn.commit()
        except pymysql.Error as e:
            logger = logging.getLogger(__name__)
            logger.exception(e)
            traceback.print_exc()
            self.conn.rollback()

    def Modify_RepoSca(self, repoData):
        '''
        更新repo的扫描结果
        '''
        try:
            sql = "UPDATE gitee_repo set is_pro_license = '%s',spec_license = '%s', is_approve_license = '%s', is_copyright = '%s' WHERE id = %s"
            self.cur.execute(sql % repoData)
            self.conn.commit()
        except pymysql.Error as e:
            logger = logging.getLogger(__name__)
            logger.exception(e)
            traceback.print_exc()
            self.conn.rollback()

    def Query_License_BySpdx(self, repoData):
        '''
        根据spdx 查询license数据
        '''
        try:
            sql = "SELECT id,name,spdx_name FROM licenses WHERE spdx_name = '%s'"
            self.cur.execute(sql % repoData)
            repoList = self.cur.fetchone()
            return repoList
        except pymysql.Error as e:
            logger = logging.getLogger(__name__)
            logger.exception(e)
            traceback.print_exc()

    def Modify_License(self, repoData):
        '''
        更新license信息
        '''
        try:
            sql = "UPDATE licenses set is_yaml = '%s',oe_approved = '%s', low_risk = '%s', black = '%s', blackReason = '%s' , alias = '%s' WHERE id = %s"
            self.cur.execute(sql % repoData)
            self.conn.commit()
        except pymysql.Error as e:
            logger = logging.getLogger(__name__)
            logger.exception(e)
            traceback.print_exc()
            self.conn.rollback()

    def add_LicData(self, licData):
        '''
        新增license数据
        '''
        try:
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
    
    def get_ItemLic(self, itemData):
        '''
        根据url 查询项目数据
        '''
        try:
            sql = "SELECT id,commite,repo_name, repo_org, repo_url, repo_license, is_pro_license FROM item_lic WHERE \
                repo_org = '%s' and repo_name = '%s' and deleted_at is null"
            self.cur.execute(sql % itemData)
            repoList = self.cur.fetchone()
            return repoList
        except pymysql.Error as e:
            logger = logging.getLogger(__name__)
            logger.exception(e)
            traceback.print_exc()

    def add_ItemLic(self, licData):
        '''
        新增item_lic数据
        '''
        try:
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
    
    def upd_ItemLic(self, licData):
        '''
        更新item_lic数据
        '''
        try:
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
    
    def add_PR(self, licData):
        '''
        新增pr数据
        '''
        try:
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
    
    def upd_PR(self, licData):
        '''
        更新pr数据
        '''
        try:
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

    def Query_PR(self, repoData):
        '''
        根据repo pr_num 查询PR数据
        '''
        try:
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
    
    def Close_Con(self):
        '''
        关闭连接
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
        查询未合并PR数据
        '''
        try:
            sql = "SELECT id,commite, repo_name, repo_org, repo_url, pr_num FROM repo_pr WHERE is_merg = 0 and deleted_at is null \
                 and updated_at <= DATE_SUB(NOW(),INTERVAL 1 day)"
            self.cur.execute(sql)
            repoList = self.cur.fetchall()
            return repoList
        except pymysql.Error as e:
            logger = logging.getLogger(__name__)
            logger.exception(e)
            traceback.print_exc()
    
    def upd_PR_State(self, licData):
        '''
        更新pr合并数据
        '''
        try:
            sql = "UPDATE repo_pr set  is_merg = '%s', updated_at = SYSDATE() WHERE id = %s"
            self.cur.execute(sql % licData)
            self.conn.commit()
        except pymysql.Error as e:
            logger = logging.getLogger(__name__)
            logger.exception(e)
            traceback.print_exc()
            self.conn.rollback()