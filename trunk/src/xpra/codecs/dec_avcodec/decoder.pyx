# This file is part of Xpra.
# Copyright (C) 2012, 2013 Antoine Martin <antoine@devloop.org.uk>
# Xpra is released under the terms of the GNU GPL v2, or, at your option, any
# later version. See the file COPYING for details.

import weakref
from xpra.log import Logger, debug_if_env
log = Logger()
debug = debug_if_env(log, "XPRA_AVCODEC_DEBUG")
error = log.error

from xpra.codecs.codec_constants import get_subsampling_divs, get_colorspace_from_avutil_enum, RGB_FORMATS
from xpra.codecs.image_wrapper import ImageWrapper

include "constants.pxi"

cdef extern from *:
    ctypedef unsigned long size_t
    ctypedef unsigned char uint8_t

cdef extern from "Python.h":
    ctypedef int Py_ssize_t
    ctypedef object PyObject
    object PyBuffer_FromMemory(void *ptr, Py_ssize_t size)
    object PyBuffer_FromReadWriteMemory(void *ptr, Py_ssize_t size)
    int PyObject_AsReadBuffer(object obj, void ** buffer, Py_ssize_t * buffer_len) except -1

cdef extern from "string.h":
    void * memcpy(void * destination, void * source, size_t num) nogil
    void * memset(void * ptr, int value, size_t num) nogil
    void free(void * ptr) nogil


cdef extern from "dec_avcodec.h":
    char *get_avcodec_version()
    char **get_supported_colorspaces()

cdef extern from "../memalign/memalign.h":
    void *xmemalign(size_t size)


ctypedef long AVPixelFormat


cdef extern from "libavutil/mem.h":
    void av_free(void *ptr)

cdef extern from "libavcodec/avcodec.h":
    ctypedef struct AVFrame:
        uint8_t **data
        int *linesize
        int format
    ctypedef struct AVCodec:
        pass
    ctypedef struct AVCodecID:
        pass
    ctypedef struct AVDictionary:
        pass
    ctypedef struct AVPacket:
        uint8_t *data
        int      size

    ctypedef struct AVCodecContext:
        int width
        int height
        AVPixelFormat pix_fmt
        int (*get_buffer)(AVCodecContext *c, AVFrame *pic)
        void (*release_buffer)(AVCodecContext *avctx, AVFrame *frame)
        int thread_safe_callbacks
        int thread_count
        int thread_type
        int flags
        int flags2

    AVPixelFormat PIX_FMT_NONE
    AVCodecID CODEC_ID_H264

    #init and free:
    void avcodec_register_all()
    AVCodec *avcodec_find_decoder(AVCodecID id)
    AVCodecContext *avcodec_alloc_context3(const AVCodec *codec)
    int avcodec_open2(AVCodecContext *avctx, const AVCodec *codec, AVDictionary **options)
    AVFrame *avcodec_alloc_frame()
    void avcodec_free_frame(AVFrame **frame)
    int avcodec_close(AVCodecContext *avctx)

    #actual decoding:
    void av_init_packet(AVPacket *pkt) nogil
    void avcodec_get_frame_defaults(AVFrame *frame) nogil
    int avcodec_decode_video2(AVCodecContext *avctx, AVFrame *picture,
                                int *got_picture_ptr, const AVPacket *avpkt) nogil

    #buffer management:
    int avcodec_default_get_buffer(AVCodecContext *s, AVFrame *pic)
    void avcodec_default_release_buffer(AVCodecContext *s, AVFrame *pic)


def get_version():
    return get_avcodec_version()


