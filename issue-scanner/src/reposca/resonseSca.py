
import json
import logging
import urllib3
logging.getLogger().setLevel(logging.INFO)

class ResonseSca(object):

    def __init__(self, url, parameter, result, purl):
        self._url_ = url
        self._para_ = parameter
        self._result_ = result
        self._purl_ = purl

    def httpReq(self):
        try:
            headers={'Content-Type': 'application/json; charset=UTF-8'}
            payload={self._purl_ : self._result_}  
            jsonRe = json.dumps(payload)   
            http = urllib3.PoolManager() 
            response = http.request('POST',self._url_+'?' + self._para_ + '='+jsonRe, headers=headers)
        except Exception as e:
            logging.exception(e)
