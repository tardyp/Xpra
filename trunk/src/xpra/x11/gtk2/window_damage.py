# This file is part of Xpra.
# Copyright (C) 2008, 2009 Nathaniel Smith <njs@pobox.com>
# Copyright (C) 2012-2016 Antoine Martin <antoine@devloop.org.uk>
# Xpra is released under the terms of the GNU GPL v2, or, at your option, any
# later version. See the file COPYING for details.

import os
from xpra.log import Logger
log = Logger("x11", "window")

from xpra.gtk_common.gobject_util import one_arg_signal
from xpra.x11.gtk2.gdk_bindings import (
            add_event_receiver,             #@UnresolvedImport
            remove_event_receiver,          #@UnresolvedImport
            )
from xpra.gtk_common.error import trap, xsync, XError

from xpra.x11.bindings.ximage import XImageBindings #@UnresolvedImport
XImage = XImageBindings()
from xpra.x11.bindings.window_bindings import constants, X11WindowBindings #@UnresolvedImport
X11Window = X11WindowBindings()
X11Window.ensure_XDamage_support()


StructureNotifyMask = constants["StructureNotifyMask"]
USE_XSHM = os.environ.get("XPRA_XSHM", "1")=="1"


class WindowDamageHandler(object):

    XShmEnabled = USE_XSHM

    __common_gsignals__ = {
        "xpra-damage-event"     : one_arg_signal,
        "xpra-unmap-event"      : one_arg_signal,
        "xpra-configure-event"  : one_arg_signal,
        "xpra-reparent-event"   : one_arg_signal,
        }

    # This may raise XError.
    def __init__(self, client_window, use_xshm=USE_XSHM):
        log("WindowDamageHandler.__init__(%#x, %s, %s)", client_window.xid)
        self.client_window = client_window
        self._use_xshm = use_xshm
        self._damage_handle = None
        self._shm_handle = None
        self._contents_handle = None
        self._border_width = 0

    def __repr__(self):
        xid = None
        if self.client_window:
            xid = self.client_window.xid
        return "WindowDamageHandler(%#x)" % xid

    def setup(self):
        self.invalidate_pixmap()
        xid = self.client_window.xid
        self._border_width = X11Window.geometry_with_border(xid)[-1]
        self._damage_handle = X11Window.XDamageCreate(xid)
        log("damage handle(%#x)=%#x", xid, self._damage_handle)
        add_event_receiver(self.client_window, self)

    def destroy(self):
        if self.client_window is None:
            log.warn("damage window handler for %s already cleaned up!", self)
            return
        #clear the reference to the window early:
        win = self.client_window
        self.client_window = None
        self.do_destroy(win)

    def do_destroy(self, win):
        remove_event_receiver(win, self)
        self.invalidate_pixmap()
        dh = self._damage_handle
        if dh:
            self._damage_handle = None
            trap.swallow_synced(X11Window.XDamageDestroy, dh)
        sh = self._shm_handle
        if sh:
            self._shm_handle = None
            sh.cleanup()
        #note: this should be redundant since we cleared the
        #reference to self.client_window and shortcut out in do_get_property_contents_handle
        #but it's cheap anyway
        self.invalidate_pixmap()

    def acknowledge_changes(self):
        sh = self._shm_handle
        if sh:
            sh.discard()
        dh = self._damage_handle
        if dh and self.client_window:
            #"Synchronously modifies the regions..." so unsynced?
            if not trap.swallow_synced(X11Window.XDamageSubtract, dh):
                self.invalidate_pixmap()

    def invalidate_pixmap(self):
        log("invalidating named pixmap")
        ch = self._contents_handle
        if ch:
            self._contents_handle = None
            ch.cleanup()

    def get_shm_handle(self):
        if not self._use_xshm or not WindowDamageHandler.XShmEnabled:
            return None
        if self._shm_handle and self._shm_handle.get_size()!=self.client_window.get_size():
            #size has changed!
            #make sure the current wrapper gets garbage collected:
            self._shm_handle.cleanup()
            self._shm_handle = None
        if self._shm_handle is None:
            #make a new one:
            self._shm_handle = XImage.get_XShmWrapper(self.client_window.xid)
            if self._shm_handle is None:
                #failed (may retry)
                return None
            init_ok, retry_window, xshm_failed = self._shm_handle.setup()
            if not init_ok:
                #this handle is not valid, clear it:
                self._shm_handle = None
            if not retry_window:
                #and it looks like it is not worth re-trying this window:
                self._use_xshm = False
            if xshm_failed:
                log.warn("Warning: disabling XShm support following irrecoverable error")
                WindowDamageHandler.XShmEnabled = False
        return self._shm_handle

    def _set_pixmap(self):
        self._contents_handle = XImage.get_xwindow_pixmap_wrapper(self.client_window.xid)

    def get_contents_handle(self):
        if not self.client_window:
            #shortcut out
            return None
        if self._contents_handle is None:
            log("refreshing named pixmap")
            assert self._listening_to is None
            trap.swallow_synced(self._set_pixmap)
        return self._contents_handle


    def get_image(self, x, y, width, height, logger=log.debug):
        handle = self.get_contents_handle()
        if handle is None:
            logger("get_image(..) pixmap is None for window %#x", self.client_window.xid)
            return None

        #try XShm:
        try:
            shm = self.get_shm_handle()
            #logger("get_image(..) XShm handle: %s, handle=%s, pixmap=%s", shm, handle, handle.get_pixmap())
            if shm is not None:
                with xsync:
                    shm_image = shm.get_image(handle.get_pixmap(), x, y, width, height)
                #logger("get_image(..) XShm image: %s", shm_image)
                if shm_image:
                    return shm_image
        except Exception as e:
            if type(e)==XError and e.msg=="BadMatch":
                logger("get_image(%s, %s, %s, %s) get_image BadMatch ignored (window already gone?)", x, y, width, height)
            else:
                log.warn("get_image(%s, %s, %s, %s) get_image %s", x, y, width, height, e, exc_info=True)

        try:
            w = min(handle.get_width(), width)
            h = min(handle.get_height(), height)
            if w!=width or h!=height:
                logger("get_image(%s, %s, %s, %s) clamped to pixmap dimensions: %sx%s", x, y, width, height, w, h)
            with xsync:
                return handle.get_image(x, y, w, h)
        except Exception as e:
            if type(e)==XError and e.msg=="BadMatch":
                logger("get_image(%s, %s, %s, %s) get_image BadMatch ignored (window already gone?)", x, y, width, height)
            else:
                log.warn("get_image(%s, %s, %s, %s) get_image %s", x, y, width, height, e, exc_info=True)
            return None


    def do_xpra_damage_event(self, event):
        raise NotImplementedError()

    def do_xpra_reparent_event(self, event):
        self.invalidate_pixmap()

    def xpra_unmap_event(self, event):
        self.invalidate_pixmap()

    def do_xpra_configure_event(self, event):
        self._border_width = event.border_width
        self.invalidate_pixmap()
