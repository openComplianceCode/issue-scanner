# Software compliance information scanning

## API interface
GET/POST  https://127.0.0.1:8868/doSca?url={url}&asyn={asyn}&resp={resp}&para={para}

### Parameters
`url`: The url of the repo that needs to be scanned can be purl/url/package http download link     `string`      **must**

`asyn`: Whether to enable asynchronous scanning, default False   `boolean`      optional

`resp`: The url to receive the result   `string`      optional

`para`: Receive interface parameters   `string`      optional

### HTTP status code
```text
200: OK
500: Internal Server Error
```

### Result field description
```
repo_license_legal: repo-level license compliance information   string
spec_license_legal: spec file license compliance information  string
license_in_scope: file-level license compliance access information  string
repo_copyright_legal: repo-level copyright information  string
pass: pass or not   boolean
notice: statement of specific circumstances    string
is_legal: repo-level license compliance details  json 
license: repo-level license list   list
detail: Specific results of the three rules for repo-level licenses   json
is_standard: describe whether the license statement is clear  json
is_white: describe whether the license is allowed   json
is_review: describe whether the license requires review   json
risks: abnormal license list   list
blackReason: reasons why license is not allowed   string
copyright: repo-level copyright list   list
result_code: Return status code   string(Reserved field, temporarily useless)
```

### Sample
#### Request
GET/POST  http://127.0.0.1:8868/doSca?url=pkg:gitee/openharmony/test@OpenHarmony-v3.1-Release

#### Return
```json
{
    "repo_license_legal": {
        "pass": true,
        "result_code": "",
        "notice": "test/LICENSE",
        "is_legal": {
            "pass": true,
            "license": [
                "Public Domain"
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
        "pass": false,
        "result_code": "",
        "notice": "无spec文件",
        "detail": {}
    },
    "license_in_scope": {
        "pass": true,
        "result_code": "",
        "notice": "OSI/FSF认证License"
    },
    "repo_copyright_legal": {
        "pass": true,
        "result_code": "",
        "notice": "缺少项目级Copyright声明文件",
        "copyright": []
    }
}
```

---

[Back to Contents](../../README.md)
