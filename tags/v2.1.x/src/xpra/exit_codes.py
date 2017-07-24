# This file is part of Xpra.
# Copyright (C) 2010-2016 Antoine Martin <antoine@devloop.org.uk>
# Xpra is released under the terms of the GNU GPL v2, or, at your option, any
# later version. See the file COPYING for details.

EXIT_OK = 0
EXIT_CONNECTION_LOST = 1
EXIT_TIMEOUT = 2
EXIT_PASSWORD_REQUIRED = 3
EXIT_PASSWORD_FILE_ERROR = 4
EXIT_INCOMPATIBLE_VERSION = 5
EXIT_ENCRYPTION = 6
EXIT_FAILURE = 7
EXIT_SSH_FAILURE = 8
EXIT_PACKET_FAILURE = 9
EXIT_MMAP_TOKEN_FAILURE = 10
EXIT_NO_AUTHENTICATION = 11
EXIT_UNSUPPORTED = 12
EXIT_REMOTE_ERROR = 13
EXIT_INTERNAL_ERROR = 14
EXIT_FILE_TOO_BIG = 15
EXIT_SSL_FAILURE = 16

EXIT_STR = {
    EXIT_OK                     : "OK",
    EXIT_CONNECTION_LOST        : "CONNECTION_LOST",
    EXIT_TIMEOUT                : "TIMEOUT",
    EXIT_PASSWORD_REQUIRED      : "PASSWORD_REQUIRED",
    EXIT_PASSWORD_FILE_ERROR    : "PASSWORD_FILE_ERROR",
    EXIT_INCOMPATIBLE_VERSION   : "INCOMPATIBLE_VERSION",
    EXIT_ENCRYPTION             : "ENCRYPTION",
    EXIT_FAILURE                : "FAILURE",
    EXIT_SSH_FAILURE            : "SSH_FAILURE",
    EXIT_PACKET_FAILURE         : "PACKET_FAILURE",
    EXIT_MMAP_TOKEN_FAILURE     : "MMAP_TOKEN_FAILURE",
    EXIT_NO_AUTHENTICATION      : "NO_AUTHENTICATION",
    EXIT_UNSUPPORTED            : "UNSUPPORTED",
    EXIT_REMOTE_ERROR           : "REMOTE_ERROR",
    EXIT_INTERNAL_ERROR         : "INTERNAL_ERROR",
    EXIT_FILE_TOO_BIG           : "FILE_TOO_BIG",
    EXIT_SSL_FAILURE            : "SSL_FAILURE",
    }