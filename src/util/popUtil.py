

def popKill(subPopen):
    try:
        if subPopen.stdin:
            subPopen.stdin.close()
        if subPopen.stdout:
            subPopen.stdout.close()
        if subPopen.stderr:
            subPopen.stderr.close()

        subPopen.kill()
    except OSError:
        pass