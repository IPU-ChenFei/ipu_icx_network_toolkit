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
import argparse


class OrchestratorCommandLineOptions:

    def __init__(self, app_name, input_args):
        self.app_name = app_name
        parser = argparse.ArgumentParser(app_name, epilog="")
        # positional arguments
        parser.add_argument('xmls', nargs='+', help='Xmls that describe current versions and capsule xml. Each next '
                                                    'xml will overwrite versions from the previous one. The last xml '
                                                    'provided should be the capsule xml - the one that specifies '
                                                    'versions that will be applied with the update.')

        # optional arguments
        parser.add_argument('--verbose', help='verbose output', action='store_true')
        args = parser.parse_args(args=input_args)

        self.xmls = args.xmls
        self.verbose = args.verbose