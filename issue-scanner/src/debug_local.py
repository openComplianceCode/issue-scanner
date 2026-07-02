# -*- coding: utf-8 -*-
"""本地断点调试入口，无需启动 Tornado 服务。"""
import argparse
import json
import os
import sys

from reposca.licenseCheck import LicenseCheck
from reposca.analyzeSca import getScaAnalyze, run_spec
from util.postOrdered import infixToPostfix


def debug_check(license_expr: str):
    lic_check = LicenseCheck("file", "indelic")
    result = lic_check.check_admittance(license_expr)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


def debug_spec(spec_path: str):
    licenses = run_spec(spec_path)
    lic_check = LicenseCheck("repo", "indelic")
    for item in licenses:
        tokens = infixToPostfix(item)
        result = lic_check.check_license_safe(tokens)
        print(f"spec license: {item}")
        print(json.dumps(result, ensure_ascii=False, indent=2))


def debug_analyze(sca_json_path: str, repo_src: str, scan_type: str = "inde"):
    with open(sca_json_path, "r", encoding="utf-8") as f:
        sca_json = f.read()
    result = getScaAnalyze(sca_json, repo_src, scan_type, "No", [])
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    return result


def main():
    parser = argparse.ArgumentParser(description="issue-scanner 本地调试")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_check = sub.add_parser("check", help="调试 /check 许可证准入逻辑")
    p_check.add_argument("license", help="许可证表达式，如 'Mulan PSL v2'")

    p_spec = sub.add_parser("spec", help="调试 spec 文件许可证解析")
    p_spec.add_argument("path", help=".spec 文件路径")

    p_analyze = sub.add_parser("analyze", help="调试 getScaAnalyze 分析逻辑")
    p_analyze.add_argument("sca_json", help="scancode 输出的 JSON 文件")
    p_analyze.add_argument("repo_src", help="仓库源码根目录")
    p_analyze.add_argument("--type", default="inde", choices=["inde", "ref"])

    args = parser.parse_args()

    if args.cmd == "check":
        debug_check(args.license)
    elif args.cmd == "spec":
        if not os.path.isfile(args.path):
            sys.exit(f"文件不存在: {args.path}")
        debug_spec(args.path)
    elif args.cmd == "analyze":
        if not os.path.isfile(args.sca_json):
            sys.exit(f"文件不存在: {args.sca_json}")
        debug_analyze(args.sca_json, args.repo_src, args.type)


if __name__ == "__main__":
    main()
