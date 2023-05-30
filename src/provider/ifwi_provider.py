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

import os
import subprocess
import xml.etree.ElementTree as ET
from src.provider.base_provider import BaseProvider
from abc import ABCMeta, abstractmethod
from six import add_metaclass
import shutil
from importlib import import_module
from dtaf_core.lib.dtaf_constants import ProductFamilies
from src.lib import content_exceptions


@add_metaclass(ABCMeta)
class IfwiProfileProvider(BaseProvider):
    """
    This class is ifwi provider
    1. Modifies the binary file according to different boot profiles and return the path of the modified ifwi file.
    2. This class is inhertented the pfr provider class and non pfr provider class based on the parameter passed in the
    content configuration file.

    """
    FIT_BUILD_STR = "-b"
    FIT_INPUT_FILE_STR = "-f"
    FIT_OUTPUT_FILE_STR = "-o"
    FIT_SAVE_XML_STR = "-save"

    BOOT_GUARD_KEY = "name"
    BINARY_XML_SEARCH_STR = r'.//file/variable'
    BINARY_XML_ATTRIB_NAME = "name"
    BINARY_XML_ATTRIB_VALUE = "value"

    PATH = "path"
    NAME = "name"
    SPS_FIT_TOOL_PATH = None
    BINARY_IMAGE_PATH = None
    SPI_IMAGE = "spi_image.bin"

    DEFAULT_CONFIG_PATH = "common/ifwi"

    def __init__(self, log, cfg_opts, os_obj):
        """
        Create a new ifwi provider object.

        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment
        :param log: Logger object to use for output messages
        """
        super(IfwiProfileProvider, self).__init__(log, cfg_opts, os_obj)
        self._cfg = cfg_opts
        self._log = log

    @abstractmethod
    def create_ifwi_profile(self, common_obj, config_obj, profile):
        """
        Create Ifwi profile provider

        :param common_content_obj: common content object
        :param common_configuration_obj: common configuration object
        :param profile: boot profile which has to be build.
        :raise NotImplementedError
        """
        raise NotImplementedError

    @staticmethod
    def factory(log, cfg_opts, os_obj):
        """
        To create a factory object based on the configuration xml file.

        :return: object
        """
        pfr_class_name = "Pfr"
        profile_container = r"pfr_container"
        package = r"src.provider.{}_provider".format(cfg_opts.tag)
        provider_name_sections = cfg_opts.tag.split("_")
        provider_class_name = "".join(map(lambda x: x.capitalize(), provider_name_sections))
        pfr_check = cfg_opts.find(profile_container)

        if pfr_check.text == "True":
            mod_name = r"{}{}Provider".format(provider_class_name, pfr_class_name)
        else:
            mod_name = r"{}Non{}Provider".format(provider_class_name, pfr_class_name)
        mod = import_module(package, mod_name)
        aclass = getattr(mod, mod_name)
        return aclass(log=log, cfg_opts=cfg_opts, os_obj=os_obj)


