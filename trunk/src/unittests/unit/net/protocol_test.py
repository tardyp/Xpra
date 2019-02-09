#!/usr/bin/env python
# This file is part of Xpra.
# Copyright (C) 2019 Antoine Martin <antoine@xpra.org>
# Xpra is released under the terms of the GNU GPL v2, or, at your option, any
# later version. See the file COPYING for details.

import os
import time
import unittest

from xpra.util import csv, envint, envbool
from xpra.os_util import monotonic_time
from xpra.net.protocol import Protocol
from xpra.net.bytestreams import Connection
from xpra.net.compression import Compressed
from xpra.gtk_common.gobject_compat import import_glib
from xpra.log import Logger

glib = import_glib()

log = Logger("network")

TIMEOUT = envint("XPRA_PROTOCOL_TEST_TIMEOUT", 20)
PROFILING = envbool("XPRA_PROTOCOL_PROFILING", False)


class FastMemoryConnection(Connection):
    def __init__(self, read_buffers, socktype="tcp"):
        self.read_buffers = read_buffers
        self.pos = 0
        self.write_data = []
        Connection.__init__(self, "local", socktype, {})

    def read(self, n):
        if self.read_buffers is None:
            while self.active:
                time.sleep(0.1)
            return None
        if not self.read_buffers:
            log("read(%i) EOF", n)
            return None
        b = self.read_buffers[0]
        if len(b)<=n:
            return self.read_buffers.pop(0)
        self.read_buffers[0] = b[n:]
        return b[:n]

    def write(self, buf):
        self.write_data.append(buf)
        return len(buf)

    def __repr__(self):
        return "FastMemoryConnection"


def noop(*args):
    pass

def nodata(*args):
    return None


class ProfileProtocol(Protocol):

    def profiling_context(self, basename):
        from pycallgraph import PyCallGraph, Config
        from pycallgraph.output import GraphvizOutput
        config = Config()
        graphviz = GraphvizOutput(output_file='%s-%i.png' % (basename, monotonic_time()))
        return PyCallGraph(output=graphviz, config=config)

    def _write_format_thread_loop(self):
        with self.profiling_context("format-thread"):
            Protocol._write_format_thread_loop(self)

    def do_read_parse_thread_loop(self):
        with self.profiling_context("read-parse-thread"):
            Protocol.do_read_parse_thread_loop(self)
        


