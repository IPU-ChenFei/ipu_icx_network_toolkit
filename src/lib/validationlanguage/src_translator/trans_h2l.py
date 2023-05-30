
from src.lib.validationlanguage.src_translator.translator import *
from src.lib.validationlanguage.src_translator.const import *
from src.lib.validationlanguage.src_translator.trans_utils import parse_arguments,get_platform_config_real_path
from src.lib.validationlanguage.src_translator.sys_variables import SystemVariables
import os
import argparse
import sys
import copy

class ResetToSentence(Sentence):
    def __init__(self, instance):
        assert (isinstance(instance, Sentence))
        super(ResetToSentence, self).__init__(instance.op, instance.templates)

    def translate(self, args_str, sys_var, escape=False):
        # type: (str, SystemVariables, bool) -> Translation

        trans = super(ResetToSentence, self).translate(args_str, sys_var, escape)
        env = trans.args[0]
        if self.op == OP_BOOT_TO and SystemVariables.OS.is_validate(env):
            sys_var.environment = SystemVariables.Environment.OS
            sys_var.os = env
        elif env == SystemVariables.Environment.UEFI_SHELL:
            sys_var.environment = SystemVariables.Environment.UEFI_SHELL
        elif (self.op == OP_RESET_TO or self.op == OP_BOOT_TO) and env == SystemVariables.Environment.OS:
            sys_var.environment = SystemVariables.Environment.OS
        else:
            assert(not 'Invalid parameters')

        return trans

class BootToSentence(ResetToSentence):
    def __init__(self, instance):
        assert (isinstance(instance, Sentence))
        super(BootToSentence, self).__init__(instance)
        self.step_support = False
        self.prepare_support = True


class SetFeatureSentence(Sentence):
    def __init__(self, feature_table):
        super(SetFeatureSentence, self).__init__(OP_SET_FEATURE)
        self.__feature_table = feature_table

    def get_new_args_str(self, args_str):
        args_list = self.get_args(args_str)

        new_args_str = ''
        for item in args_list:
            (name, value) = parse_assignment_line(item)
            l = self.__feature_table[(name, value)]
            for knob_name, knob_value in l:
                if len(new_args_str) == 0:
                    new_args_str = f'{knob_name}={knob_value}'
                else:
                    new_args_str += f', {knob_name}={knob_value}'
            Assert(len(new_args_str)>0,f'failed to find bios knob definition for {name} = {value}')
        return new_args_str

    def translate(self, args_str, sys_var, escape=False):
        # type: (str, SystemVariables, bool) -> Translation

        new_arg=self.get_new_args_str(args_str)
        low = f'{OP_SET_BIOS_KNOB}: {new_arg}'

        return Translation(self.op, [low])


class BasicHLSTranslator(VlTranslator):
    def __init__(self, transfile=default_pvl_mapping_file):
        super(BasicHLSTranslator, self).__init__(transfile)
        self.step = 0
        self.translators = {
            # op_name : sentence instance
        }
        for op, template in self.table_parser.h2l_table.items():
            assert(op not in self.translators.keys())
            self.translators[op] = Sentence(op, template)
        self.translators[OP_SET_FEATURE] = SetFeatureSentence(self.table_parser.feature_table)
        self.translators[OP_BOOT_TO] = BootToSentence(self.translators[OP_BOOT_TO])
        self.translators[OP_RESET_TO] = ResetToSentence(self.translators[OP_RESET_TO])
        self.translators[OP_EXECUTE_HOST_CMD] = CommandSentence(self.translators[OP_EXECUTE_HOST_CMD])
        self.translators[OP_EXECUTE_CMD] = CommandSentence(self.translators[OP_EXECUTE_CMD])
        self.translators[OP_ITP_CMD] = CommandSentence(self.translators[OP_ITP_CMD])
        self.var.in_prepare = True
        self.last_op = None
        self.msg_prefix = None
        self.line_no = None

    def translate(self, line):
        if len(line) == 0:
            trans = Translation(OP_EMPTY, [''])
        else:
            info = f'translating {self.msg_prefix}:{self.line_no}: [{line}]'
            trans = super(BasicHLSTranslator, self).translate(line)

            if trans is None:
                idx = line.strip().find(':')
                if idx > 0:
                    op = line.strip()[:idx]
                    if op not in self.translators.keys():
                        if self.is_low_level_step(op):
                            trans = Translation(op, None)

            if trans is None:
                info += '=> Comments Out'
                trans = Translation(OP_COMMENTS, [f'# ' + self.handle_unknown_line(line)])
            elif trans.output_lines is not None:
                info += '=> Translated'
            else:
                info += '=> Keep as low level steps'
                trans = Translation(OP_LOW_LEVEL, [line])
            print(info)

        multi_lls = [OP_BOOT_TO, OP_RESET_TO, OP_TCDB]
        if trans.op in multi_lls and self.last_op not in [OP_EMPTY, OP_COMMENTS]:
            trans.output_lines.insert(0, '')
        elif trans.op not in [OP_EMPTY] and self.last_op in multi_lls:
            trans.output_lines.insert(0, '')

        self.last_op = trans.op
        return trans

    def translate_assign_line(self, line):
        ret = parse_assignment_line(line)
        if ret is None:
            return None

        name, value = ret
        ret = self.sys_var_check_set(name, value)
        if ret:
            return [f'{name} = "{value}"']
        else:
            # TODO: support user define variables
            return None

    @staticmethod
    def get_indent(line):
        indent = ''
        for i in range(0, len(line)):
            if line[i] == ' ':
                indent += ' '
        return indent

    def translate_lines(self, lines, msg_prefix=''):
        outlines = []

        self.last_op = None
        self.msg_prefix = msg_prefix
        for i in range(0, len(lines)):
            line = lines[i].strip()
            self.line_no = i
            trans = self.translate(line)
            # add indent back
            #trans.add_prefix(self.get_indent(lines[i]))
            outlines.extend(trans.output_lines)
        return outlines


