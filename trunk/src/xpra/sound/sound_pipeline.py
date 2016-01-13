# This file is part of Xpra.
# Copyright (C) 2010-2015 Antoine Martin <antoine@devloop.org.uk>
# Xpra is released under the terms of the GNU GPL v2, or, at your option, any
# later version. See the file COPYING for details.

import os
import time

from xpra.sound.gstreamer_util import import_gst, gst_major_version
from xpra.log import Logger
log = Logger("sound")

from xpra.util import csv
from xpra.gtk_common.gobject_compat import import_glib
from xpra.gtk_common.gobject_util import one_arg_signal, gobject

FAULT_RATE = int(os.environ.get("XPRA_SOUND_FAULT_INJECTION_RATE", "0"))
_counter = 0
def inject_fault():
    global FAULT_RATE
    if FAULT_RATE<=0:
        return False
    global _counter
    _counter += 1
    return (_counter % FAULT_RATE)==0

gst = import_gst()
MESSAGE_ELEMENT = getattr(gst, "MESSAGE_ELEMENT", None)
from xpra.sound.gstreamer_util import gst_version       #must be done after import_gst()


class SoundPipeline(gobject.GObject):

    __generic_signals__ = {
        "state-changed"     : one_arg_signal,
        "error"             : one_arg_signal,
        "new-stream"        : one_arg_signal,
        "info"              : one_arg_signal,
        }

    def __init__(self, codec):
        gobject.GObject.__init__(self)
        self.codec = codec
        self.codec_description = ""
        self.codec_mode = ""
        self.bus = None
        self.bus_message_handler_id = None
        self.bitrate = -1
        self.pipeline = None
        self.pipeline_str = ""
        self.start_time = 0
        self.state = "stopped"
        self.buffer_count = 0
        self.byte_count = 0
        self.emit_info_due = False
        glib = import_glib()
        self.idle_add = glib.idle_add
        self.timeout_add = glib.timeout_add
        self.source_remove = glib.source_remove

    def idle_emit(self, sig, *args):
        self.idle_add(self.emit, sig, *args)

    def emit_info(self):
        if self.emit_info_due:
            return
        self.emit_info_due = True
        def do_emit_info():
            self.emit_info_due = False
            self.emit("info", self.get_info())
        self.timeout_add(50, do_emit_info)

    def get_info(self):
        info = {"codec"             : self.codec or "",
                "codec_description" : self.codec_description,
                "state"             : self.get_state() or "unknown",
                "buffers"           : self.buffer_count,
                "bytes"             : self.byte_count,
                "pipeline"          : self.pipeline_str,
                "volume"            : self.get_volume(),
                }
        if self.codec_mode:
            info["codec_mode"] = self.codec_mode
        if self.bitrate>0:
            info["bitrate"] = self.bitrate
        if inject_fault():
            info["INJECTING_NONE_FAULT"] = None
            log.warn("injecting None fault: get_info()=%s", info)
        return info

    def setup_pipeline_and_bus(self, elements):
        log("pipeline elements=%s", elements)
        self.pipeline_str = " ! ".join([x for x in elements if x is not None])
        log("pipeline=%s", self.pipeline_str)
        self.start_time = time.time()
        self.pipeline = gst.parse_launch(self.pipeline_str)
        self.bus = self.pipeline.get_bus()
        self.bus_message_handler_id = self.bus.connect("message", self.on_message)
        self.bus.add_signal_watch()

    def do_get_state(self, state):
        if not self.pipeline:
            return  "stopped"
        return {gst.STATE_PLAYING   : "active",
                gst.STATE_PAUSED    : "paused",
                gst.STATE_NULL      : "stopped",
                gst.STATE_READY     : "ready"}.get(state, "unknown")

    def get_state(self):
        return self.state

    def update_bitrate(self, new_bitrate):
        if new_bitrate==self.bitrate:
            return
        self.bitrate = new_bitrate
        log("new bitrate: %s", self.bitrate)
        self.emit_info()


    def set_volume(self, volume=100):
        if self.volume:
            self.volume.set_property("volume", volume/100.0)

    def get_volume(self):
        if self.volume:
            return int(self.volume.get_property("volume")*100)
        return 0


    def start(self):
        log("SoundPipeline.start() codec=%s", self.codec)
        self.idle_emit("new-stream", self.codec)
        self.state = "active"
        self.pipeline.set_state(gst.STATE_PLAYING)
        self.emit_info()
        #we may never get the stream start, synthesize codec event so we get logging:
        self.timeout_add(1000, self.new_codec_description, self.codec)
        log("SoundPipeline.start() done")

    def stop(self):
        p = self.pipeline
        self.pipeline = None
        if not p:
            return
        log("SoundPipeline.stop() state=%s", self.state)
        #uncomment this to see why we end up calling stop()
        #import traceback
        #for x in traceback.format_stack():
        #    for s in x.split("\n"):
        #        v = s.replace("\r", "").replace("\n", "")
        #        if v:
        #            log(v)
        if self.state not in ("starting", "stopped", "ready", None):
            log.info("stopping")
        self.state = "stopped"
        p.set_state(gst.STATE_NULL)
        log("SoundPipeline.stop() done")

    def cleanup(self):
        log("SoundPipeline.cleanup()")
        self.stop()
        b = self.bus
        self.bus = None
        log("SoundPipeline.cleanup() bus=%s", b)
        if not b:
            return
        b.remove_signal_watch()
        bmhid = self.bus_message_handler_id
        log("SoundPipeline.cleanup() bus_message_handler_id=%s", bmhid)
        if bmhid:
            self.bus_message_handler_id = None
            b.disconnect(bmhid)
        self.pipeline = None
        self.codec = None
        self.bitrate = -1
        self.state = None
        self.volume = None
        log("SoundPipeline.cleanup() done")


    def new_codec_description(self, desc):
        if self.codec_description!=desc.lower():
            if self.codec_description!=self.codec and desc==self.codec:
                return
            log.info("using audio codec: %s", desc)
            self.codec_description = desc.lower()


    def on_message(self, bus, message):
        #log("on_message(%s, %s)", bus, message)
        t = message.type
        if t == gst.MESSAGE_EOS:
            self.pipeline.set_state(gst.STATE_NULL)
            log.info("EOS")
            self.state = "stopped"
            self.idle_emit("state-changed", self.state)
        elif t == gst.MESSAGE_ERROR:
            self.pipeline.set_state(gst.STATE_NULL)
            err, details = message.parse_error()
            log.error("pipeline error: %s", err)
            try:
                #prettify (especially on win32):
                p = details.find("\\Source\\")
                if p>0:
                    details = details[p+len("\\Source\\"):]
                for d in details.split(": "):
                    for dl in d.splitlines():
                        log.error(" %s", dl.strip())
            except:
                log.error(" %s", details)
            self.state = "error"
            self.idle_emit("error", str(err))
        elif t == gst.MESSAGE_TAG or t == MESSAGE_ELEMENT:
            try:
                assert gst_version[0]<1
                #Gst 0.10: can handle both TAG and ELEMENT:
                parse = self.parse_message0
            except:
                #Gst 1.0: (does not have MESSAGE_ELEMENT):
                parse = self.parse_message1
            try:
                parse(message)
            except Exception as e:
                log.warn("Warning: failed to parse gstreamer message:")
                log.warn(" %s: %s", type(e), e)
        elif t == gst.MESSAGE_STREAM_STATUS:
            log("stream status: %s", message)
            try:
                log("stream status: %s", message.get_stream_status_object().get_state())
            except:
                pass
        elif t == gst.MESSAGE_STREAM_START:
            log("stream start: %r", message)
            if gst_version[0]>0:
                #with gstreamer 1.x, we don't always get the "audio-codec" message..
                #so print the codec from here instead (and assume gstreamer is using what we told it to)
                #after a delay, just in case we do get the real "audio-codec" message!
                self.timeout_add(500, self.new_codec_description, self.codec)
        elif t in (gst.MESSAGE_ASYNC_DONE, gst.MESSAGE_NEW_CLOCK):
            log("%s", message)
        elif t == gst.MESSAGE_STATE_CHANGED:
            _, new_state, _ = message.parse_state_changed()
            log("state-changed on %s: %s", message.src, gst.element_state_get_name(new_state))
            state = self.do_get_state(new_state)
            if isinstance(message.src, gst.Pipeline):
                self.state = state
                self.idle_emit("state-changed", self.state)
        elif t == gst.MESSAGE_DURATION:
            if gst_major_version==0:
                try:
                    v = d[1]
                    if v>0:
                        log("duration changed: %s", v)
                except:
                    log("duration changed: %s", d)
        elif t == gst.MESSAGE_LATENCY:
            log("latency message from %s: %s", message.src, message)
        elif t == gst.MESSAGE_INFO:
            log.info("pipeline message: %s", message)
        elif t == gst.MESSAGE_WARNING:
            w = message.parse_warning()
            log.warn("pipeline warning: %s", w[0].message)
            log.info("pipeline warning: %s", w[1:])
        else:
            log.info("unhandled bus message type %s: %s", t, message)
        self.emit_info()
        return 0

    def parse_message0(self, message):
        #message parsing code for GStreamer 0.10
        structure = message.structure
        found = False
        if structure.has_field("bitrate"):
            new_bitrate = int(structure["bitrate"])
            self.update_bitrate(new_bitrate)
            found = True
        if structure.has_field("codec"):
            desc = structure["codec"]
            if self.codec_description!=desc:
                log.info("codec: %s", desc)
                self.codec_description = desc
            found = True
        if structure.has_field("audio-codec"):
            desc = structure["audio-codec"]
            self.new_codec_description(desc)
            found = True
        if structure.has_field("mode"):
            mode = structure["mode"]
            if self.codec_mode!=mode:
                log("mode: %s", mode)
                self.codec_mode = mode
            found = True
        if structure.has_field("type"):
            if structure["type"]=="volume-changed":
                log.info("volumes=%s", csv("%i%%" % (v*100/2**16) for v in structure["volumes"]))
                found = True
            else:
                log.info("type=%s", structure["type"])
        if not found:
            #these, we know about, so we just log them:
            for x in ("minimum-bitrate", "maximum-bitrate", "channel-mode", "container-format"):
                if structure.has_field(x):
                    v = structure[x]
                    log("tag message: %s = %s", x, v)
                    return      #handled
            log.info("unknown sound pipeline message %s: %s", message, structure)
            log.info(" %s", structure.keys())


    def parse_message1(self, message):
        #message parsing code for GStreamer 1.x
        taglist = message.parse_tag()
        tags = [taglist.nth_tag_name(x) for x in range(taglist.n_tags())]
        log("bus message with tags=%s", tags)
        if not tags:
            #ignore it
            return
        if "bitrate" in tags:
            new_bitrate = taglist.get_uint("bitrate")
            if new_bitrate[0] is True:
                self.update_bitrate(new_bitrate[1])
        if "codec" in tags:
            desc = taglist.get_string("codec")
            if desc[0] is True and self.codec_description!=desc[1]:
                log.info("codec: %s", desc[1])
                self.codec_description = desc[1]
        if "audio-codec" in tags:
            desc = taglist.get_string("audio-codec")
            if desc[0] is True:
                self.new_codec_description(desc[1])
        if "mode" in tags:
            mode = taglist.get_string("mode")
            if mode[0] is True and self.codec_mode!=mode[1]:
                log("mode: %s", mode[1])
                self.codec_mode = mode[1]
        if "container-format" in tags:
            cf = taglist.get_string("container-format")
            if cf[0] is True:
                log.info("container format: %s", cf[1])
        if "encoder" in tags:
            desc = taglist.get_string("encoder")
            log("encoder: %s", desc[1])
        if "description" in tags:
            desc = taglist.get_string("description")
            log("description: %s", desc[1])
        if len([x for x in tags if x in ("bitrate", "codec", "audio-codec", "mode", "container-format", "encoder", "description")])==0:
            #no match yet
            if len([x for x in tags if x in ("minimum-bitrate", "maximum-bitrate", "channel-mode")])==0:
                structure = message.get_structure()
                log.info("unknown sound pipeline tag message: %s", structure.to_string())