class IfwiPfrProvider(IfwiProfileProvider):
    """
    Builds ifwi image from container folder to boot profile information passed in the configuration xml files.
    1. Modifies the builds xml file according boot profile.
    2. Rebuild the ifwi image by spsfit tool.
    """

    GENERATED_BIN = r"Binaries\spi_image.bin"
    UPDATE_CAPSULE_SIGNED = r"Binaries\UpdateCapsuleSigned.bin"
    PFM_SIGNED = r"PFM_signed.bin"
    BINARY_LIST = [GENERATED_BIN, UPDATE_CAPSULE_SIGNED, PFM_SIGNED]

    def __init__(self, log, cfg_opts, os_obj):
        """
        Create a new FitUtil object.

        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment
        :param log: Logger object to use for output messages
        """
        self._cfg = cfg_opts
        self._log = log
        super(IfwiPfrProvider, self).__init__(log, cfg_opts, os_obj)

    def create_ifwi_profile(self, common_obj, content_cfg, profile_parms):
        """
        This function modifies the binary image according to different boot profile and returns the modified image.

        :param common_obj: common utility obj.
        :param content_cfg: content configuration obj.
        :param profile_parms: IFWI parameters which needs to be modified.
        :return: Modified Binary image path.
        """
        self.common_obj = common_obj
        self.content_obj = content_cfg
        self.profile_parms = profile_parms
        self.pfr_container_folder, xml_file, build_file = self.content_obj.get_ifwi_container_params()
        binary_xml = os.path.join(self.pfr_container_folder, xml_file)
        self._modify_build_xml(binary_xml)
        cmd = ["python", build_file]
        return self._build_image(cmd)

    def _build_image(self, cmd):
        """
        Function builds binary image from the binary build file.

        :param cmd: build command.
        :return: True status of the binary build is successful.
        """

        os.chdir(self.pfr_container_folder)
        ret_value = False
        self._log.info("binary image build command {} ".format(cmd))
        # remove any previously generated bin files
        for i in self.BINARY_LIST:
            completpath = os.path.join(os.getcwd(), i)
            if os.path.exists(completpath):
                os.remove(completpath)

        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True, cwd=self.pfr_container_folder)
        self._log.debug("output {}" .format(output))
        for i in self.BINARY_LIST:
            completpath = os.path.join(os.getcwd(), i)
            if os.path.exists(i):
                self._log.debug("Generated SPI image path is {} " .format(completpath))
                ret_value = True
            else:
                self._log.error("unable to able to generate SPI image {}".format(cmd))
                raise RuntimeError("unable to able to generate SPI image {}".format(cmd))
        if ret_value:
            modified_binary = os.path.join(self.pfr_container_folder, self.GENERATED_BIN)
            self._log.info("Modified binary file {}".format(modified_binary))
            return modified_binary
        return ret_value

    def prepare_build(self, path):
        """
        Helper function to clean up previous build binary files.
        """
        if os.path.isdir(path):
            shutil.rmtree(path, ignore_errors=True)

    def _get_relative_path(self, filename):
        """
        Helper function to get  relative path.

        :return: relative path of the file name.
        """
        print("Container folder ", self.pfr_container_folder)
        os.chdir(os.path.dirname(self.pfr_container_folder))
        rel_path = os.path.relpath(
            self.common_obj.recursive_file_search(
                self.pfr_container_folder,
                filename),
            self.pfr_container_folder)
        self._log.info("relative path of {} is {} ".format(filename, rel_path))
        return rel_path

    def _modify_build_xml(self, binary_xml):
        """
        This function modifies the binary_Xml file which was generated from spsfittool to required boot configuration.

        :param binary_xml: Path of the xml file converted from binary ifwi.
        :return: None
        :raise RuntimeError: Raise runtimeerror if unable to modify binary xml file.
        """
        fit_cmd = self._get_build_xml_param()
        xml_flag = False
        self._log.debug("Fit xml cmd {} ".format(fit_cmd))
        with open(binary_xml, 'r') as f:
            tree = ET.parse(f)
        for config_key, config_value in fit_cmd.items():
            try:
                xml_src_str = r'.//' + config_key
                for node in tree.findall(xml_src_str):
                    node.set(self.BINARY_XML_ATTRIB_VALUE, config_value)
                    xml_flag = True
            except Exception:
                self._log.error("unable to modify the xml file {}".format(binary_xml))
                raise RuntimeError("unable to modify the xml file")

        if xml_flag:
            tree.write(binary_xml)
        else:
            self._log.error("No tag to modify in the binary {}".format(binary_xml))
            raise RuntimeError("No tag to modify in the binary")

    def _get_build_xml_param(self):
        """
        This function gets the corersponding value of xml key value from the dictonary.

        :return: dictonary of fit xml parameters.
        """
        cmd = {}
        build_xml_modifier = self.content_obj.get_ifwi_build_xml_modifier()
        for config_key, config_value in self.profile_parms.items():
            cmd[build_xml_modifier[config_key]] = config_value
        self._log.debug("fit xml modification {}".format(cmd))
        return cmd

