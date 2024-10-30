import logging
import os
import random
import requests
import urllib3
import yaml

from util.catchUtil import catch_error
USER_AGENT = [
    'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36 OPR/26.0.1656.60',
    'Opera/8.0 (Windows NT 5.1; U; en)',
    'Mozilla/5.0 (Windows NT 5.1; U; en; rv:1.8.1) Gecko/20061208 Firefox/2.0.0 Opera 9.50',
    'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; en) Opera 9.50',
    'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.71 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
    'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Chrome/10.0.648.133 Safari/534.16',
    'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:34.0) Gecko/20100101 Firefox/34.0',
    'Mozilla/5.0 (X11; U; Linux x86_64; zh-CN; rv:1.9.2.10) Gecko/20100922 Ubuntu/10.10 (maverick) Firefox/3.6.10'
]
logging.getLogger().setLevel(logging.INFO)

class AuthApi(object):
    def get_token(self, username, password, redirect_uri, client_id, client_secret, scope):
        query_params = {"username": username,
                        "password": password,
                        "redirect_uri": redirect_uri,
                        "client_id": client_id,
                        "client_secret": client_secret,
                        "grant_type": "password",
                        "scope": scope
                        }

        return requests.post("https://gitee.com/oauth/token", query_params, json=True).json()
    
    @catch_error    
    def getPrInfo(self, owner, repo, num):
        http = urllib3.PoolManager() 
        project_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))      
        config_url = project_path + '/token.yaml'
        CONF = yaml.safe_load(open(config_url))
        params = CONF['API_TOKEN']
        token_list = params.split(",")
        authorToken = random.choice(token_list)
        apiUrl = 'https://gitee.com/api/v5/repos/'+owner+'/'+repo+'/pulls/'+num+'?access_token='+authorToken.strip()
        response = http.request(
            'GET',
            apiUrl,
            headers = {'User-Agent': random.choice(USER_AGENT)}
        )       
        resStatus = response.status
        if resStatus == 403:
            token_list.remove(authorToken)
            while (len(token_list) > 0):
                authorToken = random.choice(token_list)
                apiUrl = 'https://gitee.com/api/v5/repos/'+owner+'/'+repo+'/pulls/'+num+'?access_token='+authorToken.strip()
                response = http.request(
                    'GET',
                    apiUrl,
                    headers = {'User-Agent': random.choice(USER_AGENT)}
                )         
                resStatus = response.status
                if resStatus == 200:
                    break
                else:
                    token_list.remove(authorToken)
        if resStatus == 403:
            logging.error("GITEE API LIMIT")
            return 403
        if resStatus == 404:
            logging.error("GITEE API ERROR")
            return 404
        
        return response

    def getPrInfoByGithub(self, owner, repo, num):
        http = urllib3.PoolManager() 
        authorToken = os.environ.get("GITHUB_TOKEN")    
        apiUrl = 'https://api.github.com/repos/'+owner+'/'+repo+'/pulls/'+num
        response = http.request(
            'GET',
            apiUrl,
            headers = {
                'User-Agent': random.choice(USER_AGENT),
                'Accept' : 'application/vnd.github+json',
                'Authorization':'Bearer ' + authorToken
            }
        )         
        resStatus = response.status
        if resStatus == 403:
            logging.error("GITHUB TOKEN LIMIT")
            return 403
        if resStatus == 404:
            logging.error("GITHUB API ERROR")
            return 404
        
        return response