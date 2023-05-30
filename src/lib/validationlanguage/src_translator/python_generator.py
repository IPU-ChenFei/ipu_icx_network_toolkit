from src.lib.validationlanguage.src_translator.sys_variables import SystemVariables
from src.lib.validationlanguage.src_translator.const import Assert

def get_bios_menu_knob_var_name(id):
    return f'menu_knob_{id.lower()}'

def get_or_items(args):
    code = f'{args[0]}'
    for i in range(1, len(args)):
        code = f'{code} or {args[i]}'
    return code

def get_and_items(args):
    code = f'{args[0]}'
    for i in range(1, len(args)):
        code = f'{code} and {args[i]}'
    return code

def python_indent(codelines, indent_level):
    output = []
    if indent_level == 0:
        return codelines
    elif indent_level > 0:
        indent = ''
        for i in range(0, indent_level):
            indent = indent + '    '
        for line in codelines:
            output.append(indent+line)
    else:
        raise NotImplemented
    return output


def python_knob_menu_knob(id, name, path):
    var = get_bios_menu_knob_var_name(id)
    path_str = f'"{path[0]}"'
    for i in range(1, len(path)):
        path_str += f', "{path[i]}"'
    code = [
        f'{var} = BIOS_KNOB_SERIAL(',
        f'  name="{name}",',
        f'  path=["EDKII Menu", {path_str}]',
        ')'
    ]
    return code

def body_valid_lines(body):
    count = len(body)
    for line in body:
        if line.startswith('#') or len(line) == 0:
            count -= 1
    return count

def python_if(condition, body_true, body_false=None):
    code = [f'if {condition}:']
    if body_valid_lines(body_true) == 0:
        code.append('    pass')
    for line in body_true:
        code.append('    '+line)
    if body_false is not None:
        code.append('else:')
        if body_valid_lines(body_false) == 0:
            code.append('    pass')
        for line in body_false:
            code.append('    ' + line)
    #code.append('')
    return code

def python_reset_to(current_env, to_env):
    assert (SystemVariables.Environment.is_validate(current_env))
    Assert(SystemVariables.Environment.is_validate(to_env), f'{to_env} is not valid for Reset to')
    code = None
    if current_env == SystemVariables.Environment.OS:
        if to_env == SystemVariables.Environment.OS:
            code = ['sutos.reset_cycle_step(sut)']
        elif to_env == SystemVariables.Environment.UEFI_SHELL:
            code = ['sutos.reset_to_uefi_shell(sut)']
        elif to_env == SystemVariables.Environment.BIOS_MENU:
            code = ['sutos.reset_to_bios_menu(sut)']
    elif current_env == SystemVariables.Environment.UEFI_SHELL:
        if to_env == SystemVariables.Environment.BIOS_MENU:
            code = ['UefiShell.reset_to_bios_menu(sut)']
        elif to_env == SystemVariables.Environment.UEFI_SHELL:
            code = ['UefiShell.reset_cycle_step(sut)']
        elif to_env == SystemVariables.Environment.OS:
            code = ['UefiShell.reset_to_os(sut)']
    elif current_env == SystemVariables.Environment.BIOS_MENU:
        if to_env == SystemVariables.Environment.BIOS_MENU:
            code = ['BIOS_Menu.reset_cycle_step(sut)']
        elif to_env == SystemVariables.Environment.UEFI_SHELL:
            code = ['BIOS_Menu.reset_to_uefi(sut)']
        elif to_env == SystemVariables.Environment.OS:
            code = ['BIOS_Menu.reset_to_os(sut)']

    return code


def python_enter(current_env, to_env):
    assert (SystemVariables.Environment.is_validate(current_env))
    Assert(SystemVariables.Environment.is_validate(to_env), f'{to_env} is not valid for enter')
    if current_env == to_env:
        return []
    if current_env == SystemVariables.Environment.OS:
        return python_reset_to(current_env, to_env)
    elif current_env == SystemVariables.Environment.UEFI_SHELL:
        if to_env == SystemVariables.Environment.BIOS_MENU:
            return ['UefiShell.exit_to_bios_menu(sut)']
        elif to_env == SystemVariables.Environment.OS:
            return ['UefiShell.exit_to_bios_menu(sut)',
                    'BIOS_Menu.continue_to_os(sut)']
    elif current_env == SystemVariables.Environment.BIOS_MENU:
        if to_env == SystemVariables.Environment.UEFI_SHELL:
            return ['BIOS_Menu.enter_uefi_shell(sut)']
        elif to_env == SystemVariables.Environment.OS:
            return ['BIOS_Menu.continue_to_os(sut)']
    assert(not 'shall not access here')
    return None