class ProtocolTest(unittest.TestCase):

    def make_memory_protocol(self, data=[b""], read_buffer_size=1, hangup_delay=0, process_packet_cb=noop, get_packet_cb=nodata):
        conn = FastMemoryConnection(data)
        if PROFILING:
            protocol_class = ProfileProtocol
        else:
            protocol_class = Protocol
        p = protocol_class(glib, conn, process_packet_cb, get_packet_cb=get_packet_cb)
        #p = Protocol(glib, conn, process_packet_cb, get_packet_cb=get_packet_cb)
        p.read_buffer_size = read_buffer_size
        p.hangup_delay = hangup_delay
        return p

    def test_invalid_data(self):
        self.do_test_invalid_data([b"\0"*1])
        self.do_test_invalid_data([b"P"*8])

    def do_test_invalid_data(self, data):
        errs = []
        protocol = self.make_memory_protocol(data)
        def check_failed():
            if not protocol._closed:
                errs.append("protocol not closed")
            if protocol.input_packetcount>0:
                errs.append("processed %i packets" % protocol.input_packetcount)
            if protocol.input_raw_packetcount==0:
                errs.append("not read any raw packets")
        loop = glib.MainLoop()
        glib.timeout_add(200, check_failed)
        glib.timeout_add(400, loop.quit)
        protocol.start()
        loop.run()
        assert not errs, "%s" % csv(errs)

    def test_encoders_and_compressors(self):
        for encoder in ("rencode", "bencode"):
            for compressor in ("lz4", "zlib"):
                p = self.make_memory_protocol()
                p.enable_encoder(encoder)
                p.enable_compressor(compressor)
                packet = ("test", 1, 2, 3)
                items = p.encode(packet)
                assert items

    def test_read_speed(self):
        speeds = []
        for i in range(15, 19):
            speed = self.do_test_read_speed(2**i)
            speeds.append(speed)
        log.info("incoming packet processing speed: %iMB/s", sum(speeds)//len(speeds)//1024//1024)

    def do_test_read_speed(self, pixel_data_size=2**18):
        #prepare some packets to parse:
        p = self.make_memory_protocol()
        #use optimal setup:
        p.enable_encoder("rencode")
        p.enable_compressor("lz4")
        #catch network packets before we write them:
        data = []
        def raw_write(items, *args):
            for item in items:
                data.append(item)
        p.raw_write = raw_write
        for packet in self.make_test_packets(pixel_data_size):
            p._add_packet_to_queue(packet)
        N = 100
        ldata = self.repeat_list(data, N)
        total_size = sum(len(item) for item in ldata)
        #catch parsed packets:
        parsed_packets = []
        def process_packet_cb(proto, packet):
            #log.info("process_packet_cb%s", packet[0])
            if packet[0]==Protocol.CONNECTION_LOST:
                loop.quit()
            else:
                parsed_packets.append(packet[0])
        #run the protocol on this data:
        loop = glib.MainLoop()
        glib.timeout_add(TIMEOUT*1000, loop.quit)
        protocol = self.make_memory_protocol(ldata, read_buffer_size=65536, process_packet_cb=process_packet_cb)
        start = monotonic_time()
        protocol.start()
        loop.run()
        end = monotonic_time()
        assert len(parsed_packets)==N*3, "expected to parse %i packets but got %i" % (N*3, len(parsed_packets))
        elapsed = (end-start)
        log("do_test_read_speed(%i) %iMB in %ims", pixel_data_size, total_size, elapsed*1000)
        return int(total_size/elapsed)

    def make_test_packets(self, pixel_data_size=2**18):
        pixel_data = os.urandom(pixel_data_size)
        return (
            ("test", 1, 2, 3),
            ("ping", 100, 200, 300, 0),
            ("draw", 100, 100, 640, 480, Compressed("pixel-data", pixel_data), {}),
            )

    def repeat_list(self, items, N=100):
        #repeat the same pattern N times:
        l = []
        for _ in range(N):
            for item in items:
                assert len(item)>0
                l.append(item)
        return l

    def test_format_thread(self):
        packets = self.make_test_packets()
        N = 500
        many = self.repeat_list(packets, N)
        def get_packet_cb():
            #log.info("get_packet_cb")
            try:
                packet = many.pop(0)
                return (packet, None, None, None, False, True, False)
            except IndexError:
                protocol.close()
                return (None, )
        def process_packet_cb(proto, packet):
            if packet[0]==Protocol.CONNECTION_LOST:
                glib.timeout_add(1000, loop.quit)
        protocol = self.make_memory_protocol(None, process_packet_cb=process_packet_cb, get_packet_cb=get_packet_cb)
        conn = protocol._conn
        loop = glib.MainLoop()
        glib.timeout_add(TIMEOUT*1000, loop.quit)
        start = monotonic_time()
        protocol.enable_compressor("lz4")
        protocol.enable_encoder("rencode")
        protocol.start()
        protocol.source_has_more()
        loop.run()
        assert protocol._closed
        end = monotonic_time()
        log("protocol: %s", protocol)
        log("%s write-data=%s", conn, len(conn.write_data))
        total_size = sum(len(packet) for packet in conn.write_data)
        elapsed = end-start
        log("bytes=%s, elapsed=%s", total_size, elapsed)
        log.info("format thread: %iMB/s", int(total_size/elapsed//1024//1024))
        assert conn.write_data

def main():
    unittest.main()


if __name__ == '__main__':
    main()
