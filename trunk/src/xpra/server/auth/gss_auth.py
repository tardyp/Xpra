#!/usr/bin/env python
# This file is part of Xpra.
# Copyright (C) 2018 Antoine Martin <antoine@devloop.org.uk>
# Xpra is released under the terms of the GNU GPL v2, or, at your option, any
# later version. See the file COPYING for details.

import sys

from gssapi import creds as gsscreds
from gssapi import sec_contexts as gssctx

from xpra.server.auth.sys_auth_base import SysAuthenticatorBase, init, log
from xpra.net.crypto import get_salt, get_digests, gendigest
from xpra.util import xor
assert init and log #tests will disable logging from here

def init(opts):
    pass


class Authenticator(SysAuthenticatorBase):

    def __init__(self, username, **kwargs):
        def ipop(k):
            try:
                return int(kwargs.pop(k, 0))
            except ValueError:
                return 0
        self.service = kwargs.pop("service", "")
        self.uid = ipop("uid")
        self.gid = ipop("gid")
        username = kwargs.pop("username", username)
        kwargs["prompt"] = kwargs.pop("prompt", "token")
        SysAuthenticatorBase.__init__(self, username, **kwargs)
        log("gss auth: service=%s, username=%s", self.service, username)

    def get_uid(self):
        return self.uid

    def get_gid(self):
        return self.gid

    def __repr__(self):
        return "gss"

    def get_challenge(self, digests):
        assert not self.challenge_sent
        if "gss" not in digests:
            log.error("Error: client does not support gss authentication")
            return None
        self.salt = get_salt()
        self.challenge_sent = True
        return self.salt, "gss:%s" % self.service

    def check(self, token):
        log("check(%s)", repr(token))
        assert self.challenge_sent
        server_creds = gsscreds.Credentials(usage='accept')
        server_ctx = gssctx.SecurityContext(creds=server_creds)
        server_ctx.step(token)
        log("gss step complete=%s", server_ctx.complete)
        return True


def main(argv):
    from xpra.platform import program_context
    with program_context("GSS-Auth", "GSS-Authentication"):
        if len(argv)!=3:
            sys.stderr.write("%s invalid arguments\n" % argv[0])
            sys.stderr.write("usage: %s username token\n" % argv[0])
            return 1
        username = argv[1]
        token = argv[2]
        kwargs = {}
        a = Authenticator(username, **kwargs)
        server_salt, digest = a.get_challenge(["xor"])
        salt_digest = a.choose_salt_digest(get_digests())
        assert digest=="xor"
        client_salt = get_salt(len(server_salt))
        combined_salt = gendigest(salt_digest, client_salt, server_salt)
        response = xor(token, combined_salt)
        a.authenticate(response, client_salt)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
