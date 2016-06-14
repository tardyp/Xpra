# This file is part of Xpra.
# Copyright (C) 2016 Antoine Martin <antoine@devloop.org.uk>
# Xpra is released under the terms of the GNU GPL v2, or, at your option, any
# later version. See the file COPYING for details.

import os

from xpra.log import Logger
log = Logger("webcam")
from xpra.util import engs


def get_virtual_video_devices():
    log("get_virtual_video_devices")
    v4l2_virtual_dir = "/sys/devices/virtual/video4linux"
    if not os.path.exists(v4l2_virtual_dir) or not os.path.isdir(v4l2_virtual_dir):
        log.warn("Warning: webcam forwarding is disabled")
        log.warn(" the virtual video directory '%s' was not found", v4l2_virtual_dir)
        log.warn(" make sure that the 'v4l2loopback' kernel module is installed and loaded")
        return []
    contents = os.listdir(v4l2_virtual_dir)
    devices = {}
    try:
        from xpra.codecs.v4l2.pusher import query_video_device
    except ImportError:
        def query_video_device(device):
            return {}
    for f in contents:
        if not f.startswith("video"):
            continue
        try:
            no = int(f[len("video"):])
            assert no>=0
        except:
            continue
        dev_dir = os.path.join(v4l2_virtual_dir, f)
        if not os.path.isdir(dev_dir):
            continue
        dev_name = os.path.join(dev_dir, "name")
        try:
            name = open(dev_name).read().replace("\n", "")
            log("found %s: %s", f, name)
        except:
            continue
        dev_file = "/dev/%s" % f
        info = {"device" : dev_file}
        if name:
            info["card"] = name
        info.update(query_video_device(dev_file))
        devices[no] = info
    log("devices: %s", devices)
    log("found %i virtual video device%s", len(devices), engs(devices))
    return devices

def get_all_video_devices():
    contents = os.listdir("/dev")
    devices = {}
    device_paths = set()
    try:
        from xpra.codecs.v4l2.pusher import query_video_device
    except ImportError:
        def query_video_device(device):
            return {}
    for f in contents:
        if not f.startswith("video"):
            continue
        dev_file = "/dev/%s" % f
        try:
            dev_file = os.readlink(dev_file)
        except OSError:
            pass
        if dev_file in device_paths:
            continue
        device_paths.add(dev_file)
        try:
            no = int(f[len("video"):])
            assert no>=0
        except:
            continue
        info = {"device" : dev_file}
        info.update(query_video_device(dev_file))
        devices[no] = info
    return devices


_watch_manager = None
_notifier = None
_video_device_change_callbacks = []

def _video_device_file_filter(event):
    # return True to stop processing of event (to "stop chaining")
    return not event.pathname.startswith("/dev/video")

def _fire_video_device_change(create, pathname):
    global _video_device_change_callbacks
    for x in _video_device_change_callbacks:
        try:
            x(create, pathname)
        except Exception as e:
            log("error on %s", x, exc_info=True)
            log.error("Error: video device change callback error")
            log.error(" %s", e)

def add_video_device_change_callback(callback):
    global _watch_manager, _notifier, _video_device_change_callbacks
    try:
        import pyinotify
    except ImportError as e:
        log.error("Error: cannot watch for video device changes without pyinotify:")
        log.error(" %s", e)
        return
    log("add_video_device_change_callback(%s) pyinotify=%s", callback, pyinotify)

    class EventHandler(pyinotify.ProcessEvent):
        def process_IN_CREATE(self, event):
            _fire_video_device_change(True, event.pathname)

        def process_IN_DELETE(self, event):
            _fire_video_device_change(False, event.pathname)

    if not _watch_manager:
        _watch_manager = pyinotify.WatchManager()
        mask = pyinotify.IN_DELETE | pyinotify.IN_CREATE  #@UndefinedVariable
        handler = EventHandler(pevent=_video_device_file_filter)
        _notifier = pyinotify.ThreadedNotifier(_watch_manager, handler)
        _notifier.setDaemon(True)
        wdd = _watch_manager.add_watch('/dev', mask)
        log("watching for video device changes in /dev")
        log("notifier=%s, watch=%s", _notifier, wdd)
        _notifier.start()
    _video_device_change_callbacks.append(callback)
    #for running standalone:
    #notifier.loop()

def remove_video_device_change_callback(callback):
    global _watch_manager, _notifier, _video_device_change_callbacks
    if not _watch_manager:
        log.error("Error: cannot remove video device change callback, no watch manager!")
        return
    if callback not in _video_device_change_callbacks:
        log.error("Error: video device change callback not found, cannot remove it!")
        return
    log("remove_video_device_change_callback(%s)", callback)
    _video_device_change_callbacks.remove(callback)
    if len(_video_device_change_callbacks)==0:
        log("last video device change callback removed, closing the watch manager")
        #we can close it:
        _notifier.stop()
        _notifier = None
        try:
            _watch_manager.close()
        except:
            pass
        _watch_manager = None
