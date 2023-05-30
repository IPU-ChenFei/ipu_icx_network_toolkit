#!/usr/bin/env python
#################################################################################
# INTEL CONFIDENTIAL
# Copyright Intel Corporation All Rights Reserved.
#
# The source code contained or described herein and all documents related to
# the source code ("Material") are owned by Intel Corporation or its suppliers
# or licensors. Title to the Material remains with Intel Corporation or its
# suppliers and licensors. The Material may contain trade secrets and proprietary
# and confidential information of Intel Corporation and its suppliers and
# licensors, and is protected by worldwide copyright and trade secret laws and
# treaty provisions. No part of the Material may be used, copied, reproduced,
# modified, published, uploaded, posted, transmitted, distributed, or disclosed
# in any way without Intel's prior express written permission.
#
# No license under any patent, copyright, trade secret or other intellectual
# property right is granted to or conferred upon you by disclosure or delivery
# of the Materials, either expressly, by implication, inducement, estoppel or
# otherwise. Any license under such intellectual property rights must be express
# and approved by Intel in writing.
#################################################################################
"""Module containing the abstract base class for subclass implementation guidelines.

    Typical usage example:
        The base class is meant to be inherited by subclass test cases.
"""
import os
import platform
import re
from argparse import Namespace, ArgumentParser
from logging import Logger
from typing import List
from xml.etree.ElementTree import Element, parse

import dtaf_core.lib.log_utils as log_utils
import dtaf_core.lib.registry as registry
from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.lib.private.autofill.capi import CAPIAutofill as CapiAuto
from dtaf_core.lib.test_context import TestContext