def get_tcdb_file_path(block):
    path = os.path.join(os.getcwd(), 'TcdBlocks', block + '.tcdb')
    if os.path.exists(path):
        return path

    path = os.path.join(os.path.split(os.path.realpath(__file__))[0], '..', 'TcdBlocks', block + '.tcdb')
    if os.path.exists(path):
        return path
    return None


class RunTCDSentence(Sentence):
    PARAM_LIB='<lib>'
    PARAM_REPEAT_NUM='<repeat>'
    def __init__(self, transfile):
        super(RunTCDSentence, self).__init__(OP_TCDB, None)
        self.translator = BasicHLSTranslator(transfile)

    def translate(self, args_str, sys_var, escape=False):
        self.translator.var = sys_var
        args_list = self.get_args(args_str)
        tcdb_name = None
        repeat_num = 1
        if len(args_list) == 1:
            args = parse_args([self.PARAM_LIB], args_list)
            tcdb_name = args[self.PARAM_LIB]
        elif len(args_list) == 2:
            args = parse_args([self.PARAM_LIB, self.PARAM_REPEAT_NUM], args_list)
            tcdb_name = args[self.PARAM_LIB]
            repeat_num = args[self.PARAM_REPEAT_NUM]
        else:
            args = None
        Assert(args is not None, f'Wrong parameter input for {self.op} got {args_str}')

        num = int(repeat_num)
        Assert(num >=1, f'Wrong Repeat number, shall >=1 got {num}')
        indent = ''
        f = open(get_tcdb_file_path(tcdb_name), 'r')
        lines = f.readlines()
        f.close()

        tcdb_lines = self.translator.translate_lines(lines, msg_prefix=f'{tcdb_name}')
        if len(tcdb_lines) == 0:
            return Translation(OP_TCDB, [f'#skip empty TCDB {tcdb_name}'])

        output_lines = [
            # f'',
            f'### Call TCDB {tcdb_name} Start'
        ]

        if num > 1:
            output_lines.append(f'Repeat: {num}')
            indent = '    '

        for line in tcdb_lines:
            output_lines.append(indent + line)
        if num > 1:
            output_lines.append(f'End:')
        output_lines.append(f'### Call TCDB {tcdb_name} End')
        output_lines.append(f'')
        return Translation(OP_TCDB, output_lines)



class HlsTranslator(BasicHLSTranslator):
    SUT_ENV_OS = 'OS'
    SUT_UEFI_SHELL = 'UEFI SHELL'
    SUT_BIOS_MENU = 'BIOS MENU'

    PRE_ONLY_OPS=['Boot to']

    def __init__(self, transfile=default_pvl_mapping_file):
        super(HlsTranslator, self).__init__(transfile)
        self.translators[OP_TCDB] = RunTCDSentence(transfile)


    def translate_file(self, inputfile, outputfile='out.txt'):
        f = open(inputfile, 'r')
        lines = f.readlines()
        f.close()

        filename = os.path.basename(inputfile)
        print('===== High Level Step Translation Start =====')
        outlines = self.translate_lines(lines, filename)
        print('===== High Level Step Translation End   =====')
        outlines.insert(0, f'# Tool Version [{VERSION}]')
        out_f = open(outputfile, 'w')
        out_f.writelines([line + '\n' for line in outlines])
        out_f.close()

    def test(self):
        lines = [
            'Set Feature: VTd, Enable',
            'Boot to: OS',
            'Execute Command: python --help',
            'Execute Command: python -c "print(1+1)", 20'
        ]
        for l in lines:
            print(self.translate(l))
