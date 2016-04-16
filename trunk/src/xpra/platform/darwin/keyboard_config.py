# coding=utf8
# This file is part of Xpra.
# Copyright (C) 2014 Antoine Martin <antoine@devloop.org.uk>
# Xpra is released under the terms of the GNU GPL v2, or, at your option, any
# later version. See the file COPYING for details.

from xpra.log import Logger
log = Logger("keyboard", "osx")

from xpra.server.keyboard_config_base import KeyboardConfigBase


class KeyboardConfig(KeyboardConfigBase):

    def __init__(self):
        KeyboardConfigBase.__init__(self)

    def __repr__(self):
        return "osx.KeyboardConfig"


    def get_keycode(self, client_keycode, keyname, modifiers):
        global KEYCODES
        keycode = KEYCODES.get(keyname, -1)
        if keycode==-1:
            keycode = KEYCODES.get(keyname.upper(), -1)
        log("get_keycode%s=%s", (client_keycode, keyname, modifiers), keycode)
        return keycode

#we currently assume that all key events are sent using X11 names,
#so we need to translate them to osx keys
#this list has been generated using:
#$cat /Developer/Examples/Speech/Recognition/fauxTunes/Virtual\ Key\ Code\ Mappings.txt  | awk  '{print "            \""$1"\" : "$2$3","}'
KEYCODES = {
            #Standardkeys
            "A"     : 0,
            "B"     : 11,
            "C"     : 8,
            "D"     : 2,
            "E"     : 14,
            "F"     : 3,
            "G"     : 5,
            "H"     : 4,
            "I"     : 34,
            "J"     : 38,
            "K"     : 40,
            "L"     : 37,
            "M"     : 46,
            "N"     : 45,
            "O"     : 31,
            "P"     : 35,
            "Q"     : 12,
            "R"     : 15,
            "S"     : 1,
            "T"     : 17,
            "U"     : 32,
            "V"     : 9,
            "W"     : 13,
            "X"     : 7,
            "Y"     : 16,
            "Z"     : 6,
            "1"     : 18,
            "2"     : 19,
            "3"     : 20,
            "4"     : 21,
            "5"     : 23,
            "6"     : 22,
            "7"     : 26,
            "8"     : 28,
            "9"     : 25,
            "0"     : 29,
            "-"     : 27,
            "="     : 24,
            "["     : 33,
            "]"     : 30,
            "\\"    : 42,
            ";"     : 41,
            "'"     : 39,
            ","     : 43,
            "."     : 47,
            "/"     : 44,
            "Delete"    : 51,
            "Return"    : 35,
            "Tab"       : 48,
            "Caps_Lock" : 57,
            "space" : 9,
            #Numeric pad keys:
            "KP_1"  : 83,
            "KP_2"  : 84,
            "KP_3"  : 85,
            "KP_4"  : 86,
            "KP_5"  : 87,
            "KP_6"  : 88,
            "KP_7"  : 89,
            "KP_8"  : 91,
            "KP_9"  : 92,
            "KP_0"  : 82,
            "KP_Decimal" : 65,
            "equal" : 81,
            "KP_Divide"     : 75,
            "KP_Multiply"   : 67,
            "KP_Subtract"   : 78,
            "KP_Add"        : 69,
            "clear" : 71,
            "KP_Enter" : 76,
            #Navigation keys:
            "Down"  : 125,
            "Up"    : 126,
            "Right" : 124,
            "Left"  : 123,
            "Prior" : 116,  #Page Up
            "Next"  : 121,  #Page Down
            "Home"  : 115,
            "End"   : 119,
            "Insert" : 114,   #help
            "Delete" : 117,
            #Function keys:
            "F1" : 122,
            "F2" : 120,
            "F3" : 99,
            "F4" : 119,
            "F5" : 96,
            "F6" : 57,
            "F7" : 98,
            "F8" : 100,
            "F9" : 101,
            "F10" : 109,
            "F11" : 103,
            "F12" : 111,
            "F13" : 105,
            "F14" : 107,
            "F15" : 113,
            #Modifier keys:
            "Shift_L"   : 56,
            "Control_L" : 59,
            "Alt_L"     : 58,   #option
            "Super_L"   : 55,   #apple
            }

log("KEYCODES: %s", KEYCODES)