class BaseTestCase(metaclass=registry.AbstractMetaRegistry):
    """Contains base test case function definitions and test execution flow for all test content."""

    def __init__(self, log: Logger, args: Namespace, config: Element) -> None:
        """Initialize the BaseTestCase

        Args:
            log: logger to use for test logging.
            args: test case command line arguments.
            config: configuration options for test content.
        """
        self._log = log
        self._args = args
        self._cfg = config

    def prepare(self) -> None:
        """Method called when a test is initiated to perform setup and initialization tasks"""

    def execute(self) -> None:
        """Method with the main execution test logic - Perform the expected test steps"""

    def cleanup(self) -> None:
        """Clean-up method called when execution ends - Revert platform to a stable state if required"""

    @classmethod
    def add_arguments(cls, parser: ArgumentParser) -> None:
        """Add class arguments to command line argument parser.
            Sub-classes MUST call super.add_arguments(parser) or ensure config is overridden for required parameters.

        Args:
            parser: parser to add arguments to.
        """

    @classmethod
    def parse_arguments(cls, arg_source: list, cfg_file_default: str) -> Namespace:
        """Parse command line arguments from environment

        Args:
            arg_source: List of strings to pull arguments from. Will use sys.stdin if None.
            cfg_file_default: Path to the default configuration file (users can override if they so choose).

        Return:
            argparse.Namespace: Parsed arguments from sys.argv.
        """
        # Create ArgumentParser and add default arguments
        arg_parser = ArgumentParser()
        arg_parser.add_argument('--cfg_file', default=cfg_file_default, help="Path to the system's config file.")
        arg_parser.add_argument('--project_dir', help="Override config file path to project directory")
        arg_parser.add_argument('--console_debug', action="store_true", default=False,
                                help="Enable debug output to console.")
        arg_parser.add_argument('--reset_defaults', default=True,
                                help="Enable/Disable Loadbiosdefaults for a test")
        arg_parser.add_argument('--auto_gen_xml', type=bool, default=False,
                                help="Automatically generate DTAF Core XML file")
        arg_parser.add_argument('--inventory_type', default="", choices=["", "capi"],
                                help="supported inventory server type (see user guide of DTAF Core for the full list)")
        arg_parser.add_argument('--inventory_address', default="capi-lr40n07.gv.intel.com:5000",
                                help="the address of inventory")
        arg_parser.add_argument('--output_dir', default="",
                                help="the root of the output log. it will not work only if auto_gen_xml is True")
        arg_parser.add_argument("--target", default="", help="specify capi target to run the test case")
        arg_parser.add_argument("--token", help="use the cookie file to authenticate")
        arg_parser.add_argument('-o', '--outputpath', action="store", default="", help="Log dir for command center")

        # Add user-specified arguments
        cls.add_arguments(arg_parser)

        # Return parsed arguments in a Namespace object
        return arg_parser.parse_args(args=arg_source)

    @classmethod
    def run(cls, arg_source: List[str] = None) -> bool:
        """Main method for a test class. This runs all phases of the test (prepare, execute, cleanup)

        Args:
            arg_source: List of strings to pull args from.

        Return:
            bool: True if test evaluation passed, False otherwise.
        """
        # Assign the config file path based on the current OS
        exec_os = platform.system()
        try:
            cfg_file_default = Framework.CFG_FILE_PATH[exec_os]
        except KeyError:
            print("Error - execution OS " + str(exec_os) + " not supported!")
            raise RuntimeError("Error - execution OS " + str(exec_os) + " not supported!")

        # Parse command line arguments (if any)
        args = cls.parse_arguments(arg_source, cfg_file_default)
        if args.auto_gen_xml and args.target:
            inventory_address = args.inventory_address if args.inventory_address else r""
            if m := re.match(r"([^:]+):(\d+)", inventory_address):
                capi = CapiAuto(server_name=m.group(1), port=m.group(2), output_dir=args.output_dir, token=args.token)
                capi.auto_generate_config_xml(args.target)
                if capi.dtaf_config_xml: args.cfg_file = capi.dtaf_config_xml
        config = parse(os.path.expanduser(args.cfg_file)).getroot()
        if len(args.target) > 0:
            capi = CapiAuto(config, output_dir=args.output_dir, token=args.token)
            capi.set_target(target=args.target)
            capi.set_credential()
            capi.auto_fill_blank(args.target)
            config = capi.xml_root

        with TestContext():
            # Create a log file
            log = log_utils.create_logger(cls.__name__, args.console_debug, config)
            cls.log_dir = log_utils.get_log_file_dir(log)
            log.debug(f"Log directory: {cls.log_dir}")

            # Perform Test Init
            log.info("Executing test initialization...")
            try: test = cls(log, args, config)
            except Exception as e:
                log.exception(e)
                log_utils.create_cc_failure_results_json(cls.log_dir, [str(e)])
                log.info("Test Result = FAIL")
                return False

            # Perform Test
            log.info("Executing test preparation...")
            try: test.prepare()
            except Exception as p_ex:
                log.exception(p_ex)
                log.info("Test preparation failed. Running cleanup...")
                try: test.cleanup()
                except Exception as c_ex:
                    log.exception(c_ex)
                    log.info("Test cleanup failed.")
                    log_utils.create_cc_failure_results_json(cls.log_dir, [p_ex, c_ex])
                else: log_utils.create_cc_failure_results_json(cls.log_dir, [p_ex])
                finally:
                    log.info("Test Result = FAIL")
                    return False
            else:
                log.info("Test preparation complete. Executing test...")
                try: test.execute()
                except Exception as e_ex:
                    log.exception(e_ex)
                    log.info("Test execution failed. Running cleanup...")
                    test_result = False
                else:
                    log.info("Test execution complete. Running cleanup...")
                    test_result = True
                finally:
                    try: test.cleanup()
                    except Exception as c_ex:
                        log.exception(c_ex)
                        log.info("Test cleanup failed.")
                        if not test_result: log_utils.create_cc_failure_results_json(cls.log_dir, [e_ex, c_ex])
                    else:
                        if not test_result: log_utils.create_cc_failure_results_json(cls.log_dir, [e_ex])
                    finally:
                        log.info(f"Test Result = {'PASS' if test_result else 'FAIL'}")
                        return test_result
