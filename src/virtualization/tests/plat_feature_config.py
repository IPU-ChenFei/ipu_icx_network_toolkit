# Tool Version [0.2.11]
# this is generated code from validation language mapping table (pvl.xlsx)
# knobs for bios setup menu only in "BiosMenu" tab
# Time Stamp: 20220712Z09h14m49s

from src.lib.toolkit.infra.bios.bios import BIOS_KNOB_SERIAL


menu_knob_secureboot = BIOS_KNOB_SERIAL(
  name="SecureBootMode",
  path=["EDKII Menu", "Secure Boot Configuration"]
)

menu_knob_rtcwakeups4s5 = BIOS_KNOB_SERIAL(
  name="RTC Wake system from S4/S5",
  path=["EDKII Menu", "Platform Configuration", "Miscellaneous Configuration"]
)

