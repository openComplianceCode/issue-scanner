
import os
from os.path import basename
from tqdm import tqdm
import requests


class Down(object):

    #Breakpoint download
    def downLoad(slef, url, filePath, retryTimes):
        '''
        :param url: Download link
        :param filePath: Download path
        :param retryTimes: Number of retries
        :param proxies: proxy
        :retrun: filePath
        '''
        #Recount times
        count = 0
        #Request to get the total file size
        requests.packages.urllib3.disable_warnings()
        topReq = requests.get(url, stream = True, verify = False)

        totalSize = int(topReq.headers.get('content-length', 0))

        #Determine whether the local file exists, and obtain the file data size if it exists
        if os.path.exists(filePath):
            tempSize = os.path.getsize(filePath)
        else:
            tempSize = 0

        #Download
        fileName = basename(filePath)
        while count < retryTimes:
            if count != 0:
                tempSize = os.path.getsize(filePath)

            if tempSize >= totalSize:
                break

            count += 1
            #When requesting a download, start downloading from the location where it was downloaded.
            headers = {"Range": f"bytes={tempSize}-{totalSize}"}
            downReq = requests.get(url, stream=True, verify=False, headers=headers)

            tempTotal = totalSize - tempSize
            with open(filePath, "ab") as code, tqdm(desc="Down "+fileName, total=tempTotal, unit='iB', unit_scale=True, unit_divisor=1024) as bar:
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