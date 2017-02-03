# This file is part of Xpra.
# Copyright (C) 2015-2016 Antoine Martin <antoine@devloop.org.uk>
# Xpra is released under the terms of the GNU GPL v2, or, at your option, any
# later version. See the file COPYING for details.

from cpython.buffer cimport PyBuffer_FillInfo

cdef getbuf(size_t l)
cdef padbuf(size_t l, size_t padding)
cdef makebuf(void *p, size_t l)

ctypedef void dealloc_callback(const void *p, size_t l, void *arg)


cdef void *memalign(size_t size) nogil

#cdef extern from "./memalign.h":
#    int MEMALIGN_ALIGNMENT


cdef class MemBuf:
    cdef const void *p
    cdef size_t l
    cdef dealloc_callback *dealloc_cb_p
    cdef void *dealloc_cb_arg

    cdef const void *get_mem(self)
