# 检查PR合规信息

## API接口
GET/POST  https://127.0.0.1:8868/sca?prUrl={prUrl}

### 路径参数
`prUrl`: 扫描的PR链接     string      **必需**

### HTTP状态码
```text
200: OK
500: Internal Server Error
```

### 返回字段说明
```
repo_license_legal: repo级许可证合规信息   string
spec_license_legal: spec文件许可证合规信息  string
license_in_scope: 文件级许可证合规准入信息  string
repo_copyright_legal: repo级copyright信息  string
pass: 是否通过   boolean
notice: 具体情况声明    string
is_legal: repo级许可证合规具体信息  json 
license: repo级许可证列表   list
detail: repo级许可证三个规则具体结果   json
is_standard: license是否声明清晰  json
is_white: license是否准入   json
is_review: license是否需要审查   json
risks: 不通过license列表   list
blackReason: license不准入理由   string
copyright: repo级的copyright列表   list
result_code: 放回状态码   string(预留字段,暂时无用)
```

### 样例
#### 请求
GET/POST  https://127.0.0.1:8868/sca?prUrl=https://gitee.com/test/rpm/pulls/21

#### 返回
```json
{
    "repo_license_legal": {
        "pass": true,
        "result_code": "",
        "notice": "rpm/rpm.spec",
        "is_legal": {
            "pass": true,
            "license": [
                "GPLv2+"
            ],
            "notice": "通过",
            "detail": {
                "is_standard": {
                    "pass": true,
                    "risks": []
                },
                "is_white": {
                    "pass": true,
                    "risks": [],
                    "blackReason": ""
                },
                "is_review": {
                    "pass": true,
                    "risks": []
                }
            }
        }
    },
    "spec_license_legal": {
        "pass": true,
        "result_code": "",
        "notice": "通过",
        "detail": {
            "is_standard": {
                "pass": true,
                "risks": []
            },
            "is_white": {
                "pass": true,
                "risks": [],
                "blackReason": ""
            },
            "is_review": {
                "pass": true,
                "risks": []
            }
        }
    },
    "license_in_scope": {
        "pass": true,
        "result_code": "",
        "notice": "OSI/FSF认证的License"
    },
    "repo_copyright_legal": {
        "pass": true,
        "result_code": "",
        "notice": "(rpm/COPYRIGHT)",
        "copyright": [
            "Copyright (c) 2000,2001,2002,2003,2004 Eric Gerbier"
        ]
    }
}
```

---

[返回目录](../../README.md)