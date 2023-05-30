#!/usr/bin/env python
import os
import time
import serial
import binascii
import platform
import threading
import logging as logger
from tkinter import *
from tkinter import ttk, filedialog
from tkinter.scrolledtext import ScrolledText
from serial import Serial
from serial import SerialException, SerialTimeoutException


CURENT_PATH = os.path.dirname(os.path.realpath(__file__))
IS_WINDOWS_OS = True if platform.system().lower() == "windows" else False
if IS_WINDOWS_OS:
    serial_port = r'COM100'
    sw_port = r'COM101'
    SERIAL_LOG_PATH = os.path.join(CURENT_PATH, "serial.log")
else:
    serial_port = r'/dev/ttyUSB100'
    sw_port = r'/dev/ttyUSB101'
sw_baud = 115200


class SoundWaveError(BaseException):
    pass


class InputError(BaseException):
    pass


class SoundWave(object):

    __SERIAL_CODE_REBOOT = '5503000058'

    __SERIAL_CODE_AC_ON = '550302015b'
    __SERIAL_CODE_AC_OFF = '550302025c'

    __SERIAL_CODE_USB_TO_PORTA = '550301015a'
    __SERIAL_CODE_USB_TO_PORTB = '550301025b'
    __SERIAL_CODE_USB_TO_OPEN = '550301035c'

    __SERIAL_CODE_GET_HARDWARE_VERSION = '55000055'
    __SERIAL_CODE_GET_SOFTWARE_VERSION = '55000156'
    __SERIAL_CODE_GET_CUSTOMER_MESSAGE = '55000358'

    __SERIAL_CODE_PRESS_POWER_BUTTON = '55070f0d0179'
    __SERIAL_CODE_RELEASE_POWER_BUTTON = '55070f0d0078'
    __SERIAL_CODE_PRESS_SYSID_BUTTON = '55070f0e017a'
    __SERIAL_CODE_RELEASE_SYSID_BUTTON = '55070f0e0079'
    __SERIAL_CODE_PRESS_RESET_BUTTON = '55070f0f017b'
    __SERIAL_CODE_RELEASE_RESET_BUTTON = '55070f0f007a'
    __SERIAL_CODE_PRESS_NMI_BUTTON = '55070f10017c'
    __SERIAL_CODE_RELEASE_NMI_BUTTON = '55070f10007b'

    __SERIAL_CODE_GET_AD_HW_VERSION = '55050100000000005b'
    __SERIAL_CODE_GET_AD_SW_VERSION = '55050101000000005c'
    __SERIAL_CODE_GET_FP_HW_VERSION = '55050f000000000069'
    __SERIAL_CODE_GET_FP_SW_VERSION = '55050f01000000006a'

    __SERIAL_CODE_ENABLE_LIVE_DEBUG = '55000459'
    __SERIAL_CODE_DISABLE_LIVE_DEBUG = '5500055a'

    # FP two-ways port
    TWO_WAYS_DP_OUT_1 = 1
    TWO_WAYS_DP_OUT_2 = 2
    TWO_WAYS_DP_OUT_3 = 3
    TWO_WAYS_DP_OUT_4 = 4
    TWO_WAYS_DP_OUT_5 = 5
    TWO_WAYS_DP_OUT_6 = 6
    TWO_WAYS_DP_OUT_7 = 7
    TWO_WAYS_DP_OUT_8 = 8
    TWO_WAYS_DP_OUT_9 = 9
    TWO_WAYS_DP_OUT_10 = 10
    TWO_WAYS_DP_OUT_11 = 11
    TWO_WAYS_DP_OUT_12 = 12

    # FP One-way port
    POWER_BUTTON = 13
    SYSTEM_ID_BUTTON = 14
    RESET_BUTTON = 15
    NMI_BUTTON = 16

    # FP Input
    FP_IN1 = 17
    FP_IN2 = 18
    FP_IN3 = 19

    # FP cmd
    DP_TO_A = 0
    DP_TO_B = 1

    SP_OPEN = 0
    SP_SHORT = 1

    def __init__(self, port=sw_port, baud=sw_baud):
        self.__port_name = port
        self.__baud = baud
        self.__log_buf = []
        self.open()

    def open(self):
        self.__port = SoundWaveSerialPort(portName=self.__port_name, baudrate=self.__baud, timeout=2, writeTimeout=2)

    def close(self):
        """
        close serial port
        """
        if self.__port is not None:
            self.__port.close()
            self.__port = None

    def __gen_ad_cmd(self, code_list):
        """
        combine <5(max) AD INPUT codes in one SoundWave command, and return it.
        You can use the code from 1 to 60 number for AD INPUT code, others are not supported.
        :param code_list:    integer AD code, the length should between 1 to 5, code range should between 1 to 60.
        :return:        completed command
        """
        cmd = '550701'
        for each in code_list:
            channel = hex(each)[2:]
            if len(channel) == 1:
                channel = '0' + channel
            cmd += channel
        for i in range(5 - len(code_list)):
            cmd += 'ff'
        cmd += '0000000000'

        d = [cmd[0:2], cmd[2:4], cmd[4:6], cmd[6:8], cmd[8:10], cmd[10:12], cmd[12:14], cmd[14:16], cmd[16:18],
             cmd[18:20], cmd[20:22], cmd[22:24], cmd[24:26]]
        checksum = hex(sum(int(x, 16) for x in d))[-2:]
        cmd += checksum
        return cmd

    def __gen_ctr_fp_cmd(self, channel, ctr_switch):
        """
        generate command for control FP switch.
        :param channel: self.DP_OUT_1 ~ self.DP_OUT_12 two-ways switch;
        :param ctr_switch:  self.DP_TO_A or self.DP_TO_B
        :return: complete command
        """
        cmd = '55070f'
        port = hex(channel)[2:]
        if len(port) == 1:
            port = '0' + port
        port.lower()
        cmd += port

        if ctr_switch:
            cmd += '01'
        else:
            cmd += '00'

        d = [cmd[0:2], cmd[2:4], cmd[4:6], cmd[6:8], cmd[8:10]]
        checksum = hex(sum(int(x, 16) for x in d))[-2:]
        cmd += checksum
        return cmd

    def __gen_fp_state_cmd(self, channel):
        """
        generate command for get FP switch status.
        :param channel:self.DP_OUT_1 ~ self.DP_OUT_12 two-ways switch; self.POWER_BUTTON self.SYSTEM_ID_BUTTON self.RESET_BUTTON self.NMI_BUTTON one-way switch; self.FP_IN1 ~ self.FP_IN3 input
        :return: complete command
        """
        port = hex(channel)[2:]
        if len(port) == 1:
            port = '0' + port
        port.lower()
        cmd = '55080f' + port + '00'
        d = [cmd[0:2], cmd[2:4], cmd[4:6], cmd[6:8], cmd[8:10]]
        checksum = hex(sum(int(x, 16) for x in d))[-2:]
        cmd += checksum
        return cmd

    def __gen_set_user_message_cmd(self, user_msg):
        """
        generate command for get customer message command.
        :param user_msg: customer message, format is string, length should not bigger than 128
        :return: complete command
        """
        cmd = ''
        for i in range(len(user_msg)):
            chrtohex = hex(ord(user_msg[i]))[2:]
            if len(chrtohex) == 1:
                chrtohex = '0' + chrtohex
            cmd += chrtohex
        cmd = '550002' + cmd
        while len(cmd) != 262:
            cmd += 'ff'
        l = []
        for i in range(len(cmd) // 2):
            l.append(cmd[(2 * i): (2 * (i + 1))])
        checksum = hex(sum(int(x, 16) for x in l))[-2:]
        cmd += checksum
        return cmd

    def __execute_cmd(self, code, res_len):
        """
        :Execute send command to SoundWave and handle received log message.
        :param code: need send to SoundWave command.
        :return: received response message
        :exception
            SoundWaveError: incorrect length or checksum error for received serial data.
        """
        # if self.__port is None:
        #     self.open()

        self.__log_buf = []

        ret = self.__port.send(code)
        if not ret:
            raise SoundWaveError('command length error: {}'.format(code))

        fw_log = ''
        ret_code = ''
        while True:
            ret_value = self.__port.receive(1)
            if ret_value and '55' != ret_value:
                str_log = chr(int(ret_value, 16))
                fw_log += str_log
                if str_log == '\r':
                    logger.info('ControlBox log:{0}'.format(fw_log))
                    self.__log_buf.append(fw_log[:-1])
                    fw_log = ''
            elif ret_value == '55':
                coderet = self.__port.receive(res_len / 2 - 1)
                ret_code = '55' + coderet.lower()
                break
            else:
                logger.debug('Can not receive response!')
                ret_code = None
                break
        return ret_code

    def __check_response(self, cmd, response, compare_with=None):
        """
        :check SoundWave response message.
        If Specified value is default value(None), will check response length and message header according to command.
        Then check the checksum correct or not.
        if compareWith input parameter is not None, will compare it with returned result first.
        if False, will check response message length and message header according to compareWith, # delete this step
        check the checksum correct or not for locate the incorrect.

        :param cmd: the command had sent to SoundWave.
        :param response: received response message.
        :param compare_with: default is None, you can set it Specified value.
        :return: True
        :exception
            SoundWaveError: SoundWave no response.
        """

        if not response:
            raise SoundWaveError('SoundWave seems has some issue, there is no response from it.')

        if compare_with:
            if compare_with.lower() == response.lower():
                return True
            else:
                logger.error('response value error, expect {} but got {}'.format(compare_with, response))
                return False
        else:
            compare = cmd.lower()
            length = len(compare)
            header = compare[:6]

            if not len(response) == length:
                logger.error('length of the value is not equal {}'.format(length))
                return False

            if not ''.join(response).startswith(header):
                logger.error(
                    'response format is incorrect, expect header is {} but {}'.format(header, response[:6]))
                return False

            l = []
            for i in range(int((length - 2) / 2)):
                l.append(response[(2 * i): (2 * (i + 1))])
            checksum = hex(sum(int(x, 16) for x in l))[-2:]

            if not checksum == response[(length - 2): length]:
                logger.error('check sum is incorrect,expect {} but got:{}'.format(checksum,
                                                                                  response[(length - 2): length]))
                return False

            return True

    def reboot(self):
        """
        :Make SoundWave reboot.
        For SoundWave FW version 1.1.1.0, this API only reboot MAIN board;
        For FW version 2.0.0.0 or above, this API can reboot the 3 boards(MAIN board, AD board, FP board).
        :return: True or False
        :exception
            SoundWaveError: SoundWave no response.
        """

        response = self.__execute_cmd(self.__SERIAL_CODE_REBOOT, len(self.__SERIAL_CODE_REBOOT))

        return self.__check_response(self.__SERIAL_CODE_REBOOT, response, self.__SERIAL_CODE_REBOOT)

    def ac_power_on(self):
        """
        :send AC_POWER_ON command to SoundWave.
        :return: True or False
        :exception
            SoundWaveError: SoundWave no response.
        """

        response = self.__execute_cmd(self.__SERIAL_CODE_AC_ON, len(self.__SERIAL_CODE_AC_ON))

        return self.__check_response(self.__SERIAL_CODE_AC_ON, response, self.__SERIAL_CODE_AC_ON)

    def ac_power_off(self):
        """
        :send AC_POWER_OFF command to SoundWave.
        :return: True or False
        :exception
            SoundWaveError: SoundWave no response.
        """

        response = self.__execute_cmd(self.__SERIAL_CODE_AC_OFF, len(self.__SERIAL_CODE_AC_OFF))

        return self.__check_response(self.__SERIAL_CODE_AC_OFF, response, self.__SERIAL_CODE_AC_OFF)

    def usb_to_port_a(self):
        """
        :Make USB port c connect to USB Port A, and LED A will bright.
        :return: True or False
        :exception
            SoundWaveError: SoundWave no response.
        """

        response = self.__execute_cmd(self.__SERIAL_CODE_USB_TO_PORTA, len(self.__SERIAL_CODE_USB_TO_PORTA))

        return self.__check_response(self.__SERIAL_CODE_USB_TO_PORTA, response, self.__SERIAL_CODE_USB_TO_PORTA)

    def usb_to_port_b(self):
        """
        :Make USB port c connect to USB Port B, LED B will bright.
        :return: True or False
        :exception
            SoundWaveError: SoundWave no response.
        """

        response = self.__execute_cmd(self.__SERIAL_CODE_USB_TO_PORTB, len(self.__SERIAL_CODE_USB_TO_PORTB))

        return self.__check_response(self.__SERIAL_CODE_USB_TO_PORTB, response, self.__SERIAL_CODE_USB_TO_PORTB)

    def usb_to_open(self):
        """
        :Make USB port c open. LED A and LED B on SoundWave will be turn off.
        :return: True or False
        :exception
            SoundWaveError: SoundWave no response.
        """
        response = self.__execute_cmd(self.__SERIAL_CODE_USB_TO_OPEN, len(self.__SERIAL_CODE_USB_TO_OPEN))

        return self.__check_response(self.__SERIAL_CODE_USB_TO_OPEN, response, self.__SERIAL_CODE_USB_TO_OPEN)

    def press_power_button(self):
        """
        :control FP board SP_OUT_1 to short
        switch on FP board swap to Manual, this API no effect, but you can control the POWER button
        switch on FP board swap to auto, this API can control FP board SP_OUT_1, and the POWER button no effect
        :return: True or False
        :exception
            SoundWaveError: SoundWave no response.
        """
        response = self.__execute_cmd(self.__SERIAL_CODE_PRESS_POWER_BUTTON,
                                      len(self.__SERIAL_CODE_PRESS_POWER_BUTTON))

        return self.__check_response(self.__SERIAL_CODE_PRESS_POWER_BUTTON, response,
                                     self.__SERIAL_CODE_PRESS_POWER_BUTTON)

    def release_power_button(self):
        """
        :control FP board SP_OUT_1 to open
        switch on FP board swap to Manual, this API no effect, but you can control the POWER button
        switch on FP board swap to auto, this API can control FP board SP_OUT_1, and the POWER button no effect
        :return: True or False
        :exception
            SoundWaveError: SoundWave no response.
        """
        response = self.__execute_cmd(self.__SERIAL_CODE_RELEASE_POWER_BUTTON,
                                      len(self.__SERIAL_CODE_RELEASE_POWER_BUTTON))

        return self.__check_response(self.__SERIAL_CODE_RELEASE_POWER_BUTTON, response,
                                     self.__SERIAL_CODE_RELEASE_POWER_BUTTON)

    def press_system_id_button(self):
        """
        :control FP board SP_OUT_1 to short
        switch on FP board swap to Manual, this API no effect, but you can control the SYSTEM_ID button
        switch on FP board swap to auto, this API can control FP board SP_OUT_2, and the SYSTEM_ID button no effect
        :return: True or False
        :exception
            SoundWaveError: SoundWave no response.
        """
        response = self.__execute_cmd(self.__SERIAL_CODE_PRESS_SYSID_BUTTON,
                                      len(self.__SERIAL_CODE_PRESS_SYSID_BUTTON))

        return self.__check_response(self.__SERIAL_CODE_PRESS_SYSID_BUTTON, response,
                                     self.__SERIAL_CODE_PRESS_SYSID_BUTTON)

    def release_system_id_button(self):
        """
        :control FP board SP_OUT_1 to open
        switch on FP board swap to Manual, this API no effect, but you can control the SYSTEM_ID button
        switch on FP board swap to auto, this API can control FP board SP_OUT_2, and the SYSTEM_ID button no effect
        :return: True or False
        :exception
            SoundWaveError: SoundWave no response.
        """
        response = self.__execute_cmd(self.__SERIAL_CODE_RELEASE_SYSID_BUTTON,
                                      len(self.__SERIAL_CODE_RELEASE_SYSID_BUTTON))

        return self.__check_response(self.__SERIAL_CODE_RELEASE_SYSID_BUTTON, response,
                                     self.__SERIAL_CODE_RELEASE_SYSID_BUTTON)

    def press_reset_button(self):
        """
        :control FP board SP_OUT_1 to short
        switch on FP board swap to Manual, this API no effect, but you can control the RESET button
        switch on FP board swap to auto, this API can control FP board SP_OUT_3, and the RESET button no effect
        :return: True or False
        :exception
            SoundWaveError: SoundWave no response.
        """
        response = self.__execute_cmd(self.__SERIAL_CODE_PRESS_RESET_BUTTON,
                                      len(self.__SERIAL_CODE_PRESS_RESET_BUTTON))

        return self.__check_response(self.__SERIAL_CODE_PRESS_RESET_BUTTON, response,
                                     self.__SERIAL_CODE_PRESS_RESET_BUTTON)

    def release_reset_button(self):
        """
        :control FP board SP_OUT_1 to open
        switch on FP board swap to Manual, this API no effect, but you can control the RESET button
        switch on FP board swap to auto, this API can control FP board SP_OUT_3, and the RESET button no effect
        :return: True or False
        :exception
            SoundWaveError: SoundWave no response.
        """
        response = self.__execute_cmd(self.__SERIAL_CODE_RELEASE_RESET_BUTTON,
                                      len(self.__SERIAL_CODE_RELEASE_RESET_BUTTON))

        return self.__check_response(self.__SERIAL_CODE_RELEASE_RESET_BUTTON, response,
                                     self.__SERIAL_CODE_RELEASE_RESET_BUTTON)

    def press_nmi_button(self):
        """
        :control FP board SP_OUT_4 to short
        switch on FP board swap to Manual, this API no effect, but you can control the NMI button
        switch on FP board swap to auto, this API can control FP board SP_OUT_4, and the NMI button no effect
        :return: True or False
        :exception
            SoundWaveError: SoundWave no response.
        """
        response = self.__execute_cmd(self.__SERIAL_CODE_PRESS_NMI_BUTTON, len(self.__SERIAL_CODE_PRESS_NMI_BUTTON))

        return self.__check_response(self.__SERIAL_CODE_PRESS_NMI_BUTTON, response,
                                     self.__SERIAL_CODE_PRESS_NMI_BUTTON)

    def release_nmi_button(self):
        """
        :control FP board SP_OUT_4 to open.
        switch on FP board swap to Manual, this API no effect, but you can control the NMI button
        switch on FP board swap to auto, this API can control FP board SP_OUT_4, and the NMI button no effect
        :return: True or False
        :exception
            SoundWaveError: SoundWave no response.
        """
        response = self.__execute_cmd(self.__SERIAL_CODE_RELEASE_NMI_BUTTON,
                                      len(self.__SERIAL_CODE_RELEASE_NMI_BUTTON))

        return self.__check_response(self.__SERIAL_CODE_RELEASE_NMI_BUTTON, response,
                                     self.__SERIAL_CODE_RELEASE_NMI_BUTTON)

    def get_ad_values(self, code_list):
        """
        combine <5(max) AD INPUT codes in one SoundWave command, and read back their value at one time.
        You should identify which AD INPUT values you want to read back via code_list parameter.
        You can use the code from 1 to 60 number for AD INPUT code, others are not supported.

        :param code_list:    integer AD code, the length should between 1 to 5, code range should between 1 to 60.
        :return:        integer AD value list or empty list
        :exception
            INPUT_ERROR: incorrect length or code for code_list.
            SoundWaveError: SoundWave no response.
        """
        if len(code_list) > 5 or len(code_list) == 0:
            logger.error('Input AD channel length wrong:{}'.format(code_list))
            raise InputError(
                'expect length of input AD channel list less than 5, but got:{}'.format(len(code_list)))
        for each in code_list:
            if each == 0 or each > 60:
                logger.error('Input AD channel out of range:{}'.format(each))
                raise InputError('Input AD channel out of range:{}'.format(each))

        cmd = self.__gen_ad_cmd(code_list)

        response = self.__execute_cmd(cmd, len(cmd))

        if self.__check_response(cmd, response):

            hexadstr = [response[16: 18], response[18: 20], response[20: 22], response[22: 24], response[24: 26]]
            advalues = []
            for x in range(len(code_list)):
                advalues.append(float(int(hexadstr[x], 16) * 12) / 255)
            return advalues
        else:
            return []

    def ctr_fp_two_ways_switch(self, fp_port, action):
        """
        Control specified TWO WAYS switch on FP board., for two-ways port(DP_OUT_1 ~ DP_OUT_12), switch to A or B
        :param fp_port: internal port name same as flag on cable, self.TWO_WAYS_DP_OUT_1 ~ self.TWO_WAYS_DP_OUT_12
        :param action: self.DP_TO_A or self.DP_TO_B
        :return:        True or False
        :exception
            INPUT_ERROR: incorrect port name.
            SoundWaveError: SoundWave no response.
        """
        if fp_port < self.TWO_WAYS_DP_OUT_1 or fp_port > self.TWO_WAYS_DP_OUT_12:
            logger.error('input FP port number out of range:{}'.format(fp_port))
            raise InputError('Expected in self.DP_OUT_1 ~ self.DP_OUT_12 or self.SP_OUT_1 ~ self.SP_OUT_4, '
                             'but got {}'.format(fp_port))

        if action < 0 or action > 1:
            logger.error('FP switch no this action:{}'.format(action))
            raise InputError('Expected self.DP_TO_A(self.SP_OPEN) or self.DP_TO_A(self.SP_SHORT), '
                             'but got {}'.format(action))

        cmd = self.__gen_ctr_fp_cmd(fp_port, action)

        response = self.__execute_cmd(cmd, len(cmd))

        return self.__check_response(cmd, response, None)

    def get_fp_switch_state(self, fp_port):
        """
        Get specified switch's status on FP board.
        for two-ways channel(DP_OUT_1 ~ DP_OUT_12), for one-way port(POWER_BUTTON, SYSTEM_ID_BUTTON, RESET_BUTTON, NMI_BUTTON), for input(FP_IN1 ~ FP_IN3).
        :param fp_port: self.TWO_WAYS_DP_OUT_1 ~ self.TWO_WAYS_DP_OUT_12 or self.POWER_BUTTON, self.SYSTEM_ID_BUTTON, self.RESET_BUTTON, self.NMI_BUTTON or self.FP_IN1 ~ self.FP_IN3.
        :return: specified Switch's status as '0*' or None
        :exception
            INPUT_ERROR: incorrect port name.
            SoundWaveError: SoundWave no response.
        """
        if fp_port < self.TWO_WAYS_DP_OUT_1 or fp_port > self.FP_IN3:
            logger.debug('FP channel out of range:{}'.format(fp_port))
            raise InputError('Expected in self.DP_OUT_1 ~ self.DP_OUT_12 or self.SP_OUT_1 ~ self.SP_OUT_4 '
                             'or self.FP_IN1 ~ self.FP_IN3 ,but got {}'.format(fp_port))

        cmd = self.__gen_fp_state_cmd(fp_port)

        response = self.__execute_cmd(cmd, len(cmd))

        if self.__check_response(cmd, response):

            if self.TWO_WAYS_DP_OUT_1 <= fp_port <= self.TWO_WAYS_DP_OUT_12:
                if int(response[8: 10]) == self.DP_TO_A:
                    return response[8: 10]
                elif int(response[8: 10]) == self.DP_TO_B:
                    return response[8: 10]

            elif fp_port in [self.POWER_BUTTON, self.SYSTEM_ID_BUTTON, self.RESET_BUTTON, self.NMI_BUTTON]:
                if int(response[8: 10]) == self.SP_OPEN:
                    return response[8: 10]
                elif int(response[8: 10]) == self.SP_SHORT:
                    return response[8: 10]

            elif self.FP_IN1 <= fp_port <= self.FP_IN3:
                if int(response[8: 10]) == 1:
                    return response[8: 10]
                elif int(response[8: 10]) == 0:
                    return response[8: 10]
        else:
            return None

    def get_hw_version(self):
        """
        get SoundWave hardware version.
        :return: SoundWave hardware version as 'xx.xx.xx.xx' or ''
        :exception
            SoundWaveError: SoundWave no response.
        """

        response = self.__execute_cmd(self.__SERIAL_CODE_GET_HARDWARE_VERSION, len('5500000000000055'))
        if self.__check_response('5500000000000055', response):

            hexhwstr = [response[-10: -8], response[-8: -6], response[-6: -4], response[-4: -2]]
            hwversion = ''
            for x in hexhwstr:
                hwversion += x
                hwversion += '.'
            return hwversion[:-1]
        else:
            return ''

    def get_sw_version(self):
        """
        get SoundWave software version.
        :return: SoundWave software version as 'xx.xx.xx.xx' or ''
        :exception
            SoundWaveError: SoundWave no response.
        """

        response = self.__execute_cmd(self.__SERIAL_CODE_GET_SOFTWARE_VERSION, len('5500010000000056'))

        if self.__check_response('5500010000000056', response):
            hexswstr = [response[-10: -8], response[-8: -6], response[-6: -4], response[-4: -2]]
            swversion = ''
            for x in hexswstr:
                swversion += x
                swversion += '.'
            return swversion[:-1]
        else:
            return ''

    def get_user_messasge(self):
        """
        get customer message.
        :return: customer message or ''
        :exception
            SoundWaveError: SoundWave no response.
        """

        response = self.__execute_cmd(self.__SERIAL_CODE_GET_CUSTOMER_MESSAGE, 264)

        if not response:
            raise SoundWaveError('SoundWave seems has some issue, there is no response from it.')

        if not len(response) == 264:
            logger.error('length of the value is not equal 264!')
            return ''

        if not ''.join(response).startswith('550003'):
            logger.error("response format is incorrect, expect header is '550003' but {}".format(response[:6]))
            return ''

        l = []
        for i in range(131):
            l.append(response[(2 * i): (2 * (i + 1))])
        checksum = hex(sum(int(x, 16) for x in l))[-2:]

        if not checksum == response[262: 264]:
            logger.error('check sum is incorrect,expect {} but got:{}'.format(checksum, response[262: 264]))
            return ''

        user_msg = ''
        for i in range(3, 131):
            if l[i] == 'ff':
                break
            str_log = chr(int(l[i], 16))
            user_msg += str_log
        return user_msg

    def set_user_messasge(self, user_msg):
        """
        Set customer message, message length should less than 128.
        :param user_msg: customer message, is a string, length less than 128
        :return: True or False
        :exception
            SoundWaveError: SoundWave no response.
        """

        if user_msg == '':
            logger.error('No customer message input!')
            raise SoundWaveError('No customer message input!')

        if len(user_msg) > 128:
            logger.error('length of the value is out of range!')
            raise SoundWaveError(
                'Length of customer message should not bigger than 128, but {}'.format(len(user_msg)))

        cmd = self.__gen_set_user_message_cmd(user_msg)

        response = self.__execute_cmd(cmd, len(cmd))

        return self.__check_response(cmd, response)

    def get_ad_hw_version(self):
        """
        New API, only for soundWave software version 2.0.1.0 or above, get AD board hardware version.
        :return: ad board hardware version as 'xx.xx.xx.xx' or ''
        :exception
            SoundWaveError: SoundWave no response.
        """

        response = self.__execute_cmd(self.__SERIAL_CODE_GET_AD_HW_VERSION,
                                      len(self.__SERIAL_CODE_GET_AD_HW_VERSION))
        if self.__check_response(self.__SERIAL_CODE_GET_AD_HW_VERSION, response):

            hexhwstr = [response[-10: -8], response[-8: -6], response[-6: -4], response[-4: -2]]
            adhwversion = ''
            for x in hexhwstr:
                adhwversion += x
                adhwversion += '.'
            return adhwversion[:-1]
        else:
            return ''

    def get_ad_sw_version(self):
        """
        New API, only for soundWave software version 2.0.1.0 or above, get AD board software version.
        :return: ad board software version as 'xx.xx.xx.xx' or ''
        :exception
            SoundWaveError: SoundWave no response.
        """

        response = self.__execute_cmd(self.__SERIAL_CODE_GET_AD_SW_VERSION,
                                      len(self.__SERIAL_CODE_GET_AD_SW_VERSION))

        if self.__check_response(self.__SERIAL_CODE_GET_AD_SW_VERSION, response):

            hexswstr = [response[-10: -8], response[-8: -6], response[-6: -4], response[-4: -2]]
            adswversion = ''
            for x in hexswstr:
                adswversion += x
                adswversion += '.'
            return adswversion[:-1]
        else:
            return ''

    def get_fp_hw_version(self):
        """
        New API, only for soundWave software version 2.0.1.0 or above, get FP board hardware version.
        :return: FP board hardware version as 'xx.xx.xx.xx' or ''
        :exception
            SoundWaveError: SoundWave no response.
        """

        response = self.__execute_cmd(self.__SERIAL_CODE_GET_FP_HW_VERSION,
                                      len(self.__SERIAL_CODE_GET_FP_HW_VERSION))
        if self.__check_response(self.__SERIAL_CODE_GET_FP_HW_VERSION, response):

            hexhwstr = [response[-10: -8], response[-8: -6], response[-6: -4], response[-4: -2]]
            fphwversion = ''
            for x in hexhwstr:
                fphwversion += x
                fphwversion += '.'
            return fphwversion[:-1]
        else:
            return ''

    def get_fp_sw_version(self):
        """
        New API, only for soundWave software version 2.0.1.0 or above, get FP board software version.
        :return: FP board software version as 'xx.xx.xx.xx' or ''
        :exception
            SoundWaveError: SoundWave no response.
        """

        response = self.__execute_cmd(self.__SERIAL_CODE_GET_FP_SW_VERSION,
                                      len(self.__SERIAL_CODE_GET_FP_SW_VERSION))

        if self.__check_response(self.__SERIAL_CODE_GET_FP_SW_VERSION, response):

            hexswstr = [response[-10: -8], response[-8: -6], response[-6: -4], response[-4: -2]]
            fpswversion = ''
            for x in hexswstr:
                fpswversion += x
                fpswversion += '.'
            return fpswversion[:-1]
        else:
            return ''

    def enable_live_debug(self):
        """
        New API, only for soundWave software version 2.0.1.0 or above release edition. enable live debug function, can get more log messages for debug.
        :return: True or False
        :exception
            SoundWaveError: SoundWave no response.
        """
        response = self.__execute_cmd(self.__SERIAL_CODE_ENABLE_LIVE_DEBUG,
                                      len(self.__SERIAL_CODE_ENABLE_LIVE_DEBUG))
        return self.__check_response(self.__SERIAL_CODE_ENABLE_LIVE_DEBUG, response,
                                     self.__SERIAL_CODE_ENABLE_LIVE_DEBUG)

    def disable_live_debug(self):
        """
        New API, only for soundWave software version 2.0.1.0 or above release edition. disable live debug function, only get critical message.
        :return: True or False
        :exception
            SoundWaveError: SoundWave no response.
        """
        response = self.__execute_cmd(self.__SERIAL_CODE_DISABLE_LIVE_DEBUG,
                                      len(self.__SERIAL_CODE_DISABLE_LIVE_DEBUG))
        return self.__check_response(self.__SERIAL_CODE_DISABLE_LIVE_DEBUG, response,
                                     self.__SERIAL_CODE_DISABLE_LIVE_DEBUG)


class SoundWaveSerialPort:
    def __init__(self, portName=None, baudrate=None, timeout=0, writeTimeout=0):
        self.portName = portName
        self.__serialConfig = {'port': portName,
                               'baudrate': baudrate,
                               'bytesize': 8,
                               'timeout': timeout,
                               'write_timeout': writeTimeout,
                               }
        self._serial = None
        self.open()

    def open(self):
        '''
        create serial port object and open the it.
        :exception: DeviceError: WindowsError Access is denied or couldn't device.
        '''
        try:
            self._serial = Serial(**self.__serialConfig)
        except SerialException as ex:
            logger.error(ex)
            logger.warning('try to open again')
            self._serial = Serial(**self.__serialConfig)

    def __write(self, data):
        self._serial.reset_output_buffer()
        self._serial.reset_input_buffer()
        length = self._serial.write(binascii.a2b_hex(data))
        return length

    def send(self, data):
        length = 0
        if self._serial is None:
            self.open()

        try:
            logger.debug('serial write:{}'.format(data))
            length = self.__write(data)
            logger.debug('write done:{}'.format(length))
        except SerialTimeoutException as ex:
            logger.error(ex)
            self.close()
            logger.warning('re-open')
            self.open()
            logger.warning('re-send {0}'.format(data))
            try:
                length = self.__write(data)
                logger.debug('re-write done:{}'.format(length))
            except SerialTimeoutException as ex:
                logger.error(ex)
                return False

        return True if length == len(data) / 2 else False

    def receive(self, size=None):
        if self._serial is None:
            self.open()

        try:
            logger.debug('serial try receive:{}'.format(size))
            if size is None:
                data = binascii.b2a_hex(self._serial.read())
            else:
                data = binascii.b2a_hex(self._serial.read(int(size)))

            import six
            if six.PY2:
                data = data
            else:
                data = data.decode()

            logger.debug('receive done:{}'.format(data))
            return data
        except SerialException as ex:
            logger.error(ex)
            self.close()
            logger.warning('re-open')
            self.open()
            return ''

    def close(self):
        '''
        close serial port
        '''
        if self._serial:
            self._serial.close()
            self._serial = None


serial_lock = threading.Lock()
port_lock = threading.Lock()
serial_content = ""


class Serial_Log(threading.Thread):
    def __init__(self, port):
        super(Serial_Log, self).__init__()
        self.port_num = port
        self.__maxsize = 1024 * 10
        self.__serial_log = ""
        self.serial_fp = None
        self.__port = None
        self.open()

    def log_fp(self):
        global SERIAL_LOG_PATH
        fp = open(SERIAL_LOG_PATH, "w")
        return fp

    def __log_close(self):
        self.serial_fp.close()

    def open(self):
        global serial_content
        try:
            if self.__port:
                self.__close()
            self.__port = serial.Serial(self.port_num, 115200, timeout=5)
            serial_content += "\nOpen serial {} port successful".format(self.port_num)
            return True
        except Exception as ex:
            serial_content += "\n" + str(ex)
            self.__port = None
            return False

    def __close(self):
        if self.__port:
            self.__port.close()

    def run(self):
        global serial_lock
        global serial_content
        show_serial_error = True
        self.__is_stop = False
        while not self.__is_stop:
            try:
                if serial_lock:
                    serial_lock.acquire()
                if self.__port:
                    date_length = self.__port.in_waiting
                    if date_length > 0:
                        serial_info = self.__port.read(date_length).decode()
                        serial_content += serial_info
                        if self.serial_fp:
                            self.serial_fp.write(serial_info)
                else:
                    time.sleep(5)
                    if not self.open():
                        self.__is_stop = True
            except Exception as ex:
                if show_serial_error:
                    serial_content += "\n" + str(ex)
            finally:
                if serial_lock:
                    serial_lock.release()
        if self.__port:
            self.__close()
        if self.serial_fp:
            self.serial_fp.flush()
            self.__log_close()

    def stop(self):
        if not self.__is_stop:
            global serial_content
            serial_content += "\nClose serial {} port".format(self.port_num)
            self.__is_stop = True
            self.join(1)
            if self.is_alive():
                self.stop()


def deco(func):
    def warpper(*args, **kwargs):
        global port_lock
        port_lock.acquire()
        try:
            func(*args, **kwargs)
        except Exception as ex:
            print(ex)
        finally:
            port_lock.release()

    return warpper


class Power_Action(object):
    dir_path = os.path.dirname(os.path.realpath(__file__))
    log_path = os.path.join(dir_path, "ad_value.log")
    ad_fp = open(log_path, "wb")
    AC_TIMEOUT = 60

    @deco
    def ac_on(self):
        soundwave = SoundWave(self.port_entry_value.get(), self.baud_entry_value.get())
        result = soundwave.ac_power_on()
        res = "AC power on action is: {}\n".format(result)
        if result:
            self.button_ac_on["background"] = "DarkOliveGreen3"
            self.button_ac_off["background"] = "White"
            self.button_dc_on["background"] = "White"
            self.button_dc_off["background"] = "White"
        else:
            self.button_ac_on["background"] = "red"
        self.button_text.insert(END, res, 'blue')
        self.button_text.see(END)
        soundwave.close()

    @deco
    def ac_off(self):
        soundwave = SoundWave(self.port_entry_value.get(), self.baud_entry_value.get())
        result = soundwave.ac_power_off()
        res = "AC power off action is: {}\n".format(result)
        if result:
            self.button_ac_off["background"] = "DarkOliveGreen3"
            self.button_ac_on["background"] = "White"
            self.button_dc_on["background"] = "White"
            self.button_dc_off["background"] = "White"
        else:
            self.button_ac_off["background"] = "red"
        self.button_text.insert(END, res, 'blue')
        self.button_text.see(END)
        soundwave.close()

    @deco
    def dc_off(self):
        soundwave = SoundWave(self.port_entry_value.get(), self.baud_entry_value.get())
        soundwave.press_power_button()
        time.sleep(7)
        result = soundwave.release_power_button()
        res = "DC power off action is: {}\n".format(result)
        if result:
            self.button_dc_off["background"] = "DarkOliveGreen3"
            self.button_ac_off["background"] = "White"
            self.button_ac_on["background"] = "White"
            self.button_dc_on["background"] = "White"
        else:
            self.button_ac_on["background"] = "red"
        self.button_text.insert(END, res, 'blue')
        self.button_text.see(END)
        soundwave.close()

    @deco
    def dc_on(self):
        soundwave = SoundWave(self.port_entry_value.get(), self.baud_entry_value.get())
        soundwave.press_power_button()
        time.sleep(1)
        result = soundwave.release_power_button()
        res = "DC power on action is: {}\n".format(result)
        if result:
            self.button_dc_on["background"] = "DarkOliveGreen3"
            self.button_ac_off["background"] = "White"
            self.button_ac_on["background"] = "White"
            self.button_dc_off["background"] = "White"
        else:
            self.button_ac_on["background"] = "red"
        self.button_text.insert(END, res, 'blue')
        self.button_text.see(END)
        soundwave.close()

    @deco
    def reset(self):
        soundwave = SoundWave(self.port_entry_value.get(), self.baud_entry_value.get())
        soundwave.press_reset_button()
        time.sleep(1)
        result = soundwave.release_reset_button()
        res = "Reset action is: {}\n".format(result)
        self.button_text.insert(END, res, 'blue')
        self.button_text.see(END)
        soundwave.close()

    @deco
    def usb_to_host(self):
        soundwave = SoundWave(self.port_entry_value.get(), self.baud_entry_value.get())
        soundwave.usb_to_open()
        time.sleep(1)
        result = soundwave.usb_to_port_a()
        res = "Switch usb to Host action is: {}\n".format(result)
        if result:
            self.button_usb_host["background"] = "DarkOliveGreen3"
            self.button_usb_open["background"] = "White"
            self.button_usb_sut["background"] = "White"
        else:
            self.button_usb_host["background"] = "red"
        self.button_text.insert(END, res, 'blue')
        self.button_text.see(END)
        soundwave.close()

    @deco
    def usb_to_sut(self):
        soundwave = SoundWave(self.port_entry_value.get(), self.baud_entry_value.get())
        soundwave.usb_to_open()
        time.sleep(1)
        result = soundwave.usb_to_port_b()
        res = "Switch usb to SUT action is: {}\n".format(result)
        if result:
            self.button_usb_sut["background"] = "DarkOliveGreen3"
            self.button_usb_host["background"] = "White"
            self.button_usb_open["background"] = "White"
        else:
            self.button_usb_sut["background"] = "red"
        self.button_text.insert(END, res, 'blue')
        self.button_text.see(END)
        soundwave.close()

    @deco
    def usb_to_open(self):
        soundwave = SoundWave(self.port_entry_value.get(), self.baud_entry_value.get())
        result = soundwave.usb_to_open()
        time.sleep(1)
        res = "Switch sub to open action is: {}\n".format(result)
        if result:
            self.button_usb_open["background"] = "DarkOliveGreen3"
            self.button_usb_host["background"] = "White"
            self.button_usb_sut["background"] = "White"
        else:
            self.button_usb_open["background"] = "red"
        self.button_text.insert(END, res, 'blue')
        self.button_text.see(END)
        soundwave.close()

    @deco
    def get_power_status(self, p3v3, p3v3_aux):
        default_p3v3 = float(self.p3v3_vol.get())
        default_p3v3aux = float(self.p3v3aux_vol.get())

        if p3v3 <= default_p3v3 and p3v3_aux <= default_p3v3:
            return "G3"
        elif p3v3 <= default_p3v3 and p3v3_aux >= default_p3v3aux:
            return "S5"
        elif p3v3 >= default_p3v3aux and p3v3_aux >= default_p3v3aux:
            return "S0"
        else:
            return "NA"

    def power_value(self):
        if self.__show_power:
            soundwave = SoundWave(self.port_entry_value.get(), self.baud_entry_value.get())
            try:
                port_lock.acquire()
                result = soundwave.get_ad_values([2, 11])
                p3v3 = round(result[0], 5)
                p3v3_aux = round(result[1], 5)
                default_p3v3 = float(self.p3v3_vol.get())
                default_p3v3aux = float(self.p3v3aux_vol.get())
                if p3v3 <= default_p3v3 and p3v3_aux <= default_p3v3:
                    power_name = "G3"
                elif p3v3 <= default_p3v3 and p3v3_aux >= default_p3v3aux:
                    power_name = "S5"
                elif p3v3 >= default_p3v3aux and p3v3_aux >= default_p3v3aux:
                    power_name = "S0"
                else:
                    power_name = "NA"
                self.power_status.set(power_name)
                self.ad_fp.write("{0} : {1} : {2}\n".format(str(time.asctime()), str(result), power_name).encode())
                self.ad_fp.flush()
            except Exception as ex:
                print(ex)
            finally:
                port_lock.release()
        self.button_power_list.after(2000, self.power_value)

    def check_version(self):
        soundwave = SoundWave(self.port_entry_value.get(), self.baud_entry_value.get())
        result = soundwave.get_ad_sw_version()
        res = result.split(':')[-1]
        self.entry_show_ver["state"] = "normal"
        self.main_version.set(res)
        self.button_text.insert(END, res, 'blue')
        self.button_text.see(END)
        soundwave.close()

    def button_show(self):
        if self.__show_power:
            self.entry_power_status['state'] = "disabled"
            self.__show_power = False
            self.power_status.set("")
            self.button_power_list.after_cancel(self.power_value)
        else:
            self.entry_power_status['state'] = "normal"
            self.__show_power = True
            self.button_power_list.after(2000, self.power_value)

    def show_serial_text(self):
        global serial_lock
        global serial_content
        if serial_content:
            serial_lock.acquire()
            try:
                self.serialtext.insert(END, serial_content)
                self.serialtext.see(END)
                self.serialtext.after(500, self.show_serial_text)
            finally:
                serial_lock.release()
                serial_content = ""
        else:
            self.serialtext.after(500, self.show_serial_text)

    def serial_log_save_to(self):
        global SERIAL_LOG_PATH
        global serial_content
        file_name = filedialog.asksaveasfilename(**self.file_opt)
        serial_content += "\nSave serial log to {}".format(file_name)
        self.serial_log_value.set(file_name)
        SERIAL_LOG_PATH = file_name
        if self.serial_obj:
            self.serial_obj.serial_fp = self.serial_obj.log_fp()

    def start_serial_port(self):
        self.serial_obj = Serial_Log(self.com_value.get())
        self.serial_obj.setDaemon(True)
        self.serial_obj.start()
        self.btn_serial_start["background"] = "DarkOliveGreen3"
        self.btn_serial_stop["background"] = "White"

    def stop_serial_port(self):
        self.serial_obj.stop()
        self.btn_serial_stop["background"] = "DarkOliveGreen3"
        self.btn_serial_start["background"] = "White"

    def detect_voltage(self):
        Voltage(self)

    def jumper_setting(self):
        JumperSetting(self)

    def __init__(self):
        self.__show_power = False
        self.root = Tk()
        self.root.geometry('822x738')
        self.root.resizable(width=False, height=False)
        self.root.title('Soundwave Control Panel')
        self.root["background"] = "azure2"
        self.setup()

    def setup(self):
        serialframe = Frame(self.root, width=75, height=500, bd=5, bg='white')
        buttonframe = Frame(self.root, width=28, height=500, bd=5, bg='white')

        serial_title = Label(serialframe, width=79, text="Serial Output", bg='azure3', fg='Yellow',
                             font=("Times", "10", "bold italic"))
        self.btn_serial_start = Button(serialframe, width=6, text="Start", bg="white", command=self.start_serial_port)
        self.btn_serial_stop = Button(serialframe, width=6, text="Stop", bg="white", command=self.stop_serial_port)
        self.serial_port_lable = Label(serialframe, text="Port", bg="alice blue", width=8)
        self.com_value = StringVar()
        self.com_value.set("COM100")
        self.serial_port_vaule = Entry(serialframe, textvariable=self.com_value, width=9)
        self.label_serial_baud = Label(serialframe, text="Baud", bg="alice blue", width=8)
        self.serial_baud_value = StringVar()
        self.serial_baud_value.set(115200)
        self.serial_baud = Entry(serialframe, textvariable=self.serial_baud_value, width=8)

        self.file_opt = options = {}
        options['defaultextension'] = '.txt'
        options['filetypes'] = [('all files', '.*'), ('text files', '.log')]
        options['initialdir'] = CURENT_PATH
        options['initialfile'] = 'serial.log'
        options['title'] = 'This is a title'

        self.serial_log_lable = Label(serialframe, text="Log Path", bg="alice blue", width=15)
        self.serial_log_value = StringVar()
        self.serial_log_value.set(SERIAL_LOG_PATH)
        self.serial_log_entry = Entry(serialframe, textvariable=self.serial_log_value, width=55)
        self.serial_log_button = Button(serialframe, width=5, text="Save", bg="white", command=self.serial_log_save_to)
        self.serialtext = ScrolledText(serialframe, width=67, height=39)

        # Controlbox Button
        button_title = Label(buttonframe, width=30, text="Soundwave Control", bg='azure3', fg='Yellow',
                             font=("Times", "10", "bold italic"))
        self.label_port = Label(buttonframe, width=14, text="Port", bg="alice blue")
        self.port_entry_value = StringVar()
        self.port_entry_value.set('COM101')
        self.port_value = Entry(buttonframe, width=15, textvariable=self.port_entry_value)
        global port_entry_value
        port_entry_value = self.port_entry_value

        self.label_baud = Label(buttonframe, width=14, text="Baud", bg="alice blue")
        self.baud_entry_value = StringVar()
        self.baud_entry_value.set(115200)
        self.baud_value = Entry(buttonframe, width=15, textvariable=self.baud_entry_value)
        global baud_entry_value
        baud_entry_value = self.baud_entry_value
        self.button_text = ScrolledText(buttonframe, width=24, height=21)

        self.p3v3_vol = StringVar()
        self.p3v3aux_vol = StringVar()
        self.p3v3_vol.set("0.8")
        self.p3v3aux_vol.set("2.8")

        self.p3v3 = Label(buttonframe, width=14, bg="alice blue", text="P3V3")
        self.entry_p3v3_vol = Entry(buttonframe, width=15, textvariable=self.p3v3_vol)
        self.p3v3aux = Label(buttonframe, width=14, bg="alice blue", text="P3V3_AUX")
        self.entry_p3v3aux_val = Entry(buttonframe, width=15, textvariable=self.p3v3aux_vol)

        self.button_ac_on = Button(buttonframe, width=14, text="Ac On", bg="white", command=self.ac_on)
        self.button_ac_off = Button(buttonframe, width=14, text="Ac Off", bg="white", command=self.ac_off)
        self.button_dc_on = Button(buttonframe, width=14, text="Dc On", bg="white", command=self.dc_on)
        self.button_dc_off = Button(buttonframe, width=14, text="Dc Off", bg="white", command=self.dc_off)
        self.button_reset = Button(buttonframe, width=14, text="Reset", bg="white", command=self.reset)
        self.button_usb_open = Button(buttonframe, width=14, text="Usb -> Open", bg="white", command=self.usb_to_open)
        self.button_usb_host = Button(buttonframe, width=14, text="Usb -> Host", bg="white", command=self.usb_to_host)
        self.button_usb_sut = Button(buttonframe, width=14, text="Usb -> Sut", bg="white", command=self.usb_to_sut)
        self.button_voltage = Button(buttonframe, width=14, text="Detect Voltage", bg="white", command=self.detect_voltage)
        self.button_jumper = Button(buttonframe, width=14, text="Jumper Setting", bg="white", command=self.jumper_setting)

        self.power_list = StringVar()
        self.power_list.set("Sut Current Power")
        self.button_power_list = Button(buttonframe, width=14, textvariable=self.power_list, bg="white", command=self.button_show)

        self.power_status = StringVar()
        self.power_status.set(" ")
        self.entry_power_status = Entry(buttonframe, width=15, textvariable=self.power_status, state="disabled")

        self.button_check_ver = Button(buttonframe, width=14, text="SW FW Checking", bg="white", command=self.check_version)
        self.main_version = StringVar()
        self.entry_show_ver = Entry(buttonframe, width=15, textvariable=self.main_version, state="disabled")

        # Serial Control Place
        serialframe.grid(row=0, column=0, rowspan=12, padx=5, pady=5)
        serial_title.grid(row=0, column=0, columnspan=12, sticky=NW, pady=2)
        self.btn_serial_start.grid(row=1, column=0,  sticky=W, pady=2, padx=2)
        self.btn_serial_stop.grid(row=1, column=1,  sticky=W, pady=2, padx=2)
        self.serial_port_lable.grid(row=1, column=3, sticky=E, pady=2, padx=2)
        self.serial_port_vaule.grid(row=1, column=4, sticky=W, pady=2, padx=2)
        self.label_serial_baud.grid(row=1, column=6,  sticky=E, pady=2, padx=2)
        self.serial_baud.grid(row=1, column=7, sticky=W, pady=2, padx=2)

        self.serial_log_lable.grid(row=2, column=0, columnspan=2, sticky=NW, pady=2)
        self.serial_log_entry.grid(row=2, column=2, columnspan=6, sticky=NW, pady=2)
        self.serial_log_button.grid(row=2, column=10, columnspan=2, sticky=NE, pady=2)
        self.serialtext.grid(row=3, column=0, columnspan=11, rowspan=11, sticky=NW)

        # Controlbox Control Place
        buttonframe.grid(row=0, column=1, padx=5, pady=5)
        button_title.grid(row=0, column=1, columnspan=4, sticky=NW, pady=2)
        self.label_port.grid(row=1, column=0, columnspan=2, stick=NW, pady=2)
        self.port_value.grid(row=1, column=2, columnspan=2, stick=NW, pady=2)
        self.label_baud.grid(row=2, column=0, columnspan=2, stick=NW, pady=2)
        self.baud_value.grid(row=2, column=2, columnspan=2, stick=NW, pady=2)
        self.p3v3.grid(row=3, column=0, columnspan=2, sticky=NW, pady=2)
        self.entry_p3v3_vol.grid(row=3, column=2, columnspan=2, sticky=NW, pady=2)
        self.p3v3aux.grid(row=4, column=0, columnspan=2, sticky=W, pady=2)
        self.entry_p3v3aux_val.grid(row=4, column=2, columnspan=2, sticky=NW, pady=2)

        self.button_ac_on.grid(row=5, column=0, columnspan=2, sticky=NW, pady=2)
        self.button_ac_off.grid(row=5, column=2, columnspan=2, sticky=NW, pady=2)
        self.button_dc_on.grid(row=6, column=0, columnspan=2, sticky=NW, pady=2)
        self.button_dc_off.grid(row=6, column=2, columnspan=2, sticky=NW, pady=2)
        self.button_reset.grid(row=7, column=0, columnspan=2, sticky=NW, pady=2)
        self.button_usb_open.grid(row=7, column=2, columnspan=2, sticky=NW, pady=2)
        self.button_usb_host.grid(row=8, column=0, columnspan=2, sticky=NW, pady=2)
        self.button_usb_sut.grid(row=8, column=2, columnspan=2, sticky=NW, pady=2)
        self.button_voltage.grid(row=9, column=0, columnspan=2, sticky=NW, pady=2)
        self.button_jumper.grid(row=9, column=2, columnspan=2, sticky=NW, pady=2)
        self.button_power_list.grid(row=10, column=0, columnspan=2, sticky=NW, pady=2)
        self.entry_power_status.grid(row=10, column=2, columnspan=2, sticky=E, padx=1, pady=2)
        self.button_check_ver.grid(row=11, column=0, columnspan=2, stick=NW, pady=2)
        self.entry_show_ver.grid(row=11, column=2, columnspan=2, stick=E, padx=1, pady=2)
        self.button_text.grid(row=12, column=0, columnspan=4, sticky=NW, pady=4)

    def run_gui(self):
        self.root.mainloop()


class JumperSetting(Toplevel):

    def __init__(self, parent):
        super(JumperSetting, self).__init__()
        self.parent = parent
        self.title('Jumper Setting')
        self.geometry('466x274')
        self.resizable()
        self.resizable(width=False, height=False)
        self['background'] = "azure2"

        jmpframe = Frame(self, width=29, height=120, bd=5, bg='white')
        jmp_title = Label(jmpframe, width=29, text="Connect 1-2", bg='azure3', fg='Yellow',
                             font=("Times", "10", "bold italic"))
        jmpframe2 = Frame(self, width=29, height=120, bd=5, bg='white')
        jmp_title2 = Label(jmpframe2, width=29, text="Connect 2-3", bg='azure3', fg='Yellow',
                             font=("Times", "10", "bold italic"))

        # Button
        self.dp_out_1_A = Button(jmpframe, width=12, text="DP_OUT_1", command=self.enable_dp_out_1)
        self.dp_out_2_A = Button(jmpframe, width=12, text="DP_OUT_2", command=self.enable_dp_out_2)
        self.dp_out_3_A = Button(jmpframe, width=12, text="DP_OUT_3", command=self.enable_dp_out_3)
        self.dp_out_4_A = Button(jmpframe, width=12, text="DP_OUT_4", command=self.enable_dp_out_4)
        self.dp_out_5_A = Button(jmpframe, width=12, text="DP_OUT_5", command=self.enable_dp_out_5)
        self.dp_out_6_A = Button(jmpframe, width=12, text="DP_OUT_6", command=self.enable_dp_out_6)
        self.dp_out_7_A = Button(jmpframe, width=12, text="DP_OUT_7", command=self.enable_dp_out_7)
        self.dp_out_8_A = Button(jmpframe, width=12, text="DP_OUT_8", command=self.enable_dp_out_8)
        self.dp_out_9_A = Button(jmpframe, width=12, text="DP_OUT_9", command=self.enable_dp_out_9)
        self.dp_out_10_A = Button(jmpframe, width=12, text="DP_OUT_10", command=self.enable_dp_out_10)
        self.dp_out_11_A = Button(jmpframe, width=12, text="DP_OUT_11", command=self.enable_dp_out_11)
        self.dp_out_12_A = Button(jmpframe, width=12, text="DP_OUT_12", command=self.enable_dp_out_12)

        self.dp_out_1_B = Button(jmpframe2, width=12, text="DP_OUT_1", command=self.disable_dp_out_1)
        self.dp_out_2_B = Button(jmpframe2, width=12, text="DP_OUT_2", command=self.disable_dp_out_2)
        self.dp_out_3_B = Button(jmpframe2, width=12, text="DP_OUT_3", command=self.disable_dp_out_3)
        self.dp_out_4_B = Button(jmpframe2, width=12, text="DP_OUT_4", command=self.disable_dp_out_4)
        self.dp_out_5_B = Button(jmpframe2, width=12, text="DP_OUT_5", command=self.disable_dp_out_5)
        self.dp_out_6_B = Button(jmpframe2, width=12, text="DP_OUT_6", command=self.disable_dp_out_6)
        self.dp_out_7_B = Button(jmpframe2, width=12, text="DP_OUT_7", command=self.disable_dp_out_7)
        self.dp_out_8_B = Button(jmpframe2, width=12, text="DP_OUT_8", command=self.disable_dp_out_8)
        self.dp_out_9_B = Button(jmpframe2, width=12, text="DP_OUT_9", command=self.disable_dp_out_9)
        self.dp_out_10_B = Button(jmpframe2, width=12, text="DP_OUT_10", command=self.disable_dp_out_10)
        self.dp_out_11_B = Button(jmpframe2, width=12, text="DP_OUT_11", command=self.disable_dp_out_11)
        self.dp_out_12_B = Button(jmpframe2, width=12, text="DP_OUT_12", command=self.disable_dp_out_12)

        # Grid
        jmpframe.grid(row=0, column=0, rowspan=2, padx=5, pady=5)
        jmp_title.grid(row=0, column=0, columnspan=6, sticky=NW, pady=2)
        self.dp_out_1_A.grid(row=1, column=0, sticky=NW, padx=6, pady=4)
        self.dp_out_2_A.grid(row=1, column=1, sticky=NW, padx=6, pady=4)
        self.dp_out_3_A.grid(row=2, column=0, sticky=NW, padx=6, pady=4)
        self.dp_out_4_A.grid(row=2, column=1, sticky=NW, padx=6, pady=4)
        self.dp_out_5_A.grid(row=3, column=0, sticky=NW, padx=6, pady=4)
        self.dp_out_6_A.grid(row=3, column=1, sticky=NW, padx=6, pady=4)
        self.dp_out_7_A.grid(row=4, column=0, sticky=NW, padx=6, pady=4)
        self.dp_out_8_A.grid(row=4, column=1, sticky=NW, padx=6, pady=4)
        self.dp_out_9_A.grid(row=5, column=0, sticky=NW, padx=6, pady=4)
        self.dp_out_10_A.grid(row=5, column=1, sticky=NW, padx=6, pady=4)
        self.dp_out_11_A.grid(row=6, column=0, sticky=NW, padx=6, pady=4)
        self.dp_out_12_A.grid(row=6, column=1, sticky=NW, padx=6, pady=4)

        jmpframe2.grid(row=0, column=1, rowspan=2, padx=5, pady=5)
        jmp_title2.grid(row=0, column=0, columnspan=6, sticky=NW, pady=2)
        self.dp_out_1_B.grid(row=1, column=0, sticky=NW, padx=6, pady=4)
        self.dp_out_2_B.grid(row=1, column=1, sticky=NW, padx=6, pady=4)
        self.dp_out_3_B.grid(row=2, column=0, sticky=NW, padx=6, pady=4)
        self.dp_out_4_B.grid(row=2, column=1, sticky=NW, padx=6, pady=4)
        self.dp_out_5_B.grid(row=3, column=0, sticky=NW, padx=6, pady=4)
        self.dp_out_6_B.grid(row=3, column=1, sticky=NW, padx=6, pady=4)
        self.dp_out_7_B.grid(row=4, column=0, sticky=NW, padx=6, pady=4)
        self.dp_out_8_B.grid(row=4, column=1, sticky=NW, padx=6, pady=4)
        self.dp_out_9_B.grid(row=5, column=0, sticky=NW, padx=6, pady=4)
        self.dp_out_10_B.grid(row=5, column=1, sticky=NW, padx=6, pady=4)
        self.dp_out_11_B.grid(row=6, column=0, sticky=NW, padx=6, pady=4)
        self.dp_out_12_B.grid(row=6, column=1, sticky=NW, padx=6, pady=4)

    @deco
    def enable_dp_out_1(self):
        soundwave = SoundWave(port_entry_value.get(), baud_entry_value.get())
        cr = soundwave.ctr_fp_two_ways_switch(1, 0)
        res = 'Connect DP_OUT_1: {}'.format(cr)
        self.parent.button_text.insert(END, res, 'blue')
        self.parent.button_text.see(END)
        soundwave.close()

    @deco
    def disable_dp_out_1(self):
        soundwave = SoundWave(port_entry_value.get(), baud_entry_value.get())
        cr = soundwave.ctr_fp_two_ways_switch(1, 1)
        res = 'Connect DP_OUT_1: {}\n'.format(cr)
        self.parent.button_text.insert(END, res, 'blue')
        self.parent.button_text.see(END)
        soundwave.close()

    @deco
    def enable_dp_out_2(self):
        soundwave = SoundWave(port_entry_value.get(), baud_entry_value.get())
        cr = soundwave.ctr_fp_two_ways_switch(2, 0)
        res = 'Connect DP_OUT_2: {}\n'.format(cr)
        self.parent.button_text.insert(END, res, 'blue')
        self.parent.button_text.see(END)
        soundwave.close()

    @deco
    def disable_dp_out_2(self):
        soundwave = SoundWave(port_entry_value.get(), baud_entry_value.get())
        cr = soundwave.ctr_fp_two_ways_switch(2, 1)
        res = 'Disconnect DP_OUT_2: {}\n'.format(cr)
        self.parent.button_text.insert(END, res, 'blue')
        self.parent.button_text.see(END)
        soundwave.close()

    @deco
    def enable_dp_out_3(self):
        soundwave = SoundWave(port_entry_value.get(), baud_entry_value.get())
        cr = soundwave.ctr_fp_two_ways_switch(3, 0)
        res = 'Connect DP_OUT_3: {}\n'.format(cr)
        self.parent.button_text.insert(END, res, 'blue')
        self.parent.button_text.see(END)
        soundwave.close()

    @deco
    def disable_dp_out_3(self):
        soundwave = SoundWave(port_entry_value.get(), baud_entry_value.get())
        cr = soundwave.ctr_fp_two_ways_switch(3, 1)
        res = 'Disconnect DP_OUT_3: {}\n'.format(cr)
        self.parent.button_text.insert(END, res, 'blue')
        self.parent.button_text.see(END)
        soundwave.close()

    @deco
    def enable_dp_out_4(self):
        soundwave = SoundWave(port_entry_value.get(), baud_entry_value.get())
        cr = soundwave.ctr_fp_two_ways_switch(4, 0)
        res = 'Connect DP_OUT_4: {}\n'.format(cr)
        self.parent.button_text.insert(END, res, 'blue')
        self.parent.button_text.see(END)
        soundwave.close()

    @deco
    def disable_dp_out_4(self):
        soundwave = SoundWave(port_entry_value.get(), baud_entry_value.get())
        cr = soundwave.ctr_fp_two_ways_switch(4, 1)
        res = 'Disconnect DP_OUT_4: {}\n'.format(cr)
        self.parent.button_text.insert(END, res, 'blue')
        self.parent.button_text.see(END)
        soundwave.close()

    @deco
    def enable_dp_out_5(self):
        soundwave = SoundWave(port_entry_value.get(), baud_entry_value.get())
        cr = soundwave.ctr_fp_two_ways_switch(5, 0)
        res = 'Connect DP_OUT_5: {}\n'.format(cr)
        self.parent.button_text.insert(END, res, 'blue')
        self.parent.button_text.see(END)
        soundwave.close()

    @deco
    def disable_dp_out_5(self):
        soundwave = SoundWave(port_entry_value.get(), baud_entry_value.get())
        cr = soundwave.ctr_fp_two_ways_switch(5, 1)
        res = 'Disconnect DP_OUT_5: {}\n'.format(cr)
        self.parent.button_text.insert(END, res, 'blue')
        self.parent.button_text.see(END)
        soundwave.close()

    @deco
    def enable_dp_out_6(self):
        soundwave = SoundWave(port_entry_value.get(), baud_entry_value.get())
        cr = soundwave.ctr_fp_two_ways_switch(6, 0)
        res = 'Connect DP_OUT_6: {}\n'.format(cr)
        self.parent.button_text.insert(END, res, 'blue')
        self.parent.button_text.see(END)
        soundwave.close()

    @deco
    def disable_dp_out_6(self):
        soundwave = SoundWave(port_entry_value.get(), baud_entry_value.get())
        cr = soundwave.ctr_fp_two_ways_switch(6, 1)
        res = 'Disconnect DP_OUT_6: {}\n'.format(cr)
        self.parent.button_text.insert(END, res, 'blue')
        self.parent.button_text.see(END)
        soundwave.close()

    @deco
    def enable_dp_out_7(self):
        soundwave = SoundWave(port_entry_value.get(), baud_entry_value.get())
        cr = soundwave.ctr_fp_two_ways_switch(7, 0)
        res = 'Connect DP_OUT_7: {}\n'.format(cr)
        self.parent.button_text.insert(END, res, 'blue')
        self.parent.button_text.see(END)
        soundwave.close()

    @deco
    def disable_dp_out_7(self):
        soundwave = SoundWave(port_entry_value.get(), baud_entry_value.get())
        cr = soundwave.ctr_fp_two_ways_switch(7, 1)
        res = 'Disconnect DP_OUT_7: {}\n'.format(cr)
        self.parent.button_text.insert(END, res, 'blue')
        self.parent.button_text.see(END)
        soundwave.close()

    @deco
    def enable_dp_out_8(self):
        soundwave = SoundWave(port_entry_value.get(), baud_entry_value.get())
        cr = soundwave.ctr_fp_two_ways_switch(8, 0)
        res = 'Connect DP_OUT_8: {}\n'.format(cr)
        self.parent.button_text.insert(END, res, 'blue')
        self.parent.button_text.see(END)
        soundwave.close()

    @deco
    def disable_dp_out_8(self):
        soundwave = SoundWave(port_entry_value.get(), baud_entry_value.get())
        cr = soundwave.ctr_fp_two_ways_switch(8, 1)
        res = 'Disconnect DP_OUT_8: {}\n'.format(cr)
        self.parent.button_text.insert(END, res, 'blue')
        self.parent.button_text.see(END)
        soundwave.close()

    @deco
    def enable_dp_out_9(self):
        soundwave = SoundWave(port_entry_value.get(), baud_entry_value.get())
        cr = soundwave.ctr_fp_two_ways_switch(9, 0)
        res = 'Connect DP_OUT_9: {}\n'.format(cr)
        self.parent.button_text.insert(END, res, 'blue')
        self.parent.button_text.see(END)
        soundwave.close()

    @deco
    def disable_dp_out_9(self):
        soundwave = SoundWave(port_entry_value.get(), baud_entry_value.get())
        cr = soundwave.ctr_fp_two_ways_switch(9, 1)
        res = 'Disconnect DP_OUT_9: {}\n'.format(cr)
        self.parent.button_text.insert(END, res, 'blue')
        self.parent.button_text.see(END)
        soundwave.close()

    @deco
    def enable_dp_out_10(self):
        soundwave = SoundWave(port_entry_value.get(), baud_entry_value.get())
        cr = soundwave.ctr_fp_two_ways_switch(10, 0)
        res = 'Connect DP_OUT_10: {}\n'.format(cr)
        self.parent.button_text.insert(END, res, 'blue')
        self.parent.button_text.see(END)
        soundwave.close()

    @deco
    def disable_dp_out_10(self):
        soundwave = SoundWave(port_entry_value.get(), baud_entry_value.get())
        cr = soundwave.ctr_fp_two_ways_switch(10, 1)
        res = 'Disconnect DP_OUT_10: {}\n'.format(cr)
        self.parent.button_text.insert(END, res, 'blue')
        self.parent.button_text.see(END)
        soundwave.close()

    @deco
    def enable_dp_out_11(self):
        soundwave = SoundWave(port_entry_value.get(), baud_entry_value.get())
        cr = soundwave.ctr_fp_two_ways_switch(11, 0)
        res = 'Connect DP_OUT_11: {}\n'.format(cr)
        self.parent.button_text.insert(END, res, 'blue')
        self.parent.button_text.see(END)
        soundwave.close()

    @deco
    def disable_dp_out_11(self):
        soundwave = SoundWave(port_entry_value.get(), baud_entry_value.get())
        cr = soundwave.ctr_fp_two_ways_switch(11, 1)
        res = 'Disconnect DP_OUT_11: {}\n'.format(cr)
        self.parent.button_text.insert(END, res, 'blue')
        self.parent.button_text.see(END)
        soundwave.close()

    @deco
    def enable_dp_out_12(self):
        soundwave = SoundWave(port_entry_value.get(), baud_entry_value.get())
        cr = soundwave.ctr_fp_two_ways_switch(12, 0)
        res = 'Connect DP_OUT_12: {}\n'.format(cr)
        self.parent.button_text.insert(END, res, 'blue')
        self.parent.button_text.see(END)
        soundwave.close()

    @deco
    def disable_dp_out_12(self):
        soundwave = SoundWave(port_entry_value.get(), baud_entry_value.get())
        cr = soundwave.ctr_fp_two_ways_switch(12, 1)
        res = 'Disconnect DP_OUT_12: {}\n'.format(cr)
        self.parent.button_text.insert(END, res, 'blue')
        self.parent.button_text.see(END)
        soundwave.close()


class Voltage(Toplevel):

    def __init__(self, parent):
        super(Voltage, self).__init__()
        self.parent = parent
        self.title('Soundwave Voltage')
        self.geometry('815x312')
        self.resizable(width=False, height=False)
        self["background"] = "azure2"

        voltageframe = Frame(self, width=800, height=580, bd=5, bg='white')
        voltageframe.grid(row=0, column=0, rowspan=9, padx=10, pady=10)

        # control button
        self.button_start = Button(voltageframe, width=8, text="Start", bg="white", command=self.get_all_voltage)
        self.button_stop = Button(voltageframe, width=8, text="Stop", bg="white", command=self.stop_get_vol)
        self.button_start.grid(row=9, column=1, sticky=NW, padx=15, pady=4)
        self.button_stop.grid(row=9, column=3, sticky=NW, padx=15, pady=4)

        # PIN Name
        in1 = Label(voltageframe, width=8, text="AD_IN_1", anchor=NW)
        in2 = Label(voltageframe, width=8, text="AD_IN_2", anchor=NW)
        in3 = Label(voltageframe, width=8, text="AD_IN_3", anchor=NW)
        in4 = Label(voltageframe, width=8, text="AD_IN_4", anchor=NW)
        in5 = Label(voltageframe, width=8, text="AD_IN_5", anchor=NW)
        in6 = Label(voltageframe, width=8, text="AD_IN_6", anchor=NW)
        in7 = Label(voltageframe, width=8, text="AD_IN_7", anchor=NW)
        in8 = Label(voltageframe, width=8, text="AD_IN_8", anchor=NW)
        in9 = Label(voltageframe, width=8, text="AD_IN_9", anchor=NW)
        in10 = Label(voltageframe, width=8, text="AD_IN_10", anchor=NW)
        in11 = Label(voltageframe, width=8, text="AD_IN_11", anchor=NW)
        in12 = Label(voltageframe, width=8, text="AD_IN_12", anchor=NW)
        in13 = Label(voltageframe, width=8, text="AD_IN_13", anchor=NW)
        in14 = Label(voltageframe, width=8, text="AD_IN_14", anchor=NW)
        in15 = Label(voltageframe, width=8, text="AD_IN_15", anchor=NW)
        in16 = Label(voltageframe, width=8, text="AD_IN_16", anchor=NW)
        in17 = Label(voltageframe, width=8, text="AD_IN_17", anchor=NW)
        in18 = Label(voltageframe, width=8, text="AD_IN_18", anchor=NW)
        in19 = Label(voltageframe, width=8, text="AD_IN_19", anchor=NW)
        in20 = Label(voltageframe, width=8, text="AD_IN_20", anchor=NW)
        in21 = Label(voltageframe, width=8, text="AD_IN_21", anchor=NW)
        in22 = Label(voltageframe, width=8, text="AD_IN_22", anchor=NW)
        in23 = Label(voltageframe, width=8, text="AD_IN_23", anchor=NW)
        in24 = Label(voltageframe, width=8, text="AD_IN_24", anchor=NW)
        in25 = Label(voltageframe, width=8, text="AD_IN_25", anchor=NW)
        in26 = Label(voltageframe, width=8, text="AD_IN_26", anchor=NW)
        in27 = Label(voltageframe, width=8, text="AD_IN_27", anchor=NW)
        in28 = Label(voltageframe, width=8, text="AD_IN_28", anchor=NW)
        in29 = Label(voltageframe, width=8, text="AD_IN_29", anchor=NW)
        in30 = Label(voltageframe, width=8, text="AD_IN_30", anchor=NW)
        in31 = Label(voltageframe, width=8, text="AD_IN_31", anchor=NW)
        in32 = Label(voltageframe, width=8, text="AD_IN_32", anchor=NW)
        in33 = Label(voltageframe, width=8, text="AD_IN_33", anchor=NW)
        in34 = Label(voltageframe, width=8, text="AD_IN_34", anchor=NW)
        in35 = Label(voltageframe, width=8, text="AD_IN_35", anchor=NW)
        in36 = Label(voltageframe, width=8, text="AD_IN_36", anchor=NW)
        in37 = Label(voltageframe, width=8, text="AD_IN_37", anchor=NW)
        in38 = Label(voltageframe, width=8, text="AD_IN_38", anchor=NW)
        in39 = Label(voltageframe, width=8, text="AD_IN_39", anchor=NW)
        in40 = Label(voltageframe, width=8, text="AD_IN_40", anchor=NW)

        # Pin grid
        in1.grid(row=1, column=1, sticky=NW, padx=15, pady=4)
        in2.grid(row=1, column=3, sticky=NW, padx=15, pady=4)
        in3.grid(row=1, column=5, sticky=NW, padx=15, pady=4)
        in4.grid(row=1, column=7, sticky=NW, padx=15, pady=4)
        in5.grid(row=1, column=9, sticky=NW, padx=15, pady=4)
        in6.grid(row=2, column=1, sticky=NW, padx=15, pady=4)
        in7.grid(row=2, column=3, sticky=NW, padx=15, pady=4)
        in8.grid(row=2, column=5, sticky=NW, padx=15, pady=4)
        in9.grid(row=2, column=7, sticky=NW, padx=15, pady=4)
        in10.grid(row=2, column=9, sticky=NW, padx=15, pady=4)
        in11.grid(row=3, column=1, sticky=NW, padx=15, pady=4)
        in12.grid(row=3, column=3, sticky=NW, padx=15, pady=4)
        in13.grid(row=3, column=5, sticky=NW, padx=15, pady=4)
        in14.grid(row=3, column=7, sticky=NW, padx=15, pady=4)
        in15.grid(row=3, column=9, sticky=NW, padx=15, pady=4)
        in16.grid(row=4, column=1, sticky=NW, padx=15, pady=4)
        in17.grid(row=4, column=3, sticky=NW, padx=15, pady=4)
        in18.grid(row=4, column=5, sticky=NW, padx=15, pady=4)
        in19.grid(row=4, column=7, sticky=NW, padx=15, pady=4)
        in20.grid(row=4, column=9, sticky=NW, padx=15, pady=4)
        in21.grid(row=5, column=1, sticky=NW, padx=15, pady=4)
        in22.grid(row=5, column=3, sticky=NW, padx=15, pady=4)
        in23.grid(row=5, column=5, sticky=NW, padx=15, pady=4)
        in24.grid(row=5, column=7, sticky=NW, padx=15, pady=4)
        in25.grid(row=5, column=9, sticky=NW, padx=15, pady=4)
        in26.grid(row=6, column=1, sticky=NW, padx=15, pady=4)
        in27.grid(row=6, column=3, sticky=NW, padx=15, pady=4)
        in28.grid(row=6, column=5, sticky=NW, padx=15, pady=4)
        in29.grid(row=6, column=7, sticky=NW, padx=15, pady=4)
        in30.grid(row=6, column=9, sticky=NW, padx=15, pady=4)
        in31.grid(row=7, column=1, sticky=NW, padx=15, pady=4)
        in32.grid(row=7, column=3, sticky=NW, padx=15, pady=4)
        in33.grid(row=7, column=5, sticky=NW, padx=15, pady=4)
        in34.grid(row=7, column=7, sticky=NW, padx=15, pady=4)
        in35.grid(row=7, column=9, sticky=NW, padx=15, pady=4)
        in36.grid(row=8, column=1, sticky=NW, padx=15, pady=4)
        in37.grid(row=8, column=3, sticky=NW, padx=15, pady=4)
        in38.grid(row=8, column=5, sticky=NW, padx=15, pady=4)
        in39.grid(row=8, column=7, sticky=NW, padx=15, pady=4)
        in40.grid(row=8, column=9, sticky=NW, padx=15, pady=4)

        # vol text
        self.pin1 = StringVar()
        self.pin2 = StringVar()
        self.pin3 = StringVar()
        self.pin4 = StringVar()
        self.pin5 = StringVar()
        self.pin6 = StringVar()
        self.pin7 = StringVar()
        self.pin8 = StringVar()
        self.pin9 = StringVar()
        self.pin10 = StringVar()
        self.pin11 = StringVar()
        self.pin12 = StringVar()
        self.pin13 = StringVar()
        self.pin14 = StringVar()
        self.pin15 = StringVar()
        self.pin16 = StringVar()
        self.pin17 = StringVar()
        self.pin18 = StringVar()
        self.pin19 = StringVar()
        self.pin20 = StringVar()
        self.pin21 = StringVar()
        self.pin22 = StringVar()
        self.pin23 = StringVar()
        self.pin24 = StringVar()
        self.pin25 = StringVar()
        self.pin26 = StringVar()
        self.pin27 = StringVar()
        self.pin28 = StringVar()
        self.pin29 = StringVar()
        self.pin30 = StringVar()
        self.pin31 = StringVar()
        self.pin32 = StringVar()
        self.pin33 = StringVar()
        self.pin34 = StringVar()
        self.pin35 = StringVar()
        self.pin36 = StringVar()
        self.pin37 = StringVar()
        self.pin38 = StringVar()
        self.pin39 = StringVar()
        self.pin40 = StringVar()

        text_in1 = Entry(voltageframe, width=8, text=self.pin1, state="disabled")
        text_in2 = Entry(voltageframe, width=8, text=self.pin2, state="disabled")
        text_in3 = Entry(voltageframe, width=8, text=self.pin3, state="disabled")
        text_in4 = Entry(voltageframe, width=8, text=self.pin4, state="disabled")
        text_in5 = Entry(voltageframe, width=8, text=self.pin5, state="disabled")
        text_in6 = Entry(voltageframe, width=8, text=self.pin6, state="disabled")
        text_in7 = Entry(voltageframe, width=8, text=self.pin7, state="disabled")
        text_in8 = Entry(voltageframe, width=8, text=self.pin8, state="disabled")
        text_in9 = Entry(voltageframe, width=8, text=self.pin9, state="disabled")
        text_in10 = Entry(voltageframe, width=8, text=self.pin10, state="disabled")
        text_in11 = Entry(voltageframe, width=8, text=self.pin11, state="disabled")
        text_in12 = Entry(voltageframe, width=8, text=self.pin12, state="disabled")
        text_in13 = Entry(voltageframe, width=8, text=self.pin13, state="disabled")
        text_in14 = Entry(voltageframe, width=8, text=self.pin14, state="disabled")
        text_in15 = Entry(voltageframe, width=8, text=self.pin15, state="disabled")
        text_in16 = Entry(voltageframe, width=8, text=self.pin16, state="disabled")
        text_in17 = Entry(voltageframe, width=8, text=self.pin17, state="disabled")
        text_in18 = Entry(voltageframe, width=8, text=self.pin18, state="disabled")
        text_in19 = Entry(voltageframe, width=8, text=self.pin19, state="disabled")
        text_in20 = Entry(voltageframe, width=8, text=self.pin20, state="disabled")
        text_in21 = Entry(voltageframe, width=8, text=self.pin21, state="disabled")
        text_in22 = Entry(voltageframe, width=8, text=self.pin22, state="disabled")
        text_in23 = Entry(voltageframe, width=8, text=self.pin23, state="disabled")
        text_in24 = Entry(voltageframe, width=8, text=self.pin24, state="disabled")
        text_in25 = Entry(voltageframe, width=8, text=self.pin25, state="disabled")
        text_in26 = Entry(voltageframe, width=8, text=self.pin26, state="disabled")
        text_in27 = Entry(voltageframe, width=8, text=self.pin27, state="disabled")
        text_in28 = Entry(voltageframe, width=8, text=self.pin28, state="disabled")
        text_in29 = Entry(voltageframe, width=8, text=self.pin29, state="disabled")
        text_in30 = Entry(voltageframe, width=8, text=self.pin30, state="disabled")
        text_in31 = Entry(voltageframe, width=8, text=self.pin31, state="disabled")
        text_in32 = Entry(voltageframe, width=8, text=self.pin32, state="disabled")
        text_in33 = Entry(voltageframe, width=8, text=self.pin33, state="disabled")
        text_in34 = Entry(voltageframe, width=8, text=self.pin34, state="disabled")
        text_in35 = Entry(voltageframe, width=8, text=self.pin35, state="disabled")
        text_in36 = Entry(voltageframe, width=8, text=self.pin36, state="disabled")
        text_in37 = Entry(voltageframe, width=8, text=self.pin37, state="disabled")
        text_in38 = Entry(voltageframe, width=8, text=self.pin38, state="disabled")
        text_in39 = Entry(voltageframe, width=8, text=self.pin39, state="disabled")
        text_in40 = Entry(voltageframe, width=8, text=self.pin40, state="disabled")

        # vol grid
        text_in1.grid(row=1, column=2, sticky=E, padx=2)
        text_in2.grid(row=1, column=4, sticky=E, padx=2)
        text_in3.grid(row=1, column=6, sticky=E, padx=2)
        text_in4.grid(row=1, column=8, sticky=E, padx=2)
        text_in5.grid(row=1, column=10, sticky=E, padx=2)
        text_in6.grid(row=2, column=2, sticky=E, padx=2)
        text_in7.grid(row=2, column=4, sticky=E, padx=2)
        text_in8.grid(row=2, column=6, sticky=E, padx=2)
        text_in9.grid(row=2, column=8, sticky=E, padx=2)
        text_in10.grid(row=2, column=10, sticky=E, padx=2)
        text_in11.grid(row=3, column=2, sticky=E, padx=2)
        text_in12.grid(row=3, column=4, sticky=E, padx=2)
        text_in13.grid(row=3, column=6, sticky=E, padx=2)
        text_in14.grid(row=3, column=8, sticky=E, padx=2)
        text_in15.grid(row=3, column=10, sticky=E, padx=2)
        text_in16.grid(row=4, column=2, sticky=E, padx=2)
        text_in17.grid(row=4, column=4, sticky=E, padx=2)
        text_in18.grid(row=4, column=6, sticky=E, padx=2)
        text_in19.grid(row=4, column=8, sticky=E, padx=2)
        text_in20.grid(row=4, column=10, sticky=E, padx=2)
        text_in21.grid(row=5, column=2, sticky=E, padx=2)
        text_in22.grid(row=5, column=4, sticky=E, padx=2)
        text_in23.grid(row=5, column=6, sticky=E, padx=2)
        text_in24.grid(row=5, column=8, sticky=E, padx=2)
        text_in25.grid(row=5, column=10, sticky=E, padx=2)
        text_in26.grid(row=6, column=2, sticky=E, padx=2)
        text_in27.grid(row=6, column=4, sticky=E, padx=2)
        text_in28.grid(row=6, column=6, sticky=E, padx=2)
        text_in29.grid(row=6, column=8, sticky=E, padx=2)
        text_in30.grid(row=6, column=10, sticky=E, padx=2)
        text_in31.grid(row=7, column=2, sticky=E, padx=2)
        text_in32.grid(row=7, column=4, sticky=E, padx=2)
        text_in33.grid(row=7, column=6, sticky=E, padx=2)
        text_in34.grid(row=7, column=8, sticky=E, padx=2)
        text_in35.grid(row=7, column=10, sticky=E, padx=2)
        text_in36.grid(row=8, column=2, sticky=E, padx=2)
        text_in37.grid(row=8, column=4, sticky=E, padx=2)
        text_in38.grid(row=8, column=6, sticky=E, padx=2)
        text_in39.grid(row=8, column=8, sticky=E, padx=2)
        text_in40.grid(row=8, column=10, sticky=E, padx=2)

    def get_all_voltage(self):
        soundwave = SoundWave(sw_port, sw_baud)
        vol_list = []
        for i in range(40):
            ret = soundwave.get_ad_values([i + 1])
            value = round(ret[0], 3)
            vol_list.append(value)

        self.pin1.set(vol_list[0])
        self.pin2.set(vol_list[1])
        self.pin3.set(vol_list[2])
        self.pin4.set(vol_list[3])
        self.pin5.set(vol_list[4])
        self.pin6.set(vol_list[5])
        self.pin7.set(vol_list[6])
        self.pin8.set(vol_list[7])
        self.pin9.set(vol_list[8])
        self.pin10.set(vol_list[9])
        self.pin11.set(vol_list[10])
        self.pin12.set(vol_list[11])
        self.pin13.set(vol_list[12])
        self.pin14.set(vol_list[13])
        self.pin15.set(vol_list[14])
        self.pin16.set(vol_list[15])
        self.pin17.set(vol_list[16])
        self.pin18.set(vol_list[17])
        self.pin19.set(vol_list[18])
        self.pin20.set(vol_list[19])
        self.pin21.set(vol_list[20])
        self.pin22.set(vol_list[21])
        self.pin23.set(vol_list[22])
        self.pin24.set(vol_list[23])
        self.pin25.set(vol_list[24])
        self.pin26.set(vol_list[25])
        self.pin27.set(vol_list[26])
        self.pin28.set(vol_list[27])
        self.pin29.set(vol_list[28])
        self.pin30.set(vol_list[29])
        self.pin31.set(vol_list[30])
        self.pin32.set(vol_list[31])
        self.pin33.set(vol_list[32])
        self.pin34.set(vol_list[33])
        self.pin35.set(vol_list[34])
        self.pin36.set(vol_list[35])
        self.pin37.set(vol_list[36])
        self.pin38.set(vol_list[37])
        self.pin39.set(vol_list[38])
        self.pin40.set(vol_list[39])
        self.button_stop["background"] = "White"
        self.button_start["background"] = "DarkOliveGreen3"
        global count
        count = self.button_start.after(1000, self.get_all_voltage)

    def stop_get_vol(self):
        self.pin1.set("")
        self.pin2.set("")
        self.pin3.set("")
        self.pin4.set("")
        self.pin5.set("")
        self.pin6.set("")
        self.pin7.set("")
        self.pin8.set("")
        self.pin9.set("")
        self.pin10.set("")
        self.pin11.set("")
        self.pin12.set("")
        self.pin13.set("")
        self.pin14.set("")
        self.pin15.set("")
        self.pin16.set("")
        self.pin17.set("")
        self.pin18.set("")
        self.pin19.set("")
        self.pin20.set("")
        self.pin21.set("")
        self.pin22.set("")
        self.pin23.set("")
        self.pin24.set("")
        self.pin25.set("")
        self.pin26.set("")
        self.pin27.set("")
        self.pin28.set("")
        self.pin29.set("")
        self.pin30.set("")
        self.pin31.set("")
        self.pin32.set("")
        self.pin33.set("")
        self.pin34.set("")
        self.pin35.set("")
        self.pin36.set("")
        self.pin37.set("")
        self.pin38.set("")
        self.pin39.set("")
        self.pin40.set("")
        self.button_start.after_cancel(count)
        self.button_start["background"] = "White"
        self.button_stop["background"] = "DarkOliveGreen3"


def main():
    power_action = Power_Action()
    power_action.run_gui()
    print("exit process")


if __name__ == "__main__":
    main()

