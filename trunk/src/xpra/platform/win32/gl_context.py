# This file is part of Xpra.
# Copyright (C) 2017 Antoine Martin <antoine@devloop.org.uk>
# Xpra is released under the terms of the GNU GPL v2, or, at your option, any
# later version. See the file COPYING for details.

from xpra.log import Logger
log = Logger("opengl")

from ctypes import sizeof, byref
from xpra.client.gl.gl_check import check_PyOpenGL_support
from xpra.platform.win32.common import GetDC, SwapBuffers, ChoosePixelFormat, SetPixelFormat, BeginPaint, EndPaint, GetDesktopWindow
from xpra.platform.win32.glwin32 import wglCreateContext, wglMakeCurrent, wglDeleteContext , PIXELFORMATDESCRIPTOR, PFD_TYPE_RGBA, PFD_DRAW_TO_WINDOW, PFD_SUPPORT_OPENGL, PFD_DOUBLEBUFFER, PFD_DEPTH_DONTCARE, PFD_MAIN_PLANE, PAINTSTRUCT


class WGLWindowContext(object):

    def __init__(self, hwnd):
        bpc = 8
        self.hwnd = hwnd
        self.ps = None
        self.hdc = GetDC(hwnd)
        pfd = PIXELFORMATDESCRIPTOR()
        pfd.nsize = sizeof(PIXELFORMATDESCRIPTOR)
        pfd.nVersion=1
        pfd.dwFlags = PFD_DRAW_TO_WINDOW | PFD_SUPPORT_OPENGL | PFD_DOUBLEBUFFER | PFD_DEPTH_DONTCARE
        pfd.iPixelType = PFD_TYPE_RGBA
        pfd.cColorBits = bpc*3
        pfd.cRedBits = bpc
        pfd.cRedShift = 0
        pfd.cGreenBits = bpc
        pfd.cGreenShift = 0
        pfd.cBlueBits = bpc
        pfd.cBlueShift = 0
        pfd.cAlphaBits = 0 #bpc
        pfd.cAlphaShift = 0
        pfd.cAccumBits = 0
        pfd.cAccumRedBits = 0
        pfd.cAccumGreenBits = 0
        pfd.cAccumBlueBits = 0
        pfd.cAccumAlphaBits = 0
        pfd.cDepthBits = bpc*3
        pfd.cStencilBits = 2
        pfd.cAuxBuffers = 0
        pfd.iLayerType = PFD_MAIN_PLANE #ignored
        pfd.bReserved = 0
        pfd.dwLayerMask = 0
        pfd.dwVisibleMask = 0
        pfd.dwDamageMask = 0
        pf = ChoosePixelFormat(self.hdc, byref(pfd))
        log("ChoosePixelFormat for window %#x and %i bpc: %#x", hwnd, bpc, pf)
        SetPixelFormat(self.hdc, pf, byref(pfd))
        self.context = wglCreateContext(self.hdc)
        log("wglCreateContext(%#x)=%#x", self.hdc, self.context)

    def __enter__(self):
        r = wglMakeCurrent(self.hdc, self.context)
        if not r:
            raise Exception("wglMakeCurrent failed")
        self.ps = PAINTSTRUCT()
        #warning: we replace the hdc here..
        self.hdc = BeginPaint(self.hwnd, byref(self.ps))
        assert self.hdc, "BeginPaint: no display device context"
        self.valid = True

    def __exit__(self, *_args):
        assert self.valid and self.context
        self.valid = False
        EndPaint(self.hwnd, byref(self.ps))
        if not wglDeleteContext(self.context):
            raise Exception("wglDeleteContext failed for context %#x" % self.context)
        self.context = None

    def swap_buffers(self):
        assert self.valid
        SwapBuffers(self.hdc)

    def __repr__(self):
        return "WGLWindowContext(%#x)" % self.hwnd


class WGLContext(object):

    def __init__(self):
        pass

    def check_support(self, force_enable=False):
        hwnd = GetDesktopWindow()
        with WGLWindowContext(hwnd):
            return check_PyOpenGL_support(force_enable)

    def get_bit_depth(self):
        return 0

    def is_double_buffered(self):
        return True

    def get_paint_context(self, gdk_window):
        assert gdk_window
        return WGLWindowContext(gdk_window.hwnd)

    def destroy(self):
        self.context = None

    def __repr__(self):
        return "WGLContext"

GLContext = WGLContext
