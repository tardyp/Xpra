/* This file is part of Parti.
 * Copyright (C) 2012 Serviware (Arthur Huillet, <ahuillet@serviware.com>)
 * Copyright (C) 2012 Antoine Martin <antoine@devloop.org.uk>
 * Parti is released under the terms of the GNU GPL v2, or, at your option, any
 * later version. See the file COPYING for details.
 */

#ifdef _WIN32
#include "stdint.h"
#include "inttypes.h"
#else
#include "stdint.h"
#include "stdlib.h"
#endif

#ifndef _WIN32
#include <x264.h>
#else
#define inline __inline
typedef void * x264_picture_t;
#endif

/** Opaque structure - "context". You must have a context to encode images of a given size */
struct x264lib_ctx;

/** Expose the encoder pixel format so the decoder can use the same setting */
int get_encoder_pixel_format(struct x264lib_ctx *ctx);

/** Expose current quality setting so we can tell the client how good the frame was */
int get_encoder_quality(struct x264lib_ctx *ctx);

/** Create an encoding context for images of a given size.  */
struct x264lib_ctx *init_encoder(int width, int height, int initial_quality, int supports_csc_option);

/** Create a decoding context for images of a given size. */
struct x264lib_ctx *init_decoder(int width, int height, int csc_fmt);

/** Call this before decoding, the decoder may need to be re-initialized with the new csc format */
void set_decoder_csc_format(struct x264lib_ctx *ctx, int csc_fmt);

/** Cleanup encoding context. Also frees the memory. */
void clean_encoder(struct x264lib_ctx *);

/** Cleanup decoding context. Without freeing the memory. */
void do_clean_decoder(struct x264lib_ctx *ctx);

/** Cleanup decoding context. Also frees the memory. */
void clean_decoder(struct x264lib_ctx *);

/** Colorspace conversion.
 * Note: you must call compress_image to free the image buffer.
 @param in: Input buffer, format is packed RGB24.
 @param stride: Input stride (size is taken from context).
 @return: the converted picture.
*/
x264_picture_t *csc_image_rgb2yuv(struct x264lib_ctx *ctx, const uint8_t *in, int stride);

/** Colorspace conversion.
 @param in: Input picture (3 planes).
 @param stride: Input strides (3 planes).
 @param out: Will be set to point to the output data in packed RGB24 format. Must be freed after use by calling free().
 @param outsz: Will be set to the size of the output buffer.
 @param outstride: Output stride.
 @return non zero on error.
*/
int csc_image_yuv2rgb(struct x264lib_ctx *ctx, uint8_t *in[3], const int stride[3], uint8_t **out, int *outsz, int *outstride);

/** Compress an image using the given context.
 @param in: the input image, as returned by csc_image_rgb2yuv. It will be freed along with its container x264_picture_t automatically.
 @param out: Will be set to point to the output data. This output buffer MUST NOT BE FREED and will be erased on the
 next call to compress_image.
 @param outsz: Output size
 @param quality_override: Desired quality setting (0 to 100), -1 to use current settings.
*/
int compress_image(struct x264lib_ctx *ctx, x264_picture_t *pic_in, uint8_t **out, int *outsz, int quality_override);

/** Decompress an image using the given context.
 @param in: Input buffer, format is H264.
 @param size: Input size.
 @param out: Will be filled to point to the output data in planar YUV420 format (3 planes). This data will be freed automatically upon next call to the decoder. 
 @param outsize: Output size.
 @param outstride: Output strides (3 planes).
*/
int decompress_image(struct x264lib_ctx *, uint8_t *in, int size, uint8_t *(*out)[3], int *outsize, int (*outstride)[3]);

/**
 * Change the speed of encoding (x264 preset).
 * @param percent: 100 for maximum ("ultrafast") with lowest compression, 0 for highest compression (slower)
 */
void set_encoding_speed(struct x264lib_ctx *ctx, int pct);

/**
 * Change the quality of encoding (x264 f_rf_constant).
 * @param percent: 100 for maximum quality, 0 for lowest quality
 */
void set_encoding_quality(struct x264lib_ctx *ctx, int pct);

/**
 * Define our own memalign function so we can more easily
 * workaround platforms that lack posix_memalign.
 * It does its best to provide sse compatible memory allocation.
 */
void* xmemalign(size_t size);

/**
 * Frees memory allocated with xmemalign
 */
void xmemfree(void *ptr);
