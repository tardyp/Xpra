#!/usr/bin/env python
# This file is part of Xpra.
# Copyright (C) 2016-2018 Antoine Martin <antoine@devloop.org.uk>
# Xpra is released under the terms of the GNU GPL v2, or, at your option, any
# later version. See the file COPYING for details.

import os

from xpra.os_util import osexpand, get_hex_uuid
from unit.server_test_util import ServerTestUtil, log

uq = 0

class X11ClientTestUtil(ServerTestUtil):

	def run_client(self, *args):
		client_display = self.find_free_display()
		xvfb = self.start_Xvfb(client_display)
		xvfb.display = client_display
		return xvfb, self.do_run_client(client_display, *args)

	def do_run_client(self, client_display, *args):
		from xpra.x11.vfb_util import xauth_add
		filename = osexpand(os.environ.get("XAUTHORITY", "~/.Xauthority"))
		xauth_data = get_hex_uuid()
		xauth_add(filename, client_display, xauth_data, os.getuid(), os.getgid())
		env = self.get_run_env()
		env["DISPLAY"] = client_display
		global uq
		env["XPRA_LOG_PREFIX"] = "client %i: " % uq
		uq +=1
		log("starting test client on Xvfb %s", client_display)
		return self.run_xpra(["attach"] + list(args) , env)
