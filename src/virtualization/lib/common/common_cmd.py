VM_CONNECT_PY = "python vm_connect.py "


def answer_cmd(method, cmd, extra_args=" "):
    # type: (str,list,str) -> str
    cmd_str = "{} -m \"{}\" ".format(VM_CONNECT_PY, method)
    cmd_str = cmd_str + extra_args + " "
    for c in cmd:
        cmd_str += "-acmd \"{}\" ".format(c)
    return cmd_str


def static_cmd(method, cmd, extra_args=" "):
    # type: (str,list,str) -> str
    cmd_str = "{} -m \"{}\" ".format(VM_CONNECT_PY, method)
    cmd_str = cmd_str + extra_args + " "
    for c in cmd:
        cmd_str += "-cmd \"{}\" ".format(c)
    return cmd_str


if __name__ == '__main__':
    l = ["]# & ifconfig", "]# & exit()"]
    answer_cmd("qemu", l)
    l = "ifconfig[10]", "pwd"
    cmds = static_cmd("console", ["ifconfig[10]", "pwd"], "-ip \"VM_IP\" ")
    print(cmds)