class IfwiNonPfrProvider(IfwiProfileProvider):
    """
    Builds ifwi image from boot profile information passed in the configuration xml files by spsfit tool.
    1. converts ifwi image to xml , modifies xml and  rebuilds the ifwi image using spsfit tool.
    2. Rebuilds the ifwi image by using spsfit tool.
    """

    MOD_IMAGE = None
    profile_parms = None
    USE_XML_OPTIONS = [ProductFamilies.SKX,ProductFamilies.CLX]

    def __init__(self, log, cfg_opts, os_obj):
        """
        Create a new FitUtil object.

        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment
        :param log: Logger object to use for output messages
        """

        self._cfg = cfg_opts
        self._log = log
        super(IfwiNonPfrProvider, self).__init__(log, cfg_opts, os_obj)

    def create_ifwi_profile(self, common_obj, content_cfg, profile_parms):
        """
        This function modifies the binary image according to different boot profile and returns the modified image.

        :param common_obj: common utility obj.
        :param content_cfg: content configuration obj.
        :param profile_parms: IFWI parameters which needs to be modified are passed.
        :return: Modified Binary image path.
        """
        self.common_obj = common_obj
        self.content_obj = content_cfg
        self.profile_parms = profile_parms
        self._get_binary_config_params()
        self._get_modified_binary_path()
        self._log.debug("Platform information {} ".format(common_obj.get_platform_family()))
        if common_obj.get_platform_family() in self.USE_XML_OPTIONS:
            return self._modify_binary_by_xml()
        else:
            return self._modify_binary_by_fit()

    def _modify_binary_by_fit(self):
        """
        This function modifies the binary ifwi image using spsfittool inbuild command.

        :return: Path of the modified binary image.
        :raise: runtimeerror: raise runtime error if unable to modify ifwi binary file using spsfittool.
        """

        self._log.debug("Binary Modify Params {} ". format(self.profile_parms))
        fit_cmd = self._get_build_params()

        self._log.debug("Fit command {} " .format(fit_cmd))
        cmd = [self.SPS_FIT_TOOL_PATH, self.FIT_BUILD_STR]
        for i in fit_cmd:
            cmd.append(i)

        cmd = cmd + [self.FIT_INPUT_FILE_STR, self.BINARY_IMAGE_PATH, self.FIT_OUTPUT_FILE_STR, self.MOD_IMAGE]
        self._log.debug("build binary Command {}".format(cmd))
        subprocess.check_output(cmd)
        if os.path.exists(self.MOD_IMAGE):
            self._log.info("rebuild binary image from fit command is successful and path of newly build is  {} ".format(
                self.MOD_IMAGE))
            return self.MOD_IMAGE
        else:
            self._log.error("unable to rebuild image using fit commands".format(cmd))
            raise RuntimeError("unable to rebuild image using fit commands")

    def _modify_binary_by_xml(self):
        """
        Function modifies the ifwi binary into xml and modifies the binary

        :return: Modified path of image after rebuilding the binary image.
        """
        binary_xml = self._convert_binary_to_xml()
        self._modify_build_xml(binary_xml)
        return self._build_binary_from_xml(binary_xml)

    def _get_binary_config_params(self):
        """
        This function get Ifwi , spsFit tool information from the content configuration file.
        Sets the complete ifwi path and spsfit tool path

        :return: None
        :raise: Content Exception if IFWI file is not found in given location
        """

        self._spsfitc_path, self.FIT_SPS_TOOL = self.content_obj.get_spsfit_params()
        self._binary_path, self._binary_name = self.content_obj.get_ifwi_params()
        if not os.path.isfile(self._binary_path):
            raise content_exceptions.TestFail("IFWI file not found in location {}".format(self._binary_path))
        self._log.debug("Binary path {} " .format(self._binary_path))
        self._log.debug("Binary name {} " .format(self._binary_name))
        self.SPS_FIT_TOOL_PATH = self.common_obj.recursive_file_search(self._spsfitc_path, self.FIT_SPS_TOOL)
        self._log.debug("spsfit tool path {}".format(self.SPS_FIT_TOOL_PATH))
        self.BINARY_IMAGE_PATH = self.common_obj.recursive_file_search(self._binary_path, self._binary_name)
        self._log.debug("image path {} ".format(self.BINARY_IMAGE_PATH))

    def _get_modified_binary_path(self):
        """
        Function sets path of modified image which would be build.

        :return: None
        """
        self.MOD_IMAGE = os.path.join(
            os.path.dirname(
                self.BINARY_IMAGE_PATH),
            "mod_" +
            os.path.basename(
                self.BINARY_IMAGE_PATH))
        self._log.info("modified binary {}".format(self.MOD_IMAGE))

    def _get_build_params(self):
        """
        This function compares the build params passed by the user and returns corresponding build params in a list .

        :return: list of fit spstool command to ifwi.
        """
        cmd = []
        for config_key, config_value in self.profile_parms.items():
            cmd.append("-" + config_key)
            cmd.append(config_value)
        return cmd

    def _convert_binary_to_xml(self):
        """
        This function converts the binary image to Xml file.

        :return: returns the path of the xml file converted from binary ifwi.
        :raise: runtimeerror: Raise runtimeerror if unable to modify xml file.
        """

        binary_xml = os.path.join(os.path.dirname(self.BINARY_IMAGE_PATH), "output.xml")
        os.chdir(os.path.dirname(self.SPS_FIT_TOOL_PATH))
        cmd = [
            self.SPS_FIT_TOOL_PATH,
            self.FIT_INPUT_FILE_STR,
            self.BINARY_IMAGE_PATH,
            self.FIT_SAVE_XML_STR,
            binary_xml]
        self._log.debug("convert binary image cmd {} ".format(cmd))
        subprocess.check_output(cmd)
        if os.path.exists(binary_xml):
            self._log.debug("Binary file saved in XML format {} ".format(binary_xml))
            return binary_xml
        else:
            self._log.error("unable to save in XML format for modification ".format(binary_xml))
            raise RuntimeError("unable to save in XML format for modification would not able to mofidy binary file.")

    def _modify_build_xml(self, binary_xml):
        """
        This function modifies the binary_Xml file which was generated from spsfittool.

        :return: None
        :raise RuntimeError: Raise runtimeerror if unable to modify binary xml file.
        """
        xml_flag = False
        fit_cmd = self._get_build_xml_param()
        self._log.debug("Fit xml cmd {} ".format(fit_cmd))
        with open(binary_xml, 'r') as f:
            tree = ET.parse(f)
        for config_key, config_value in fit_cmd.items():
            try:
                for node in tree.findall(self.BINARY_XML_SEARCH_STR):
                    if node.get(self.BINARY_XML_ATTRIB_NAME) == config_key:
                        self._log.debug(
                            "Current XML key is  of {} and value is {}" .format(
                                node.get(
                                    self.BINARY_XML_ATTRIB_NAME), node.get(
                                    self.BINARY_XML_ATTRIB_VALUE)))
                        node.set(self.BINARY_XML_ATTRIB_VALUE, config_value)
                        xml_flag = True
            except Exception:
                self._log.error("unable to modify the xml file {}".format(binary_xml))
                raise RuntimeError("unable to modify the xml file")

        if xml_flag:
            tree.write(binary_xml)
        else:
            self._log.error("No tag to modify in the binary {}".format(binary_xml))
            raise RuntimeError("No tag to modify in the binary")

    def _build_binary_from_xml(self, binary_xml):
        """
        This function rebuilds the binary file from modified xml.

        :param binary_xml: Path of the xml file converted from binary ifwi.
        :return: path of the modified image file if successful.
        :raise: runtimeerror: if unable to build the binary image from the xml file.
        """

        os.chdir(os.path.dirname(self.SPS_FIT_TOOL_PATH))
        cmd = [
            self.SPS_FIT_TOOL_PATH,
            self.FIT_BUILD_STR,
            self.FIT_INPUT_FILE_STR,
            binary_xml,
            self.FIT_OUTPUT_FILE_STR,
            self.MOD_IMAGE]
        self._log.debug("cmd {} ".format(cmd))
        subprocess.check_output(cmd)
        if os.path.exists(self.MOD_IMAGE):
            self._log.info(
                "Build binary image from Xml file is successful path of the modified image is {} ".format(
                    self.MOD_IMAGE))
            return self.MOD_IMAGE
        else:
            self._log.error("unable to build image from xml ".format(binary_xml))
            raise RuntimeError("unable to build image from xml ")

    def _get_build_xml_param(self):
        """
        This function compares the build params passed by the user and returns corresponding build params in a dictonary.

        :return: dictonary of fit xml parameters.
        """
        cmd = {}
        build_xml_modifier = self.content_obj.get_ifwi_build_xml_modifier()
        for config_key, config_value in self.profile_parms.items():
            cmd[build_xml_modifier[config_key]] = config_value
        self._log.debug("fit xml modification {}".format(cmd))
        return cmd
