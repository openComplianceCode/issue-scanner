# Check PR compliance information

## API interface
GET/POST  https://127.0.0.1:8868/sca?prUrl={prUrl}

### Parameters
`prUrl`: PR url that needs to be scanned     `string`      **must**

### HTTP status code
```text
200: OK
500: Internal Server Error
```

### Result field description
```
repo_license_legal: repo-level license compliance information   string
spec_license_legal: spec file license compliance information  string
license_in_scope: File-level license compliance access information  string
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
GET/POST  https://127.0.0.1:8868/sca?prUrl=https://gitee.com/test/rpm/pulls/21

#### Return
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

[Back to Contents](../../README.md)