# This file is part of Parti.
# Copyright (C) 2008 Nathaniel Smith <njs@pobox.com>
# Parti is released under the terms of the GNU GPL v2, or, at your option, any
# later version. See the file COPYING for details.

#gcc -pthread -shared -O0 build/temp.linux-x86_64-2.7/xpra/x264/codec.o xpra/x264/x264lib.o -L/usr/lib64 -lx264 -lavcodec -lswscale -lpthread -lpython2.7 -o build/lib.linux-x86_64-2.7/xpra/x264/codec.so

cdef extern from "Python.h":
    ctypedef int Py_ssize_t
    ctypedef object PyObject
    int PyObject_AsReadBuffer(object obj,
                              void ** buffer,
                              Py_ssize_t * buffer_len) except -1

ctypedef unsigned char uint8_t
ctypedef void x264lib_ctx
cdef extern from "x264lib.h":
    x264lib_ctx* init_encoder(int width, int height)
    void clean_encoder(x264lib_ctx *context)
    int compress_image(x264lib_ctx *context, uint8_t *input, int stride, uint8_t **out, int *outsz)


ENCODERS = {}

cdef class Encoder:
    cdef x264lib_ctx *context
    cdef int width
    cdef int height

    def __cinit__(self):
        self.width = 0
        self.height = 0

    def __dealloc__(self):
        self.clean()

    def clean(self):
        if self.context!=NULL:
            clean_encoder(self.context)
            self.context = NULL

    def init(self, width, height):
        self.context = init_encoder(width, height)
        assert self.context
        self.width = width
        self.height = height
    
    def get_width(self):
        return self.width

    def get_height(self):
        return self.height

    def compress_image(self, input, rowstride):
        cdef uint8_t *cout
        cdef int coutsz
        cdef uint8_t *buf = <uint8_t *> 0
        cdef Py_ssize_t buf_len = 0
        assert self.context!=NULL
        PyObject_AsReadBuffer(input, <void **>&buf, &buf_len)
        i = compress_image(self.context, buf, rowstride, &cout, &coutsz)
        if i!=0:
            return i, 0, ""
        coutv = (<char *>cout)[:coutsz]
        return  i, coutsz, coutv
