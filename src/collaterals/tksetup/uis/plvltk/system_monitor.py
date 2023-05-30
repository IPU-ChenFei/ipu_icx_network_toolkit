#!/usr/bin/env python

from tkinter import *
import threading

# def __



def start_power_state_detect(label):
    print('start power state detect')
    label['text'] = 'S5'


def stop_power_state_detect(label):
    print('stop power state detect')
    label['text'] = 'G3'


def start_post_code_detect(label):
    print('start post code detect')
    label['text'] = '00'


def stop_post_code_detect(label):
    print('stop post code detect')
    label['text'] = 'EF'

