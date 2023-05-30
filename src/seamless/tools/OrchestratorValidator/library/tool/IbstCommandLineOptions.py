#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
INTEL CONFIDENTIAL
Copyright 2017-2020 Intel Corporation.
This software and the related documents are Intel copyrighted materials, and
your use of them is governed by the express license under which they were
provided to you (License).Unless the License provides otherwise, you may not
use, modify, copy, publish, distribute, disclose or transmit this software or
the related documents without Intel's prior written permission.

This software and the related documents are provided as is, with no express or
implied warranties, other than those that are expressly stated in the License.
"""
import argparse
from .utils import get_file_name_no_ext
from .LibConfig import LibConfig


class IbstHelpFormatter(argparse.RawDescriptionHelpFormatter):

    def _format_actions_usage(self, actions, groups):
        try:
            positional_index = next(i for i, action in enumerate(actions) if not action.option_strings)
        except StopIteration:
            positional_index = len(actions)
        # Add info about '--' only if there are some optional arguments in the list
        if positional_index > 0:
            new_action = argparse.Action(["--"], "")
            actions = actions[:positional_index] + [new_action] + actions[positional_index:]
        return super()._format_actions_usage(actions, groups)


class IbstCommandLineOptions:

    app_name = None
    input_file = None
    output_file = None
    config_override_file = None
    setting_overrides = []
    skip_validation = False
    example = None
    output_info = None
    output_map = None

    def __init__(self, app_name, app_dir, input_args):
        self.app_name = app_name
        self.app_dir = app_dir
        self.example = "Use '--' to indicate end of optional arguments.\n\n" \
            'examples:\n' \
            '   $ python3 {0} IE.xml \n' \
            '   $ python3 {0} OEMToken.xml -o OEMToken.bin\n' \
            '   $ python3 {0} IE.xml -o ie.bin -s ftpr_key=rsa_key.pem\n' \
            '   $ python3 {0} OEMToken.xml -o OEMToken.bin --skip_valid\n' \
            '   $ python3 {0} -s is_acm=1 binary=ACM.bin key=keys.pem -- CoSigningManifest.xml\n' \
            ''.format(self.app_name)

        parser = argparse.ArgumentParser(app_name,
                                         formatter_class=IbstHelpFormatter,
                                         epilog=self.example)
        # positional arguments
        parser.add_argument('input', help='configuration xml file')

        # optional arguments
        parser.add_argument('-o', '--output', help='output file (default: <input_name>.bin)')
        parser.add_argument('-v', '--version',
                            help='displays version information',
                            action='version',
                            version=' ')  # leave empty, version in header
        parser.add_argument('--config_override',
                            help='second configuration file with settings to be overriden',
                            nargs=1)
        parser.add_argument('-s', '--setting', help='override setting value', nargs='+',)
        parser.add_argument('--skip_valid', help='skip xml schema validation', action='store_true')
        parser.add_argument('--info', help=argparse.SUPPRESS)
        parser.add_argument('--map', help="output xml file with binary's map")
        parser.add_argument('--verbose', help="print additional information", action='store_true')
        args = parser.parse_args(args=input_args)

        self.input_file = args.input
        input_name = get_file_name_no_ext(self.input_file)
        if args.output is not None:
            IbstCommandLineOptions.output_file = args.output
        if args.info:
            self.output_info = args.info
        if args.map:
            self.output_map = args.map
        if args.config_override is not None:
            self.config_override_file = args.config_override[0]
        if args.setting is not None:
            self.setting_overrides = args.setting
        if args.verbose:
            LibConfig.isVerbose = True
        self.skip_validation = (args.skip_valid is not False)
