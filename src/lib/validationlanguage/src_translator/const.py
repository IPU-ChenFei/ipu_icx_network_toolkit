VERSION='0.2.14'

feature_def_tab='Features'
bios_menu_knob_tab='BiosMenu'

bios_knob_config_module = 'plat_feature_config'
bios_menu_root = 'EDKII Menu'

default_pvl_mapping_file='pvl.xlsx'
defalut_bios_knobs_file='BiosKnobs.xml'

OP_TCDB = 'Run TCD Block'
OP_BOOT_TO = 'Boot to'
OP_RESET_TO = 'Reset to'
OP_SET_FEATURE = 'Set Feature'
OP_REPEAT = 'Repeat'
OP_END='End'
OP_SET_BIOS_KNOB = 'Set BIOS knob'
OP_STEP = 'STEP'
OP_PREPARE = 'PREPARE'
OP_LOG = 'Log'
OP_EXECUTE_CMD = 'Execute Command'
OP_EXECUTE_HOST_CMD = 'Execute Host Command'
OP_ITP_CMD = 'Execute ITP Command'
OP_WAIT = 'Wait'
OP_DC = 'Switch DC'
OP_AC = 'Switch AC'
OP_CHECK_ENVIRONMENT = 'Check Environment'
OP_CHECK_POWER_STATE = 'Check Power State'
OP_WAIT_FOR = 'Wait for'
OP_RESET = 'Reset'

OP_LOW_LEVEL = 1
OP_EMPTY = 2
OP_COMMENTS = 3
OP_ASSIGNMENT = 4


def Assert(condition, msg):
    if not condition:
        print('ERROR:' + msg)
        raise Exception(msg)