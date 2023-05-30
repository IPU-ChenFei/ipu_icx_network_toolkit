#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
INTEL CONFIDENTIAL
Copyright 2020 Intel Corporation.
This software and the related documents are Intel copyrighted materials, and
your use of them is governed by the express license under which they were
provided to you (License).Unless the License provides otherwise, you may not
use, modify, copy, publish, distribute, disclose or transmit this software or
the related documents without Intel's prior written permission.

This software and the related documents are provided as is, with no express or
implied warranties, other than those that are expressly stated in the License.
"""
import sys

from library.tool.ColorPrint import ColorPrint
from library.tool.LibConfig import LibConfig
from library.tool.utils import print_header, is_python_ver_satisfying
from orchestrator.OrcherstratorArgParser import OrchestratorCommandLineOptions
from orchestrator.OrchestratorEngine import OrchestratorEngine


def parse_args():
    name = 'Intel (R) Orchestrator'
    version = "1.0"
    print_header(name, version)
    if not is_python_ver_satisfying(required_python=(3, 6)):
        sys.exit(1)
    args = OrchestratorCommandLineOptions(name, sys.argv[1:])
    return args


def main():
    ColorPrint.setup_colorama()
    args = parse_args()
    capsule_xml = args.xmls[-1]
    settings_xmls = args.xmls[:-1]

    engine = OrchestratorEngine(args.verbose, capsule_xml, settings_xmls)
    engine.check_capsule()


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        ColorPrint.error("Error occurred: \n" + str(e))
        LibConfig.exitCode = 1
    sys.exit(LibConfig.exitCode)
