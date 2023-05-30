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

import re

from .exceptions import GeneralException
from .LibException import ComponentException, LibException
from .Converter import Converter
from .utils import last_index, bin_operators_map
from .LibConfig import LibConfig


class ExpressionEngine:

    def __init__(self, component):
        self.component = component

    def create_expression(self, formula, allow_calculate=False):
        parts = list(filter(None, formula.split(" ")))
        parts = self.split_brackets(parts)
        symbols = ['(', ')', '?', ':']
        expression = []
        for part in parts:
            if part in list(bin_operators_map.keys()) or part in symbols:
                expression.append(part)
            else:
                expression.append(str(self.get_value_of_variable(part, allow_calculate)))
        formula_with_value = ' '.join(expression)
        return[formula, formula_with_value]

    def calculate_value(self, formula=None, parts=None, allow_calculate=False, allow_none_return=False):
        if parts is None:
            parts = list(filter(None, formula.split(" ")))

        if any('(' in s for s in parts) or any(')' in s for s in parts):
            return self.calculate_with_brackets(parts)
        elif parts.count(':') > 0 or parts.count('?') > 0:
            return self.calculate_with_ifs(parts, allow_calculate)

        if not parts:
            raise ComponentException("Invalid formula", self.component.name)
        elif len(parts) == 1:
            return self.get_value_of_variable(parts[0], allow_calculate, allow_none_return)
        else:
            return self.get_value_of_expression(parts, allow_calculate)

    def get_value_of_variable(self, variable: str, allow_calculate, allow_none_return=False):
        value = self.value_from_string(variable)
        if value is not None:
            return value
        if "\'" in variable:
            return variable.strip('\'')  # Remove '' for string comparision

        value = self.calculate_value_from_path(variable, allow_calculate)

        if value is None and not allow_none_return:
            raise ComponentException("Expression '{}' returns no value."
                                     .format(variable), self.component.name)
        return value

    def value_from_string(self, variable: str):
        if '{index}' in variable:
            variable = variable.replace('{index}', str(self.component.get_table_index()))
        if '{parent_index}' in variable:
            variable = variable.replace('{parent_index}', str(self.component.get_parent_table_index()))
        try:
            return Converter.string_to_bool(variable)
        except ValueError:
            pass
        try:
            return Converter.string_to_int(variable)
        except LibException:
            pass

    def get_value_of_expression(self, parts, allow_calculate):
        left = lambda idx: self.calculate_value(parts=parts[:idx], allow_calculate=allow_calculate)
        right = lambda idx: self.calculate_value(parts=parts[idx + 1:], allow_calculate=allow_calculate)
        i = None
        for oper, pair in bin_operators_map.items():
            try:
                if pair[1]:
                    i = last_index(parts, oper)
                else:
                    i = parts.index(oper)
            except ValueError:
                pass
            if i is not None:
                if oper == 'and':
                    return left(i) and right(i)
                elif oper == 'or':
                    return left(i) or right(i)
                elif oper == 'not':
                    return not right(i)
                return pair[0](left(i), right(i))

        raise ComponentException("Invalid calculation formula: '{}'"
                                 .format(" ".join(parts)), self.component.name)

    def split_brackets(self, temp_parts):
        parts = []
        for part in temp_parts:
            left_cnt = part.count('(')
            right_cnt = part.count(')')
            parts.extend(['('] * left_cnt)
            if right_cnt == 0:               # here we change '(value)' into '(', 'value', ')' [could be ((value)) etc.]
                parts.append(part[left_cnt:])   # we need to unhook number of '(' from left and ')' for right
            else:                               # there is exception if there is no ')' then we can't unhook from right
                parts.append(part[left_cnt:-1 * right_cnt])  # the raise of exception is lower in this method.
            parts.extend([')'] * right_cnt)
        if parts.count('(') != parts.count(')'):
            raise ComponentException("Invalid formula, number of '(' and ')' must be equal", self.component.name)
        parts = list(filter(None, parts))
        return parts

    def calculate_with_brackets(self, temp_parts):
        parts = self.split_brackets(temp_parts)
        while len(parts) > 0:
            # Here we are sure that number of '(' and ')' are equal, so if there is no ')'
            # we can calculate value of pure sentence
            if parts.count(')') > 0:
                close_idx = parts.index(')')
            else:
                return self.calculate_value(parts=parts)
            try:
                # but if there is ')' we need to find the closest '(' to the left of it:
                open_idx = len(parts[:close_idx]) - list(reversed(parts[:close_idx])).index('(') - 1
            except ValueError:
                raise ComponentException("Invalid formula, '(' must be before ')'", self.component.name)
            # and calculate sentence between them as a pure sentence, and replace it with a value
            val = self.calculate_value(parts=parts[open_idx + 1:close_idx])
            parts = parts[:open_idx] + parts[close_idx + 1:]
            parts.insert(open_idx, str(val))
            # we do it recursively until all brackets are calculated

    def calculate_with_ifs(self, parts, allow_calculate):
        try:
            question_mark_idx = parts.index("?")
            colon_idx = parts.index(":")
        except ValueError:
            raise ComponentException("Invalid formula, missing ':' / '?' operator required by '?' / ':'",
                                     self.component.name)
        if colon_idx < question_mark_idx:
            raise ComponentException("Invalid formula, ':' must be behind '?'", self.component.name)

        if self.calculate_value(parts=parts[:question_mark_idx]):
            return self.calculate_value(parts=parts[question_mark_idx + 1:colon_idx], allow_calculate=allow_calculate)
        else:
            return self.calculate_value(parts=parts[colon_idx + 1:], allow_calculate=allow_calculate)

    def calculate_component_from_path(self, formula: str):
        return self.calculate_value_from_path(formula.rsplit('.', 1)[0])

    def calculate_value_from_path(self, path, allow_calculate=False):
        parts = path.split(LibConfig.pathSeparator)

        component = self.component
        for (i, part) in enumerate(parts):
            if not part and i == 0:
                component = self.component.rootComponent
                continue
            elif part and LibConfig.isOrchestrator:
                component = self.component.rootComponent.get_child(part)
                continue

            if not part:
                raise ComponentException(f"Empty part at index {i} in path '{path}'", self.component.name)
            if i == (len(parts) - 1):
                subparts = part.rsplit(".", maxsplit=1)
            else:
                subparts = [part]

            if subparts[0] == "parent":
                component = component.parent
            elif subparts[0] != "this":
                brackets = re.search(r'(.*)\[(.*)\]', subparts[0])
                if brackets:
                    component = component.get_child(brackets[1])
                if "{index}" in subparts[0]:
                    index = self.component.get_table_index()
                    subparts[0] = subparts[0].replace("{index}", str(index))
                if "{parent_index}" in subparts[0]:
                    index = self.component.get_parent_table_index()
                    subparts[0] = subparts[0].replace("{parent_index}", str(index))
                # TableEntryComponent in calculate formula should be resolved only for decomposition purpose
                if component.component_type == 'TableEntryComponent' and component.is_decomposition_node:
                    component = component._find_table_entry(component.table, False)
                    if component is None:
                        return None
                component = component.get_child(subparts[0])

            if len(subparts) > 1:
                return component.get_property(subparts[1], allow_calculate)

        return component

    @staticmethod
    def get_logical_shift(value, formula):
        """Function is used to get information about how big was the logical shift on a value and to reverse this
         process"""
        m = re.search("(?<=>> )[^ ]*", formula)
        sign = '<<'
        if not m:
            sign = '>>'
            m = re.search("(?<=<< )[^ ]*", formula)
        if not m:
            raise GeneralException(f"Passed formula - {formula} is incorrect. Could not find logical shift sign.")
        result = int(m.group(0), 16)
        return value << result if sign == '<<' else value >> result
