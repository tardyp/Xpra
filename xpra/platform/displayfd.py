# This file is part of Xpra.
# Copyright (C) 2017-2018 Antoine Martin <antoine@xpra.org>
# Xpra is released under the terms of the GNU GPL v2, or, at your option, any
# later version. See the file COPYING for details.

import os

from xpra.os_util import monotonic_time
from xpra.util import envint

DISPLAY_FD_TIMEOUT = envint("XPRA_DISPLAY_FD_TIMEOUT", 20)

def eerrno(e):
    try:
        #python3:
        return e.errno
    except AttributeError:
        #python2:
        return e[0]

def write_displayfd(w_pipe, display, timeout=10):
    import select   #@UnresolvedImport
    import errno
    buf = b"%s\n" % display
    limit = monotonic_time()+timeout
    while buf and monotonic_time()<limit:
        try:
            timeout = max(0, limit-monotonic_time())
            _, w, _ = select.select([], [w_pipe], [], timeout)
            if w_pipe in w:
                count = os.write(w_pipe, buf)
                buf = buf[count:]
        except select.error as e:
            if eerrno(e)!=errno.EINTR:
                raise
        except (OSError, IOError) as e:
            if eerrno(e)!=errno.EINTR:
                raise
    return len(buf)==0

def read_displayfd(r_pipe, timeout=DISPLAY_FD_TIMEOUT, proc=None):
    import select   #@UnresolvedImport
    import errno
    # Read the display number from the pipe we gave to Xvfb
    # waiting up to 10 seconds for it to show up
    limit = monotonic_time()+timeout
    buf = b""
    while monotonic_time()<limit and len(buf)<8 and (proc is None or proc.poll() is None):
        try:
            timeout = max(0, limit-monotonic_time())
            r, _, _ = select.select([r_pipe], [], [], timeout)
            if r_pipe in r:
                buf += os.read(r_pipe, 8)
                if buf and (buf[-1]==b'\n' or len(buf)>=8):
                    break
        except select.error as e:
            if eerrno(e)!=errno.EINTR:
                raise
        except (OSError, IOError) as e:
            if eerrno(e)!=errno.EINTR:
                raise
    return buf

def parse_displayfd(buf, err):
    if len(buf) == 0:
        err("did not provide a display number using displayfd")
        return None
    if buf[-1] not in (b'\n', ord(b"\n")):
        err("output not terminated by newline: %s" % buf)
        return None
    try:
        n = int(buf[:-1])
    except:
        err("display number is not a valid number: %s" % buf[:-1])
    if n<0 or n>=2**16:
        err("provided an invalid display number: %s" % n)
    return n
