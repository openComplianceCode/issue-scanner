## Run

* 一、Pull dependency
    ```
    pip install issue-scanner/requirements.txt
    ```
* 二、Set up system environment
    ```
    env:
        - name: MYSQL_HOST
          value: your_db_host
        - name: MYSQL_USER
          value: your_db_name
        - name: MYSQL_PASSWORD
          valueFrom:your_db_password
        - name: MYSQL_DB_NAME
          value: your_db_name
        - name: MYSQL_PORT
          value: your_db_port
        - name: GITE_REDIRECT_URI
          value: your_gitee_api_token_redirect_uri
        - name: GITEE_CLIENT_ID
          value: your_gitee_api_token_client_id
        - name: GITEE_CLIENT_SECRET
          value: your_gitee_api_token_client_secret
        - name: GITEE_USER
          value: your_gitee_user
        - name: GITEE_PASS
          value: your_gitee_password
    ```
* 三、Run
    
    以服务形式
    ```
    python issue-scanner/src/main.py
    ```
    以指令行形式
    ```
    python issue-scanner/src/command.py -m pr/repo input
    ```
  
---

[返回目录](../../README.md)