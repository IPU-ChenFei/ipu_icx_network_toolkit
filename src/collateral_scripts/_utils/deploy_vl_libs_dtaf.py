#!/usr/bin/env python

"""
Target Purpose: Copy all domain inband_lib to sutos path

Steps:
1> Go through all domain folders under /src
2> Check if domain_inband/domain_ofband package in /src/domain/lib
3> If exists, copy it to sutos path:
    Windows: C:\\BKCPkg
    Linux: /home/BKCPkg
    Esxi: /home/BKCPkg
"""

# Usage:
#       python deploy_vl_libs.py --domain=domain_name1,domian_name2 --target=ofband  : deploy appointed domain to host
#       python deploy_vl_libs.py --domain=domain_name1,domian_name2 --target=inband  : deploy appointed domain to sut
#       python deploy_vl_libs.py --domain=all --target=ofband                        : deploy all domain to host
#       python deploy_vl_libs.py --domain=all --target=inband                        : deploy all domain to sut

import argparse
import os
import shutil
import sys

path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.append(path)
# from src.lib.toolkit.infra.sut import get_default_sut
from dtaf_core.lib.tklib.infra.sut import get_default_sut

domain_pkg_list = os.listdir(os.path.join(path, "src"))


def deploy_inband_lib(sut, target, domain="ALL"):
    file_name = "domain_" + target

    if not os.path.exists(os.path.join(r"C:\\BKCPkg", file_name)):
        os.makedirs(os.path.join(r"C:\\BKCPkg", file_name))

    if domain == "all":
        for domain_pkg in domain_pkg_list:
            deploy(domain_pkg, sut, target)
    else:
        if "," in domain:
            for x in domain.split(","):
                deploy(x, sut, target)
        else:
            deploy(domain, sut, target)
    print("deploy comlpete")


def deploy(domain, sut, target):
    file_name = "domain_" + target
    if target == "ofband":

        domain_path = os.path.join(path, "src", domain, "lib")
        domain_inband_path = os.path.join(domain_path, file_name)
        if os.path.exists(domain_inband_path):
            for x in os.listdir(domain_inband_path):
                shutil.copy(os.path.join(domain_inband_path, x),
                            os.path.join(r"C:\\BKCPkg", file_name, x))
    else:
        domain_path = os.path.join(path, "src", domain, "lib")
        domain_inband_path = os.path.join(domain_path, file_name)
        if os.path.exists(domain_inband_path):
            for x in os.listdir(domain_inband_path):
                sut.upload_to_remote(os.path.join(domain_inband_path, x),
                                     os.path.join(sutos_path, file_name, x))


def get_parser():
    parser = argparse.ArgumentParser(description="deploy inband lib to sutos")
    parser.add_argument('--domain', type=str, required=False, default="all", help="domain name")
    parser.add_argument('--target', type=str, required=True, default="inband", help="work type")
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    sut = get_default_sut()
    if sut.default_os == "vmware":
        sutos_path = "/bkcvalidation"
    if sut.SUT_PLATFORM == "LINUX":
        sutos_path = "/home/bkcvalidation"
    else:
        sutos_path = r"C:\bkcvalidation"

    args = get_parser()
    deploy_inband_lib(sut, args.target, args.domain)
