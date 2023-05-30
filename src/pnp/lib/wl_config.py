#!/usr/bin/env python
##########################################################################
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
##########################################################################
import os
import pandas as pd
from sqlalchemy import create_engine
import six
if six.PY2:
    from pathlib import Path
if six.PY3:
    from pathlib2 import Path
import configparser
from src.pnp.lib.pnp_constants import ClusteringMode, Config, Filename

class TestcaseConfigs(object):
    """
    Class for managing PnP Testcase Configs
    """

    def __init__(self):
        """
        Create an instance for WL Config
        """

    def __get_pnp_config_path(self, wl_config_file_name):
        """
        This function returns the path of csv config files
        
        Args:
            wl_config_file_name: csv config file name of the workload
        
        Returns:
            Absolute path of the file
        """
        config_path_from_pnp_src = Path("config\\" + wl_config_file_name)
        pnp_path = Path(os.path.dirname(os.path.realpath(__file__))).parent
        pnp_config_path = os.path.join(pnp_path, config_path_from_pnp_src)
        return pnp_config_path

    def get_config_for_testcase(self, workload_config_file, tc_name):
        """
        This function returns config for a testcase

        :param tc_name: Name of the testcase

        :returns dictionary
        """
        config_file = self.__get_pnp_config_path(workload_config_file)
        
        engine = create_engine('sqlite://', echo=False)
        
        '''Return? if testcase not available in configs xl'''

        #Read given Excel sheet into a data frame
        df = pd.read_csv(config_file)
        
        #Convert data frame to sql by creating a table named configs
        df.to_sql('configs', engine, if_exists='replace', index=False)

        #Prepare and run query
        query = "select * from configs where " + Config.TEST_CASE + "='{}'".format(tc_name)
        result = engine.execute(query)

        final = pd.DataFrame(result,columns=df.columns)
        config = final.to_dict(orient='records')
        
        if not config:
            return {}

        return config[0]

    def get_configs_for_linked_testcases(self, workload_config_file, tc_name):
        """
        This function returns configs of linked testcases for the testcase

        :param tc_name: Name of the testcase

        :returns array of dictionaries
        """
        config_file = self.__get_pnp_config_path(workload_config_file)

        engine = create_engine('sqlite://', echo=False)
        
        #Read given Excel sheet int a data frame
        df = pd.read_csv(config_file)
        
        #Convert data frame to sql by creating a table named configs
        df.to_sql('configs', engine, if_exists='replace', index=False)

        #Prepare and run query
        query = "select * from configs where " + Config.PARENT_TEST_CASE + "='{}'".format(tc_name)
        result = engine.execute(query)

        final = pd.DataFrame(result,columns=df.columns)
        config = final.to_dict(orient='records')
        return config


class WorkloadConfig(object):
    """
    Class for managing PnP Workload Configs
    """
    def __init__(self, workload, clustering_mode):
        """
        Create an instance for WL Config
        """
        self.__workload = workload
        self.__workload_dir = None
        self.__workload_config_file = None
        self.__workload_bios_file = None
        self.__workload_branch = None
        self.__clustering_mode = clustering_mode
        self.__set_config_values()
        
    def __set_config_values(self):
        workload_config_file = self.__get_workload_config_file_path()

        config = configparser.ConfigParser()
        config.read(workload_config_file)

        if not self.__workload in config:
            raise Exception("There is no entry for the workload '{}' in {}" \
                             .format(self.__workload,Filename.WORKLOAD_CONFIG_FILE))
        
        if not Config.WORKLOAD_DIR in config[self.__workload]:
            raise Exception("WorkloadDir entry for the workload '{}' is not present in {}" \
                                .format(self.__workload,Filename.WORKLOAD_CONFIG_FILE))

        if not Config.CONFIG_FILE in config[self.__workload] \
           and not Config.CONFIG_FILE_QUAD in config[self.__workload] \
           and not Config.CONFIG_FILE_SNC4 in config[self.__workload]:
                raise Exception("ConfigFile entry for the workload '{}' is not present in {}" \
                                 .format(self.__workload,Filename.WORKLOAD_CONFIG_FILE))

        #Set WorkloadDir
        self.__workload_dir = config[self.__workload][Config.WORKLOAD_DIR]

        #Set ConfigFile
        if self.__workload == "mlc":
            if self.__clustering_mode == ClusteringMode.QUAD:
                self.__workload_config_file = config[self.__workload][Config.CONFIG_FILE_QUAD]
            elif self.__clustering_mode == ClusteringMode.SNC4:
                self.__workload_config_file = config[self.__workload][Config.CONFIG_FILE_SNC4]
            else:
                raise Exception("There is no config file for the Clustering Mode")
        else:
            self.__workload_config_file = config[self.__workload][Config.CONFIG_FILE]

        #Set BiosConfig
        if Config.BIOS_FILE in config[self.__workload]:
            pnp_folder_path = Path(os.path.dirname(os.path.realpath(__file__))).parent
            bios_file_path_from_pnp = Path("bios_config\\"+ config[self.__workload][Config.BIOS_FILE])
            self.__workload_bios_file = os.path.join(pnp_folder_path,bios_file_path_from_pnp)

        #Set Branch
        if Config.BRANCH in config[self.__workload]:
            self.__workload_branch = config[self.__workload][Config.BRANCH]

    def __get_workload_config_file_path(self):
        """
        This function returns the path of WORKLOAD_CONFIG_FILE
        """
        config_path_from_pnp_src = Path(Filename.WORKLOAD_CONFIG_FILE)
        pnp_path = Path(os.path.dirname(os.path.realpath(__file__))).parent
        pnp_config_path = os.path.join(pnp_path, config_path_from_pnp_src)
        return pnp_config_path

    def get_workload_dir(self):
        return self.__workload_dir

    def get_wokload_config_file(self):
        return self.__workload_config_file

    def get_wokload_bios_file(self):
        return self.__workload_bios_file

    def get_wokload_branch(self):
        return self.__workload_branch

    def get_workload_details(self):
        workload_details = {}

        if self.__workload_dir:
            workload_details[Config.WORKLOAD_DIR] = self.__workload_dir

        if self.__workload_config_file:
            workload_details[Config.CONFIG_FILE] = self.__workload_config_file

        if self.__workload_bios_file:
            workload_details[Config.BIOS_FILE] = self.__workload_bios_file

        if self.__workload_branch:
            workload_details[Config.BRANCH] = self.__workload_branch

        return workload_details

