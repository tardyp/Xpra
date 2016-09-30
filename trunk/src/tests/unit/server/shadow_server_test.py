#!/usr/bin/env python
# This file is part of Xpra.
# Copyright (C) 2016 Antoine Martin <antoine@devloop.org.uk>
# Xpra is released under the terms of the GNU GPL v2, or, at your option, any
# later version. See the file COPYING for details.

import time
import unittest
from ..server_test_util import ServerTestUtil


class ShadowServerTest(ServerTestUtil):

	def test_shadow_start_stop(self):
		display = self.find_free_display()
		xvfb = self.start_Xvfb(display)
		time.sleep(1)
		assert display in self.find_X11_displays()
		#start server using this display:
		server = self.check_server("shadow", display)
		self.check_stop_server(server, "stop", display)
		time.sleep(1)
		assert self.pollwait(xvfb, 2) is None, "the Xvfb should not have been killed by xpra shutting down!"
		xvfb.terminate()


def main():
	unittest.main()


if __name__ == '__main__':
	main()
