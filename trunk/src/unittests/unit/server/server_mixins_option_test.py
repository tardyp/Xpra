#!/usr/bin/env python
# This file is part of Xpra.
# Copyright (C) 2018 Antoine Martin <antoine@devloop.org.uk>
# Xpra is released under the terms of the GNU GPL v2, or, at your option, any
# later version. See the file COPYING for details.

import time
import unittest
from collections import OrderedDict

from xpra.os_util import pollwait, OSX, POSIX, PYTHON2
from unit.server_test_util import ServerTestUtil, log


class ServerAuthTest(ServerTestUtil):

    @classmethod
    def setUpClass(cls):
        ServerTestUtil.setUpClass()
        cls.default_xpra_args = [
            "--systemd-run=no",
            "--pulseaudio=no",
            "--socket-dirs=/tmp",
            "--start=xterm",
            ]
        cls.display = None
        cls.xvfb = None
        cls.client_display = None
        cls.client_xvfb = None
        if True:
            #use a single display for the server that we recycle:
            cls.display = cls.find_free_display()
            cls.xvfb = cls.start_Xvfb(cls.display)
            time.sleep(1)
            assert cls.display in cls.find_X11_displays()
            log("ServerAuthTest.setUpClass() server display=%s, xvfb=%s", cls.display, cls.xvfb)
        if True:
            #display use by the client:
            cls.client_display = cls.find_free_display()
            cls.client_xvfb = cls.start_Xvfb(cls.client_display)
            log("ServerAuthTest.setUpClass() client display=%s, xvfb=%s", cls.client_display, cls.client_xvfb)


    @classmethod
    def tearDownClass(cls):
        ServerTestUtil.tearDownClass()
        if cls.xvfb:
            cls.xvfb.terminate()
        if cls.client_xvfb:
            cls.client_xvfb.terminate()

    def _test(self, options={}):
        log("starting test server with options=%s", options)
        args = ["--%s=%s" % (k,v) for k,v in options.items()]
        if self.display:
            display = self.display
            args.append("--use-display")
        else:
            display = self.find_free_display()
        log("args=%s", " ".join("'%s'" % x for x in args))
        server = self.check_start_server(display, *args)
        #we should always be able to get the version:
        client = self.run_xpra(["version", display])
        assert pollwait(client, 5)==0, "version client failed to connect to server with args=%s" % args
        #run info query:
        cmd = ["info", display]
        client = self.run_xpra(cmd)
        r = pollwait(client, 5)
        assert r==0, "info client failed and returned %s for server with args=%s" % (r, args)
        #connect a gui client:
        gui_client = None
        if self.client_display and self.client_xvfb:
            xpra_args = ["attach", display]
            gui_client = self.run_xpra(xpra_args, {"DISPLAY" : self.client_display})
            r = pollwait(gui_client, 5)
            if r is not None:
                log.warn("gui client stdout=%s", gui_client.stdout_file)
            assert r is None, "gui client terminated early and returned %i for server with args=%s" % (r, args)
        if self.display:
            self.check_stop_server(server, subcommand="exit", display=display)
        else:
            self.check_stop_server(server, subcommand="stop", display=display)
        if gui_client:
            r = pollwait(gui_client, 1)
            assert r is not None, "gui client should have been disconnected"

    def Xtest_nooptions(self):
        self._test()

    def Xtest_nonotifications(self):
        self._test({"notifications" : False})

    def test_all(self):
        OPTIONS = (
            "windows",
            "notifications",
            "webcam",
            "clipboard",
            "speaker",
            "microphone",
            "av-sync",
            "printing",
            "file-transfer",
            "mmap",
            "readonly",
            "dbus-proxy",
            "remote-logging",
            )
        #to test all:
        #TEST_VALUES = range(2**len(OPTIONS))
        #to test nothing disabled and everything disabled only:
        #TEST_VALUES = (0, 2**len(OPTIONS)-1)
        #test every option disabled individually:
        TEST_VALUES = tuple(2**i for i in range(len(OPTIONS)))
        for i in TEST_VALUES:
            options = OrderedDict()
            for o, option in enumerate(OPTIONS):
                options[option] = not bool((2**o) & i)
            log("test options for %i: %s", i, options)
            self._test(options)


def main():
    if POSIX and PYTHON2 and not OSX:
        unittest.main()


if __name__ == '__main__':
    main()