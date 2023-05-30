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
import re
import sys
from library.tool.BinaryGenerator import BinaryGenerator
from library.tool.ColorPrint import ColorPrint
from library.tool.LibConfig import LibConfig
from library.tool.components.AutoVersionComponent import AutoVersionComponent
from library.tool.components.ComponentFactory import ComponentFactory
from library.tool.components.IComponent import IComponent
from library.tool.components.RootComponent import RootComponent
from library.tool.components.VersionComponent import VersionComponent
from library.tool.SecureXmlParser import SecureXmlParser


class OrchestratorComponentFactory(ComponentFactory):

    def __init__(self):
        super().__init__()
        self._class_map['version'] = AutoVersionComponent


class OrchestratorEngine(object):
    '''
        OrchestratorEngine - core of the Orchestrator, cmd calls its methods
    '''

    def __init__(self, is_verbose, capsule_xml, xmls):
        LibConfig.settingsTag = LibConfig.configurationTag
        LibConfig.overridesTag = 'component_meta'
        LibConfig.rootTag = 'component_meta'
        LibConfig.layoutTag = 'dependencies'
        LibConfig.settingsTag = 'implements'
        LibConfig.allowEmptyConfiguration = True
        LibConfig.maxBufferSize = 100
        LibConfig.isOrchestrator = True
        LibConfig.isVerbose = is_verbose
        self.capsule_xml = capsule_xml
        self.xmls = xmls
        self.generator = None

    def check_capsule(self):
        self.generator = self.create_generator(self.capsule_xml)
        capsule_name, capsule_update_versions = self.parse_capsule_xml()
        self.parse_version_xmls()
        self.generator.parse_layout()
        self.simplify_generator_children()
        can_apply_capsule = self.evaluate_dependencies()
        if can_apply_capsule:
            ColorPrint.success(f"\n{capsule_name} approved.")
            ColorPrint.info("The capsule will update components as follows:")
            self.print_settings(self.generator, capsule_update_versions, print_method=ColorPrint.info)
        else:
            ColorPrint.error(f"\n{capsule_name} rejected.")
            sys.exit(1)

    @staticmethod
    def create_generator(xml):
        generator = BinaryGenerator(xml, SecureXmlParser.Schema.NoSchema, component_factory=OrchestratorComponentFactory)
        return generator

    def parse_capsule_xml(self):
        capsule_name = self.generator.xml_root.attrib["help_text"]
        self.generator.parse_configuration()
        capsule_update_versions = self.generator.configuration_root.semideepcopy()
        settings_node = self.generator.xml_root.find(LibConfig.settingsTag)
        settings_node.clear()
        ColorPrint.debug(f'\nValues after reading "{self.capsule_xml}"')
        self.print_settings(self.generator)
        return capsule_name, capsule_update_versions

    def parse_version_xmls(self):
        for xml in self.xmls:
            override_nodes = BinaryGenerator.get_override_nodes(xml)
            for configuration_node in override_nodes:
                for override_node in configuration_node:
                    self.generator.apply_nodes_override(override_node)
                    ColorPrint.debug(f'\nValues after reading "{xml}"')
                    self.print_settings(self.generator)

    def evaluate_dependencies(self):
        ColorPrint.debug("\nEvaluating dependencies:")
        return all(self.evaluate_single_rule(rule) for rule in self.generator.layout_root.children)

    def evaluate_single_rule(self, rule):
        self.generate_dynamic_children(rule, self.generator.root_component)
        is_dependency_met = rule.calculate_value(rule.value_formula)
        print_method = ColorPrint.debug if is_dependency_met else ColorPrint.error
        print_method(f'Evaluating rule: {rule.value_formula}')
        print_method(is_dependency_met)
        return is_dependency_met

    @staticmethod
    def print_settings(generator: BinaryGenerator, configuration=None, print_method=ColorPrint.debug):
        if not configuration:
            # if generator.root_component is not None, than changes in xml_tree would not be loaded. So there is a need
            # to set the root_component to None to load changes made by xmls overriding

            # in general, whole overriding logic should be more complex: orchestrator should print only what has changed
            # instead of printing whole list of settings. Since this is a temporary solution, it updates should not affect IBST code
            # that is why this is resolved on orchestrator side. Following two lines should not be necessary with next solution.
            if generator.root_component:
                generator.root_component = None
            generator.parse_configuration()
            configuration = generator.configuration_root
        for sett in configuration.children:
            print_method(f'{sett.name}={sett.get_value_string()}')

    # orchestator children are simplified
    # {IComponent.name: IComponent.value} instead of {IComponent.name: IComponent.instance}
    def simplify_generator_children(self):
        for child in self.generator.configuration_root.children:
            simplified = {child.name: child.comparison_value if isinstance(child, VersionComponent) else child.value}
            self.generator.root_component.children_by_name.update(simplified)

    # generate children that are defined inside rule like
    # <rule calculate="ME_RCV >= ver(4.4.3.29)"/>
    @staticmethod
    def generate_dynamic_children(rule: IComponent, root_comp: RootComponent):
        dynamic_ver_comp_regex = r"(ver\((.*?)\))"  # match 2 groups: whole "ver(4.4.3.29)" string and "4.4.3.29" value
        dynamic_def_and_value_tuples: (str, str) = re.findall(dynamic_ver_comp_regex, rule.value_formula)
        # create components with name = value and value = value for comparison
        dynamic_version_components = {x[1]: VersionComponent.convert_string_value_for_comparison(x[1]) for x in dynamic_def_and_value_tuples}
        root_comp.children_by_name.update(dynamic_version_components)
        for dynamio_def, value in dynamic_def_and_value_tuples:
            rule.value_formula = rule.value_formula.replace(dynamio_def, value)
