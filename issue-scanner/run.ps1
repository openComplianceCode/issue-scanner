# 使用项目虚拟环境启动 issue-scanner 服务
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvPython = Join-Path $Root ".venv\Scripts\python.exe"
$SrcDir = Join-Path $Root "src"

if (-not (Test-Path $VenvPython)) {
    Write-Error "未找到虚拟环境，请先执行: python -m venv .venv && pip install -r requirements-windows.txt"
}

Set-Location $SrcDir
& $VenvPython main.py
