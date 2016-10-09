# This file is part of Xpra.
# Copyright (C) 2008 Nathaniel Smith <njs@pobox.com>
# Copyright (C) 2011-2013 Antoine Martin <antoine@devloop.org.uk>
# Xpra is released under the terms of the GNU GPL v2, or, at your option, any
# later version. See the file COPYING for details.

import os.path
import glob
import socket
import errno
import stat

from xpra.platform.dotxpra_common import PREFIX, LIVE, DEAD, UNKNOWN


def osexpand(s, actual_username="", uid=0, gid=0):
    if len(actual_username)>0 and s.startswith("~/"):
        #replace "~/" with "~$actual_username/"
        s = "~%s/%s" % (actual_username, s[2:])
    v = os.path.expandvars(os.path.expanduser(s))
    if os.name=="posix":
        v = v.replace("$UID", str(uid or os.getuid()))
        v = v.replace("$GID", str(gid or os.getgid()))
    if len(actual_username)>0:
        for k in ("USERNAME", "USER"):
            v = v.replace("$%s" % k, actual_username)
            v = v.replace("${%s}" % k, actual_username)
    return v

def norm_makepath(dirpath, name):
    if name[0]==":":
        name = name[1:]
    return os.path.join(dirpath, PREFIX + name)

def debug(msg, *args):
    from xpra.log import Logger
    log = Logger("network")
    log(msg, *args)


class DotXpra(object):
    def __init__(self, sockdir=None, sockdirs=[], actual_username="", uid=0, gid=0):
        self.uid = uid or os.getuid()
        self.gid = gid or os.getgid()
        self.username = actual_username
        if sockdir:
            sockdir = self.osexpand(sockdir)
        elif sockdirs:
            sockdir = self.osexpand(sockdirs[0])
        else:
            sockdir = "undefined"
        self._sockdir = self.osexpand(sockdir)
        self._sockdirs = [self.osexpand(x) for x in sockdirs]

    def osexpand(self, v):
        return osexpand(v, self.username, self.uid, self.gid)

    def __repr__(self):
        return "DotXpra(%s, %s)" % (self._sockdir, self._sockdirs)

    def mksockdir(self):
        if self._sockdir and not os.path.exists(self._sockdir):
            os.mkdir(self._sockdir, 0o700)
            if self.uid!=os.getuid() or self.gid!=os.getgid():
                os.chown(self._sockdir, self.uid, self.gid)

    def socket_expand(self, path):
        return self.osexpand(path, uid=self.uid, gid=self.gid)

    def socket_path(self, local_display_name):
        return norm_makepath(self._sockdir, local_display_name)

    LIVE = LIVE
    DEAD = DEAD
    UNKNOWN = UNKNOWN

    def get_server_state(self, sockpath, timeout=5):
        if not os.path.exists(sockpath):
            return self.DEAD
        sock = socket.socket(socket.AF_UNIX)
        sock.settimeout(timeout)
        try:
            sock.connect(sockpath)
        except socket.error as e:
            debug("get_server_state: connect(%s)=%s", sockpath, e)
            err = e.args[0]
            if err==errno.ECONNREFUSED:
                #could be the server is starting up
                return self.UNKNOWN
            if err in (errno.EWOULDBLOCK, errno.ENOENT):
                return self.DEAD
        else:
            sock.close()
            return self.LIVE
        return self.UNKNOWN


    def displays(self, check_uid=0, matching_state=None):
        return list(set(v[1] for v in self.sockets(check_uid, matching_state)))

    #this is imported by winswitch, so we can't change the method signature
    def sockets(self, check_uid=0, matching_state=None):
        #flatten the dictionnary into a list:
        return list(set((v[0], v[1]) for details_values in self.socket_details(check_uid, matching_state).values() for v in details_values))

    def socket_paths(self, check_uid=0, matching_state=None, matching_display=None):
        paths = []
        for details in self.socket_details(check_uid, matching_state, matching_display).values():
            for _, _, socket_path in details:
                paths.append(socket_path)
        return paths

    #find the matching sockets, and return:
    #(state, local_display, sockpath) for each socket directory we probe
    def socket_details(self, check_uid=0, matching_state=None, matching_display=None):
        try:
            import collections
            sd = collections.OrderedDict()
        except:
            sd = {}
        dirs = [self._sockdir]+[x for x in self._sockdirs if x!=self._sockdir]
        seen = set()
        for d in dirs:
            if not d or not os.path.exists(d):
                debug("socket_details: '%s' path does not exist", d)
                continue
            real_dir = os.path.realpath(d)
            if real_dir in seen:
                continue
            seen.add(real_dir)
            #ie: "~/.xpra/HOSTNAME-"
            base = os.path.join(d, PREFIX)
            potential_sockets = glob.glob(base + "*")
            results = []
            for sockpath in sorted(potential_sockets):
                try:
                    s = os.stat(sockpath)
                except OSError as e:
                    debug("socket_details: '%s' path cannot be accessed: %s", sockpath, e)
                    #socket cannot be accessed
                    continue
                if stat.S_ISSOCK(s.st_mode):
                    if check_uid>0:
                        if s.st_uid!=check_uid:
                            #socket uid does not match
                            debug("socket_details: '%s' uid does not match (%s vs %s)", sockpath, s.st_uid, check_uid)
                            continue
                    local_display = ":"+sockpath[len(base):]
                    if matching_display and local_display!=matching_display:
                        debug("socket_details: '%s' display does not match (%s vs %s)", sockpath, local_display, matching_display)
                        continue
                    state = self.get_server_state(sockpath)
                    if matching_state and state!=matching_state:
                        debug("socket_details: '%s' state does not match (%s vs %s)", sockpath, state, matching_state)
                        continue
                    results.append((state, local_display, sockpath))
            if results:
                sd[d] = results
        return sd


#win32 re-defines DotXpra for namedpipes:
from xpra.platform import platform_import
platform_import(globals(), "dotxpra", False,
                "DotXpra",
                "norm_makepath")