COLORSPACES = None
FORMAT_TO_ENUM = {}
ENUM_TO_FORMAT = {}
def init_colorspaces():
    global COLORSPACES
    if COLORSPACES is not None:
        #done already!
        return
    #populate mappings:
    COLORSPACES = []
    for pix_fmt, av_enum_str in {
            "YUV420P"   : "AV_PIX_FMT_YUV420P",
            "YUV422P"   : "AV_PIX_FMT_YUV422P",
            "YUV444P"   : "AV_PIX_FMT_YUV444P",        
            "RGB"       : "AV_PIX_FMT_RGB24",
            "XRGB"      : "AV_PIX_FMT_0RGB",
            "BGRX"      : "AV_PIX_FMT_BGR0",
            "ARGB"      : "AV_PIX_FMT_ARGB",
            "BGRA"      : "AV_PIX_FMT_BGRA",
            "GBRP"      : "AV_PIX_FMT_GBRP",
         }.items():
        if av_enum_str not in const:
            debug("colorspace format %s (%s) not supported by avcodec", pix_fmt, av_enum_str)
            continue
        av_enum = const[av_enum_str]
        FORMAT_TO_ENUM[pix_fmt] = av_enum
        ENUM_TO_FORMAT[av_enum] = pix_fmt
        COLORSPACES.append(pix_fmt)
    debug("colorspaces supported by avcodec %s: %s", get_version(), COLORSPACES)
    if len(COLORSPACES)==0:
        error("avcodec installation problem: no colorspaces found!")

def get_colorspaces():
    init_colorspaces()
    return COLORSPACES


#maps AVCodecContext to the Decoder that manages it
#the key must be obtained using get_context_key()
#The Decoder manages everything.
DECODERS = {}


#these two functions convert pointers to longs
#so we can use a context or frame as a dictionary key
#NOTE: we can't simply use the "Frame" pointer as key
#(the one we create and pass to avcodec_decode_video2)
#because avcodec will pass a different "Frame" pointing
#to the same memory. So we have to use frame.data[0] instead.
cdef long get_context_key(AVCodecContext *avctx):
    cdef unsigned long ctx_key
    assert avctx!=NULL, "context is not set!"
    ctx_key = <unsigned long> avctx
    return ctx_key

cdef long get_frame_key(AVFrame *frame):
    cdef unsigned long frame_key
    assert frame!=NULL, "frame is not set!"
    frame_key = <unsigned long> frame.data[0]
    return frame_key

cdef void clear_frame(AVFrame *frame):
    assert frame!=NULL, "frame is not set!"
    for i in xrange(4):
        frame.data[i] = NULL


cdef get_decoder(AVCodecContext *avctx):
    cdef long ctx_key = get_context_key(avctx)
    global DECODERS
    decoder = DECODERS.get(ctx_key)
    assert decoder is not None, "decoder not found for context %s" % hex(ctx_key)
    return decoder



cdef int avcodec_get_buffer(AVCodecContext *avctx, AVFrame *frame) with gil:
    """ This function overrides AVCodecContext.get_buffer:
        we create an AVFrameWrapper object and
        register it with the Decoder for this context.
    """
    cdef unsigned long frame_key = 0
    cdef AVFrameWrapper frame_wrapper
    cdef int ret
    decoder = get_decoder(avctx)
    ret = avcodec_default_get_buffer(avctx, frame)
    if ret==0:
        frame_key = get_frame_key(frame)
        frame_wrapper = AVFrameWrapper()
        frame_wrapper.set_context(avctx, frame)
        decoder.add_framewrapper(frame_key, frame_wrapper)
    #debug("avcodec_get_buffer(%s, %s) ret=%s, decoder=%s, frame pointer=%s",
    #        hex(<unsigned long> avctx), hex(frame_key), ret, decoder, hex(frame_key))
    return ret

cdef void avcodec_release_buffer(AVCodecContext *avctx, AVFrame *frame) with gil:
    """ when avcodec releases the buffer,
        we tell the Decoder to manage it.
    """
    cdef unsigned long frame_key = get_frame_key(frame)
    decoder = get_decoder(avctx)
    decoder.av_free(frame_key)


cdef class AVFrameWrapper:
    """
        Wraps an AVFrame so we can free it
        once both xpra and avcodec are done with it.
    """
    cdef AVCodecContext *avctx
    cdef AVFrame *frame
    cdef int av_freed
    cdef int xpra_freed

    cdef set_context(self, AVCodecContext *avctx, AVFrame *frame):
        self.avctx = avctx
        self.frame = frame
        self.av_freed = 0
        self.xpra_freed = 0

    def __dealloc__(self):
        #debug("CSCImage.__dealloc__()")
        #By the time this wrapper is garbage collected,
        #we must have freed it!
        assert self.av_freed, "AVFrameWrapper falling out of scope before being freed by avcodec!"
        assert self.xpra_freed, "AVFrameWrapper falling out of scope before being freed by xpra!"
        assert self.frame==NULL and self.avctx==NULL, "frame was freed by both, but not actually freed!"

    def __str__(self):
        return "AVFrameWrapper(%s)" % hex(self.get_key())

    def xpra_free(self):
        debug("%s.xpra_free()", self)
        self.xpra_freed = 1
        if self.av_freed==0:
            return False
        self.free()
        return True

    def av_free(self):
        debug("%s.av_free()", self)
        self.av_freed = 1
        if self.xpra_freed==0:
            return False
        self.free()
        return True

    def free(self):
        debug("%s.free()", self)
        if self.avctx!=NULL and self.frame!=NULL:
            avcodec_default_release_buffer(self.avctx, self.frame)
            #do we need this?
            #avcodec_free_frame(frame)
            self.avctx = NULL
            self.frame = NULL

    def get_key(self):
        return get_frame_key(self.frame)

        
