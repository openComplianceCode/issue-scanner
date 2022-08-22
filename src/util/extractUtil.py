import gzip
import os
import tarfile
import traceback
import zipfile
import rarfile
from util.catchUtil import catch_error
from util.formateUtil import formateUrl

COMPRESSED_LIST = ['tar', 'tgz', 'zip', 'rar']

def extractCode(filePath):
    result = "inde"
    try:
        for deRoot,deDir,deFiles in os.walk(filePath):  
            for defile in deFiles:                        
                dePath = os.path.join(deRoot,defile)
                dePath = formateUrl(dePath)
                wrar = checkWrar(defile)
                #判断压缩文件
                if wrar in COMPRESSED_LIST:
                    result = "ref"
                    if wrar == 'tar' or wrar == 'tgz':
                        un_tar(dePath, filePath)
                    elif wrar == 'zip':
                        un_zip(dePath, filePath)
                    else:
                        un_rar(dePath, filePath)
                else:
                    continue
            break
    except Exception as e:
        result = "Except"
        traceback.print_exc()
        pass
    finally:
        return result

@catch_error
def checkWrar(fileName):
    if '.tar' in fileName:
        return 'tar'
    elif '.tgz' in fileName:
        return 'tgz'
    elif '.zip' in fileName:
        return 'zip'
    elif '.rar' in fileName:
        return 'rar'
    else:
        return 'fault'

def un_tar(filePath, tarPath):
    """ungz tar file"""
    try:
        t = tarfile.open(filePath)
        t.extractall(path = tarPath)            
    except Exception as e:
        traceback.print_exc()
        pass
    finally:
        t.close()

def un_zip(filePath, tarPath):
    """ungz zip file"""
    try:
        zip_file = zipfile.ZipFile(filePath)
        for file in zip_file.namelist():
            zip_file.extract(file, path=tarPath)    
    except Exception as e:
        traceback.print_exc()
        pass
    finally:
        zip_file.close()

def un_rar(filePath, tarPath):
    """ungz rar file"""
    try:
        rar = rarfile.RarFile(filePath)
        rar.extractall(path = tarPath)    
    except Exception as e:
        traceback.print_exc()
        pass
    finally:
        rar.close()
