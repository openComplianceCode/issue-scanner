
import os
from wsgiref import headers
from scipy.misc import electrocardiogram
from tqdm import tqdm
import requests


class Down(object):

    #断点下载
    def downLoad(slef, url, filePath, retryTimes):
        '''
        :param url: 下载连接
        :param filePath: 下载路径
        :param retryTimes: 重试次数
        :param proxies: proxy
        :retrun: filePath
        '''
        #重计次数
        count = 0
        #请求获取文件总大小
        topReq = requests.get(url, stream = True, verify = False)
        print(topReq.text)

        totalSize = int(topReq.headers.get('content-length', 0))

        #判断本地文件是否存在，存在则获取文件数据大小
        if os.path.exists(filePath):
            tempSize = os.path.getsize(filePath)
        else:
            tempSize = 0

        #下载
        while count < retryTimes:
            if count != 0:
                tempSize = os.path.getsize(filePath)

            #判断结束
            if tempSize >= totalSize:
                break

            count += 1
            #请求下载时,从下载过的地方开始下载
            headers = {"Range": f"bytes={tempSize}-{totalSize}"}
            downReq = requests.get(url, stream=True, verify=False, headers=headers)

            tempTotal = totalSize - tempSize
            with open(filePath, "ab") as code, tqdm(desc=filePath, total=tempTotal, unit='iB', unit_scale=True, unit_divisor=1024) as bar:
                if count != 1:
                    code.seek(tempSize)
                for data in downReq.iter_content(chunk_size=1024):
                    if data:
                        tempSize += len(data)
                        size = code.write(data)
                        code.flush()
                        bar.update(size)

                downReq.close()

        return filePath