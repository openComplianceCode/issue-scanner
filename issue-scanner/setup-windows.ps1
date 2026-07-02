# Windows + Python 3.12 一键创建虚拟环境
# 在 issue-scanner 目录下执行: .\setup-windows.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

if (-not (Test-Path ".venv")) {
    python -m venv .venv
}

$pip = ".\.venv\Scripts\pip.exe"
$scancode = ".\.venv\Scripts\scancode.exe"

& $pip install --upgrade pip wheel
& $pip install "click==8.1.7" "setuptools>=69,<81" "packaging==21.3"

# 先装 scancode 核心（跳过 Windows 上难编译的依赖）
& $pip install "scancode-toolkit==31.0.1" --no-deps
& $pip install "boolean.py" "chardet" "commoncode==31.0.0b4" "container-inspector==32.0.1" `
    "debian-inspector" "dparse2" "fasteners" "ftfy" "gemfileparser" "html5lib" `
    "importlib-metadata" "intbitset" "jaraco.functools" "javaproperties" "jinja2" `
    "jsonstreams" "license-expression" "lxml" "MarkupSafe" "packageurl-python" `
    "parameter-expansion-patched" "pdfminer.six==20221105" "pefile" "pkginfo2" `
    "pip-requirements-parser" "pluggy" "plugincode==31.0.0b1" "publicsuffix2" `
    "pyahocorasick" "pygmars" "pygments" "pymaven-patch" "spdx-tools==0.7.0a3" `
    "toml" "urlpy" "xmltodict" "typecode" "extractcode==31.0.0" "dockerfile_parse" `
    "extractcode-7z" "extractcode-libarchive" "six" "cryptography" "ply" "rdflib" "banal"
& $pip install "fingerprints==0.6.6" --no-deps
& $pip install "normality==2.5.0" --no-deps
& $pip install "typecode-libmagic==5.39.210531"

# 应用依赖（跳过 scipy，Py3.12 不支持 1.7.1）
& $pip install "tornado==6.1" "PyMySQL==0.9.3" "PyYAML==6.0" "requests==2.26.0" `
    "urllib3==1.26.18" "charset-normalizer==2.0.12" "SQLAlchemy==1.3.24" `
    "tqdm==4.62.3" "GitPython==3.1.27" "DBUtils==1.3" "APScheduler==3.10.1" `
    "jsonpath==0.82" "rarfile==4.0" "attrs==22.1.0" "python-rpm-spec==0.11" `
    "beautifulsoup4==4.11.1" "click==8.1.7"

Write-Host ""
Write-Host "验证 scancode ..."
& $scancode --version
Write-Host ""
Write-Host "完成。激活环境: .\.venv\Scripts\Activate.ps1"
Write-Host "启动服务:     .\run.ps1"
