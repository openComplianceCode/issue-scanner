FROM ubuntu:20.04
LABEL name="build issue scanner"
COPY sources.list /etc/apt/sources.list
RUN mkdir /home/issue-scanner \
    mkdir /home/giteeFile \
    && apt-get update \
    && apt-get install -y git \
    && git config --global http.postBuffer 1048576000 \
    && apt-get install -y python3 \
    && apt-get install -y python3-pip \
    && apt-get install -y cron \
    && apt-get install -y systemctl
COPY issue-scanner /home/issue-scanner
COPY root /var/spool/cron/crontabs/
RUN pip --default-timeout=100 install --index=https://pypi.tuna.tsinghua.edu.cn/simple/ -r /home/issue-scanner/requirements.txt
# 创建 myuser 用户
RUN groupadd -g 1002 myuser && \
    useradd -u 1002 -g 1002 -m -s /usr/sbin/nologin myuser\
    && chmod 777 /home
# 切换到 myuser 用户
USER myuser
CMD ["/bin/bash","-c","python3 /home/issue-scanner/src/main.py && systemctl start cron"]
