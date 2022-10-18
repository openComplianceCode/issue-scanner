import requests

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