class AVImageWrapper(ImageWrapper):
    """
        Wrapper which allows us to call xpra_free on the decoder
        when the image is freed, or once we have made a copy of the pixels.
    """

    def __str__(self):                          #@DuplicatedSignature
        return ImageWrapper.__str__(self)+"-(%s)" % self.av_frame

    def free(self):                             #@DuplicatedSignature
        debug("AVImageWrapper.free() av_frame=%s", self.av_frame)
        ImageWrapper.free(self)
        self.xpra_free_frame()

    def clone_pixel_data(self):
        ImageWrapper.clone_pixel_data(self)
        self.xpra_free_frame()

    def xpra_free_frame(self):
        if self.av_frame:
            assert self.decoder, "no decoder set!"
            self.decoder.xpra_free(self.av_frame.get_key())
            self.av_frame = None



cdef class Decoder:
    """
        This wraps the AVCodecContext and its configuration,
        also tracks AVFrames.
    """
    cdef AVCodec *codec
    cdef AVCodecContext *codec_ctx
    cdef AVPixelFormat pix_fmt
    cdef AVPixelFormat actual_pix_fmt
    cdef char *colorspace
    cdef object framewrappers
    cdef object weakref_images
    cdef AVFrame *frame                             #@DuplicatedSignature
    cdef int frames

    def init_context(self, int width, int height, colorspace):
        init_colorspaces()
        assert colorspace in COLORSPACES, "invalid colorspace: %s" % colorspace
        self.colorspace = NULL
        for x in COLORSPACES:
            if x==colorspace:
                self.colorspace = x
                break
        if self.colorspace==NULL:
            error("invalid pixel format: %s", colorspace)
            return  False
        self.pix_fmt = FORMAT_TO_ENUM.get(colorspace, PIX_FMT_NONE)
        if self.pix_fmt==PIX_FMT_NONE:
            error("invalid pixel format: %s", colorspace)
            return  False
        self.actual_pix_fmt = self.pix_fmt

        avcodec_register_all()

        self.codec = avcodec_find_decoder(CODEC_ID_H264)
        if self.codec==NULL:
            error("codec H264 not found!")
            return  False
        #from here on, we have to call clean_decoder():
        self.codec_ctx = avcodec_alloc_context3(self.codec)
        if self.codec_ctx==NULL:
            error("failed to allocate codec context!")
            self.clean_decoder()
            return  False

        self.codec_ctx.width = width
        self.codec_ctx.height = height
        self.codec_ctx.pix_fmt = self.pix_fmt
        self.codec_ctx.get_buffer = avcodec_get_buffer
        self.codec_ctx.release_buffer = avcodec_release_buffer
        self.codec_ctx.thread_safe_callbacks = 1
        self.codec_ctx.thread_type = 2      #FF_THREAD_SLICE: allow more than one thread per frame
        self.codec_ctx.thread_count = 0     #auto
        self.codec_ctx.flags2 |= CODEC_FLAG2_FAST   #may cause "no deblock across slices" - which should be fine
        if avcodec_open2(self.codec_ctx, self.codec, NULL) < 0:
            error("could not open codec")
            self.clean_decoder()
            return  False
        self.frame = avcodec_alloc_frame()
        if self.frame==NULL:
            error("could not allocate an AVFrame for decoding")
            self.clean_decoder()
            return  False
        self.frames = 0
        #to keep track of frame wrappers:
        self.framewrappers = {}
        #to keep track of images not freed yet:
        #(we want a weakref.WeakSet() but this is python2.7+ only..)
        self.weakref_images = []
        #register this decoder in the global dictionary:
        global DECODERS
        cdef unsigned long ctx_key = get_context_key(self.codec_ctx)
        DECODERS[ctx_key] = self
        debug("dec_avcodec.Decoder.init_context(%s, %s, %s) self=%s", width, height, colorspace, self.get_info())
        return True

    def clean(self):
        self.clean_decoder()

    def clean_decoder(self):
        debug("%s.clean_decoder()", self)
        #we may have images handed out, ensure we don't reference any memory
        #that needs to be freed using avcodec_release_buffer(..)
        #as this requires the context to still be valid!
        #copying the pixels should ensure we free the AVFrameWrapper associated with it: 
        images = [y for y in [x() for x in self.weakref_images] if y is not None]
        self.weakref_images = []
        debug("clean_decoder() cloning pixels for images still in use: %s", images)
        for img in images:
            img.clone_pixel_data()

        debug("clean_decoder() freeing AVFrame: %s", hex(<unsigned long> self.frame))
        if self.frame!=NULL:
            avcodec_free_frame(&self.frame)
            #redundant: self.frame = NULL

        cdef unsigned long ctx_key          #@DuplicatedSignature
        debug("clean_decoder() freeing AVCodecContext: %s", hex(<unsigned long> self.codec_ctx))
        if self.codec_ctx!=NULL:
            avcodec_close(self.codec_ctx)
            av_free(self.codec_ctx)
            global DECODERS
            ctx_key = get_context_key(self.codec_ctx)
            if ctx_key in DECODERS:
                DECODERS[ctx_key] = self
            self.codec_ctx = NULL
        debug("clean_decoder() done")


    def __str__(self):                      #@DuplicatedSignature
        return "dec_avcodec.Decoder(%s)" % self.get_info()

    def get_info(self):
        info = {
                "type"      : self.get_type(),
                "colorspace": self.get_colorspace(),
                "actual_colorspace": self.get_actual_colorspace(),
                "frames"    : self.frames,
                "buffers"   : len(self.framewrappers),
                }
        if not self.is_closed():
            info["width"] = self.get_width()
            info["height"] = self.get_height()
        else:
            info["closed"] = True
        return info

    def is_closed(self):
        return self.codec_ctx==NULL

    def __dealloc__(self):                          #@DuplicatedSignature
        self.clean()

    def get_width(self):
        assert self.codec_ctx!=NULL
        return self.codec_ctx.width

    def get_height(self):
        assert self.codec_ctx!=NULL
        return self.codec_ctx.height

    def get_type(self):
        return "x264"

    def decompress_image(self, input, options):
        cdef unsigned char * padded_buf = NULL
        cdef const unsigned char * buf = NULL
        cdef Py_ssize_t buf_len = 0
        cdef int len = 0
        cdef int got_picture
        cdef AVPacket avpkt
        cdef unsigned long frame_key                #@DuplicatedSignature
        cdef object framewrapper, img
        assert self.codec_ctx!=NULL
        assert self.codec!=NULL
        #copy input buffer into padded C buffer:
        PyObject_AsReadBuffer(input, <const void**> &buf, &buf_len)
        padded_buf = <unsigned char *> xmemalign(buf_len+128)
        memcpy(padded_buf, buf, buf_len)
        memset(padded_buf+buf_len, 0, 128)
        #ensure we can detect if the frame buffer got allocated:
        clear_frame(self.frame)
        #now safe to run without gil:
        with nogil:
            av_init_packet(&avpkt)
            avpkt.data = <uint8_t *> padded_buf
            avpkt.size = buf_len
            len = avcodec_decode_video2(self.codec_ctx, self.frame, &got_picture, &avpkt)
            free(padded_buf)
        if len < 0: #for testing add: or options.get("frame", 0)%100==99:
            framewrapper = self.frame_error()
            log.warn("%s.decompress_image(%s:%s, %s) avcodec_decode_video2 failure: %s, framewrapper=%s", self, type(input), buf_len, options, len, framewrapper)
            return None
            #raise Exception("avcodec_decode_video2 failed to decode this frame and returned %s, decoder=%s" % (len, self.get_info()))

        if self.actual_pix_fmt!=self.frame.format:
            self.actual_pix_fmt = self.frame.format
            if self.actual_pix_fmt not in ENUM_TO_FORMAT:
                self.frame_error()
                raise Exception("unknown output pixel format: %s, expected %s (%s)" % (self.actual_pix_fmt, self.pix_fmt, self.colorspace))
            debug("avcodec actual output pixel format is %s (%s), expected %s (%s)", self.actual_pix_fmt, self.get_actual_colorspace(), self.pix_fmt, self.colorspace)

        #print("decompress image: colorspace=%s / %s" % (self.colorspace, self.get_colorspace()))
        cs = self.get_actual_colorspace()
        if cs.endswith("P"):
            out = []
            strides = []
            outsize = 0
            divs = get_subsampling_divs(cs)
            nplanes = 3
            for i in range(nplanes):
                _, dy = divs[i]
                if dy==1:
                    height = self.codec_ctx.height
                elif dy==2:
                    height = (self.codec_ctx.height+1)>>1
                else:
                    self.frame_error()
                    raise Exception("invalid height divisor %s" % dy)
                stride = self.frame.linesize[i]
                size = height * stride
                outsize += size
                plane = PyBuffer_FromMemory(<void *>self.frame.data[i], size)
                out.append(plane)
                strides.append(stride)
        else:
            strides = self.frame.linesize[0]+self.frame.linesize[1]+self.frame.linesize[2]
            outsize = self.codec_ctx.height * strides
            out = PyBuffer_FromMemory(<void *>self.frame.data[0], outsize)
            nplanes = 0
        if outsize==0:
            self.frame_error()
            raise Exception("output size is zero!")
        img = AVImageWrapper(0, 0, self.codec_ctx.width, self.codec_ctx.height, out, cs, 24, strides, nplanes)
        img.decoder = self
        img.av_frame = None
        #we must find the frame wrapper used by our get_buffer override:
        frame_key = get_frame_key(self.frame)
        framewrapper = self.get_framewrapper(frame_key)
        img.av_frame = framewrapper
        self.frames += 1
        #add to weakref list after cleaning it up:
        self.weakref_images = [x for x in self.weakref_images if x() is not None]
        ref = weakref.ref(img)
        self.weakref_images.append(ref)
        debug("%s.decompress_image(%s:%s, %s)=%s", self, type(input), buf_len, options, img)
        return img


    def frame_error(self):
        frame_key = get_frame_key(self.frame)
        framewrapper = self.get_framewrapper(frame_key, True)
        log("frame_error() freeing %s", framewrapper)
        if framewrapper:
            #avcodec had allocated a buffer, make sure we don't claim to be using it:
            self.av_free(frame_key)
        return framewrapper

    def get_framewrapper(self, frame_key, ignore_missing=False):
        framewrapper = self.framewrappers.get(int(frame_key))
        #debug("get_framewrapper(%s)=%s, known frame keys=%s", frame_key, framewrapper,
        #                        [hex(x) for x in self.framewrappers.keys()])
        assert ignore_missing or framewrapper is not None, "frame not found for pointer %s, known frame keys=%s" % (hex(frame_key),
                                [hex(x) for x in self.framewrappers.keys()])
        return framewrapper

    def add_framewrapper(self, frame_key, frame_wrapper):
        debug("add_framewrapper(%s, %s) known frame keys: %s", hex(frame_key), frame_wrapper,
                                [hex(x) for x in self.framewrappers.keys()])
        self.framewrappers[int(frame_key)] = frame_wrapper

    def av_free(self, frame_key):                       #@DuplicatedSignature
        avframe = self.get_framewrapper(frame_key)
        debug("av_free(%s) framewrapper=%s", hex(frame_key), avframe)
        if avframe.av_free():
            #frame has been freed - remove it from dict:
            del self.framewrappers[frame_key]

    def xpra_free(self, frame_key):                     #@DuplicatedSignature
        avframe = self.get_framewrapper(frame_key)
        debug("xpra_free(%s) framewrapper=%s", hex(frame_key), avframe)
        if avframe.xpra_free():
            #frame has been freed - remove it from dict:
            del self.framewrappers[frame_key]

    def get_colorspace(self):
        return self.colorspace

    def get_actual_colorspace(self):
        return ENUM_TO_FORMAT.get(self.actual_pix_fmt, "unknown/invalid")
