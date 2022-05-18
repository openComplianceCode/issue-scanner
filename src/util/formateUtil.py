

from util.catchUtil import catch_error


@catch_error
def formateUrl(urlData):
    return urlData.replace("\\", "/")