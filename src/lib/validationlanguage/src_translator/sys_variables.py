class SystemVariableDef(object):
    @classmethod
    def get_members(cls):
        list = []
        for member in dir(cls):
            if not callable(getattr(cls, member)) and not member.startswith("__"):
                attr = getattr(cls, member)
                list.append(attr)
        return list

    @classmethod
    def is_validate(cls, value):
        return value in cls.get_members()

class SystemVariables(SystemVariableDef):
    class Environment(SystemVariableDef):
        UNKNOWN = None
        OS = 'OS'
        UEFI_SHELL = 'UEFI SHELL'
        BIOS_MENU = 'BIOS Menu'

    class ItpLib(SystemVariableDef):
        PYTHONSV = 'pythonsv'
        CSCRIPT = 'cscript'

    class OS(SystemVariableDef):
        LINUX = 'Linux'
        WINDOWS = 'Windows'
        VMWARE = 'ESXi'
        UNKOWN = None

    def __init__(self):
        self.environment = self.Environment.OS
        self.itplib = self.ItpLib.PYTHONSV
        self.os = self.OS.UNKOWN
        self.in_prepare = True
        self.check_stage = False

    @classmethod
    def get_variables(cls):
        list = []
        for (name, value) in cls.__dict__.items():
            if name.startswith("__"):
                continue
            if isinstance(value, type(object)):
                list.append(name)

        return list

    @classmethod
    def is_sys_var(cls, var):
        return var in cls.get_variables()

    def verify_value(self, name, value):
        assert(self.is_sys_var(name))

    def set(self, name, value):
        assert(self.is_sys_var(name))
        value = value.strip('"')
        value = value.strip('\'')
        var_name = name.lower()
        var_type = getattr(type(self), name)
        if var_type.is_validate(value):
            assert(hasattr(self, var_name))
            setattr(self, var_name, value)
            return True
        else:
            return False
        #setattr(var_name, )


if __name__ == '__main__':
    var = SystemVariables()
    print(SystemVariables.Environment.get_members())
    print(SystemVariables.OS.get_members())
    print(var.set('Environment', SystemVariables.Environment.OS))
    print(var.environment)
    print(var.set('Environment', 'NA'))
    print(var.environment)
    #print(SystemVariables.get_variables())