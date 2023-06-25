import logging
import requests
import urllib3

from util.catchUtil import catch_error
ACCESS_TOKEN = '694b8482b84b3704c70bceef66e87606'
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
        apiUrl = 'https://gitee.com/api/v5/repos/'+owner+'/'+repo+'/pulls/'+num+'?access_token='+ACCESS_TOKEN
        response = http.request('GET',apiUrl)       
        resStatus = response.status
        if resStatus == 403:
            logging.error("GITEE API LIMIT")
            return 403
        if resStatus == 404:
            logging.error("GITEE API ERROR")
            return 404
        
        return response