# Query software compliance information

## API interface
GET/POST  http://127.0.0.1:8868/lic?purl=[{purl}]

### Parameters
`purl`: The purl of the repo that needs to be queried     `list`      **must**

### HTTP status code
```text
200: OK
500: Internal Server Error
```

### Result field description
```
purl: purl url   string
result: Query information results  json
repo_license: repo license list  list
repo_license_legal: repo compliance license list  list
repo_license_illegal: repo non-compliant license list   list
repo_copyright_legal: repo compliance copyright list    list(temporarily useless)
repo_copyright_illegal: repo non-compliant copyright list    list(temporarily useless)
is_sca: have you scanned   boolean
```

### Sample
#### Request
GET/POST  http://127.0.0.1:8868/lic?purl=["pkg:gitee/openharmony/test@OpenHarmony-v3.1-Release"]

#### Return
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

[Back to Contents](../../README.md)