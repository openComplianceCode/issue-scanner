# 查询软件仓合规信息

## API接口
GET/POST  http://127.0.0.1:8868/lic?purl=[{purl}]

### 路径参数
`purl`: 查询的repopurl地址     list      **必需**

### HTTP状态码
```text
200: OK
500: Internal Server Error
```

### 返回字段说明
```
purl: purl地址   string
result: 查询信息结果  json
repo_license: repo许可证列表  list
repo_license_legal: repo合规许可证列表  list
repo_license_illegal: repo不合规许可证列表   list
repo_copyright_legal: repo合规copyright列表    list(暂时无用)
repo_copyright_illegal: repo不合规copyright列表    list(暂时无用)
is_sca: 是否扫描过   boolean
```

### 样例
#### 请求
GET/POST  http://127.0.0.1:8868/lic?purl=["pkg:gitee/openharmony/test@OpenHarmony-v3.1-Release"]

#### 返回
```json
[
    {
        "purl": "pkg:gitee/openharmony/test@OpenHarmony-v3.1-Release",
        "result": {
            "repo_license": [
                "Public Domain"
            ],
            "repo_license_legal": [
                "Public Domain"
            ],
            "repo_license_illegal": [],
            "repo_copyright_legal": [],
            "repo_copyright_illegal": [],
            "is_sca": true
        }
    }
]
```

---

[返回目录](../../README.md)