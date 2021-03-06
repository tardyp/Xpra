# -*- coding: utf-8 -*-
# This file is part of Xpra.
# Copyright (C) 2010-2019 Antoine Martin <antoine@xpra.org>
# Xpra is released under the terms of the GNU GPL v2, or, at your option, any
# later version. See the file COPYING for details.

import os

from xpra.server.source.stub_source_mixin import StubSourceMixin


"""
Expose the ClientConnection using a dbus service
"""
class DBUS_Mixin(StubSourceMixin):

    def __init__(self):
        self.dbus_control = False
        self.dbus_server = None

    def init_from(self, _protocol, server):
        self.dbus_control = server.dbus_control

    def init_state(self):
        if self.dbus_control:
            from xpra.server.dbus.dbus_common import dbus_exception_wrap
            def make_dbus_server():
                from xpra.server.dbus.dbus_source import DBUS_Source
                return DBUS_Source(self, os.environ.get("DISPLAY", "").lstrip(":"))
            self.dbus_server = dbus_exception_wrap(make_dbus_server, "setting up client dbus instance")

    def cleanup(self):
        ds = self.dbus_server
        if ds:
            self.dbus_server = None
            self.idle_add(ds.cleanup)
