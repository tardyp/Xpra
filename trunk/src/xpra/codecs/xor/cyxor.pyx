# This file is part of Xpra.
# Copyright (C) 2012-2019 Antoine Martin <antoine@xpra.org>
# Xpra is released under the terms of the GNU GPL v2, or, at your option, any
# later version. See the file COPYING for details.

#cython: wraparound=False, language_level=3
from __future__ import absolute_import

from libc.stdint cimport uint32_t, uintptr_t
from xpra.buffers.membuf cimport getbuf, object_as_buffer, MemBuf
from libc.string cimport memcpy


def xor_str(a, b):
    assert len(a)==len(b), "cyxor cannot xor strings of different lengths (%s:%s vs %s:%s)" % (type(a), len(a), type(b), len(b))
    cdef Py_ssize_t alen = 0, blen = 0
    cdef uintptr_t ap
    cdef uintptr_t bp
    cdef uintptr_t op
    assert object_as_buffer(a, <const void **> &ap, &alen)==0, "cannot get buffer pointer for %s" % type(a)
    assert object_as_buffer(b, <const void **> &bp, &blen)==0, "cannot get buffer pointer for %s" % type(b)
    assert alen == blen, "python or cython bug? buffers don't have the same length?"
    cdef MemBuf out_buf = getbuf(alen)
    op = <uintptr_t> out_buf.get_mem()
    cdef unsigned char *acbuf = <unsigned char *> ap
    cdef unsigned char *bcbuf = <unsigned char *> bp
    cdef unsigned char *ocbuf = <unsigned char *> op
    cdef uint32_t *obuf = <uint32_t*> op
    cdef uint32_t *abuf = <uint32_t*> ap
    cdef uint32_t *bbuf = <uint32_t*> bp
    cdef unsigned int i, j, steps, char_steps
    if (ap % 4)!=0 or (bp % 4)!=0:
        #unaligned access, use byte at a time slow path:
        char_steps = alen
        for 0 <= i < char_steps:
            ocbuf[i] = acbuf[i] ^ bcbuf[i]
    else:
        #do 4 bytes at a time:
        steps = alen // 4
        if steps>0:
            for 0 <= i < steps:
                obuf[i] = abuf[i] ^ bbuf[i]
        #bytes at a time again at the end:
        char_steps = alen % 4
        if char_steps>0:
            for 0 <= i < char_steps:
                j = alen-char_steps+i
                ocbuf[j] = acbuf[j] ^ bcbuf[j]
    return memoryview(out_buf)

def hybi_unmask(data, unsigned int offset, unsigned int datalen):
    cdef Py_ssize_t mlen = 0, dlen = 0
    cdef uintptr_t mp, dp, op
    cdef uintptr_t buf
    assert object_as_buffer(data, <const void **> &buf, &dlen)==0, "cannot get buffer pointer for %s" % type(data)
    assert dlen>=offset+4+datalen, "buffer too small %i vs %i: offset=%i, datalen=%i" % (dlen, offset+4+datalen, offset, datalen)
    mp = buf+offset
    dp = buf+offset+4
    #we skip the first 'align' bytes in the output buffer,
    #to ensure that its alignment is the same as the input data buffer
    cdef unsigned int align = (<uintptr_t> dp) % 4
    cdef unsigned int initial_chars = (4-align) % 4
    cdef MemBuf out_buf = getbuf(datalen+align+initial_chars)
    op = <uintptr_t> out_buf.get_mem()
    #char pointers:
    cdef unsigned char *mcbuf = <unsigned char *> mp
    cdef unsigned char *dcbuf = <unsigned char *> dp
    cdef unsigned char *ocbuf = <unsigned char *> op
    cdef unsigned int i
    #bytes at a time until we reach the 32-bit boundary:
    for 0 <= i < initial_chars:
        ocbuf[align+i] = dcbuf[i] ^ mcbuf[i%4]
    #32-bit pointers:
    cdef uint32_t *mbuf = <uint32_t*> mp
    cdef uint32_t *dbuf = <uint32_t*> (dp+initial_chars)
    cdef uint32_t *obuf = <uint32_t*> (op+align+initial_chars)
    cdef uint32_t mask_value = 0
    for 0 <= i < 4:
        mask_value *= 0x100
        mask_value += mcbuf[(3-i+initial_chars) % 4]
    cdef unsigned int uint32_steps = (datalen-initial_chars) // 4
    if uint32_steps>0:
        for 0 <= i < uint32_steps:
            obuf[i] = dbuf[i] ^ mask_value
    #bytes at a time again at the end:
    cdef unsigned int last_chars = (datalen-initial_chars) % 4
    if last_chars!=0:
        for 0 <= i < last_chars:
            j = datalen-last_chars+i
            ocbuf[align+j] = dcbuf[j] ^ mcbuf[j%4]
    if align>0:
        return memoryview(out_buf)[align:align+datalen]
    return memoryview(out_buf)
