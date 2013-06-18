# coding=utf8
# This file is part of Xpra.
# Copyright (C) 2013 Antoine Martin <antoine@devloop.org.uk>
# Xpra is released under the terms of the GNU GPL v2, or, at your option, any
# later version. See the file COPYING for details.

from xpra.log import Logger, debug_if_env
log = Logger()
debug = debug_if_env(log, "XPRA_VIDEOPIPELINE_DEBUG")


class VideoPipelineHelper(object):

    _video_encoder_specs = {}
    _csc_encoder_specs = {}

    def may_init(self):
        if len(self._video_encoder_specs)==0:
            self.init_video_encoders_options()
        if len(self._csc_encoder_specs)==0:
            self.init_csc_options()

    def get_encoder_specs(self, encoding):
        return self._video_encoder_specs.get(encoding, [])

    def get_csc_specs(self, src_format):
        return self._csc_encoder_specs.get(src_format, [])

    def init_video_options(self):
        self.init_video_encoders_options()
        self.init_csc_options()

    def init_video_encoders_options(self):
        from xpra.server.server_base import SERVER_ENCODINGS
        if "vpx" in SERVER_ENCODINGS:
            try:
                from xpra.codecs.vpx import encoder
                self.init_video_encoder_option("vpx", encoder)
            except Exception, e:
                log.warn("init_video_encoders_options() cannot add vpx encoder: %s" % e)
        if "x264" in SERVER_ENCODINGS:
            try:
                from xpra.codecs.enc_x264 import encoder        #@Reimport
                self.init_video_encoder_option("x264", encoder)
            except Exception, e:
                log.warn("init_video_encoders_options() cannot add x264 encoder: %s" % e)
            try:
                from xpra.codecs.nvenc import encoder           #@Reimport
                self.init_video_encoder_option("x264", encoder)
            except Exception, e:
                log.warn("init_video_encoders_options() cannot add nvenc encoder: %s" % e)
        debug("init_video_encoders_options() video encoder specs: %s", self._video_encoder_specs)

    def init_video_encoder_option(self, encoding, encoder_module):
        colorspaces = encoder_module.get_colorspaces()
        debug("init_video_encoder_option(%s, %s) colorspaces=%s", encoding, encoder_module, colorspaces)
        encoder_specs = VideoPipelineHelper._video_encoder_specs.setdefault(encoding, {})
        for colorspace in colorspaces:
            colorspace_specs = encoder_specs.setdefault(colorspace, [])
            spec = encoder_module.get_spec(colorspace)
            colorspace_specs.append(spec)

    def init_csc_options(self):
        try:
            from xpra.codecs.csc_swscale import colorspace_converter
            self.init_csc_option(colorspace_converter)
        except Exception, e:
            log.warn("init_csc_options() cannot add swscale csc: %s" % e)
        try:
            from xpra.codecs.csc_nvcuda import colorspace_converter #@Reimport
            self.init_csc_option(colorspace_converter)
        except Exception, e:
            log.warn("init_csc_options() cannot add nvcuda csc: %s" % e)
        debug("init_csc_options() csc specs: %s", self._csc_encoder_specs)

    def init_csc_option(self, csc_module):
        in_cscs = csc_module.get_input_colorspaces()
        debug("init_csc_option(%s)", csc_module)
        for in_csc in in_cscs:
            csc_specs = VideoPipelineHelper._csc_encoder_specs.setdefault(in_csc, [])
            out_cscs = csc_module.get_output_colorspaces(in_csc)
            for out_csc in out_cscs:
                spec = csc_module.get_spec(in_csc, out_csc)
                item = out_csc, spec
                csc_specs.append(item)
