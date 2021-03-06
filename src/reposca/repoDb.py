# -- coding: utf-8 --
from distutils import config
import logging
import traceback
import pymysql


class RepoDb(object):

    # 定义初始化数据库连接
    def __init__(self, host_db='127.0.0.1', user_db='root', password_db='root',
                 name_db='gitee', port_db=3306, link_type=0):
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
            if link_type == 0:
                # 创建数据，返回字典
                self.conn = pymysql.connect(host=host_db, user=user_db, password=password_db, db=name_db, port=port_db,
                                            cursorclass=pymysql.cursors.DictCursor)
            else:
                # 创建数据库，返回元祖
                self.conn = pymysql.connect(
                    host=host_db, user=user_db, password=password_db, db=name_db, port=port_db)
            self.cur = self.conn.cursor()
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

    #    CUR.close()  # 关闭游标
    #    CONN.close()  # 关闭连接

    def Buid_OwnerData(self, ownerData):
        '''
        新增owner数据
        '''
        try:

            sql = "INSERT INTO repo_owner ( repo_id, gitee_id, login, user_url, owner_name)  VALUES (%s, %s, %s, %s, %s)"
            # self.cur.executemany(sql, ownerData)
            self.cur.execute('SET character_set_connection=utf8;')
            self.cur.executemany(sql, ownerData)
            self.conn.commit()

        except pymysql.Error as e:
            # Rollback in case there is any error
            # 输出异常信息
            logger = logging.getLogger(__name__)
            logger.exception(e)
            traceback.print_exc()
            self.conn.rollback()

    def Query_AllRepo(self):
        '''
        获取repo数据
        '''
        try:

            sql = "SELECT repo_name,repo_org, repo_url, sca_json, repo_owner FROM gitee_repo WHERE repo_url IS NOT NULL"
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

            sql = "SELECT repo_name,sca_json FROM gitee_repo WHERE repo_name = '%s' and repo_org ='%s'"
            self.cur.execute(sql % repoData)

            repoList = self.cur.fetchone()

            self.conn.close()
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

            # self.conn.close()
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

            # self.conn.close()
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

            # self.conn.close()
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
