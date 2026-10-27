/*
 * input_code.c — Comprehensive benchmark suite for LLVM Peephole Optimization Verification.
 *
 * Contains compute kernels across:
 * 1. Cryptographic hashing & bit mixing (MurmurHash, Chacha rounds)
 * 2. Fixed-point arithmetic & DSP digital biquad filters
 * 3. Computer graphics pixel blending & channel packing (RGB565, ARGB8888)
 * 4. Classical bit-manipulation algorithms (Hacker's Delight primitives)
 * 5. Fast numerical algorithms (branchless absolute value, integer clamp, Horner polynomials)
 */

#include <stdint.h>
#include <stdbool.h>

// -----------------------------------------------------------------------------
// 1. Cryptographic Hashing & Bit Mixing Kernels
// -----------------------------------------------------------------------------

uint32_t murmur3_32_scramble(uint32_t k) {
    k *= 0xcc9e2d51;
    k = (k << 15) | (k >> 17);
    k *= 0x1b873593;
    return k;
}

uint32_t murmur3_32_finalize(uint32_t h) {
    h ^= h >> 16;
    h *= 0x85ebca6b;
    h ^= h >> 13;
    h *= 0xc2b2ae35;
    h ^= h >> 16;
    return h;
}

uint64_t splitmix64_next(uint64_t *state) {
    uint64_t z = (*state += 0x9e3779b97f4a7c15ULL);
    z = (z ^ (z >> 30)) * 0xbf58476d1ce4e5b9ULL;
    z = (z ^ (z >> 27)) * 0x94d049bb133111ebULL;
    return z ^ (z >> 31);
}

void chacha_quarter_round(uint32_t *a, uint32_t *b, uint32_t *c, uint32_t *d) {
    *a += *b; *d ^= *a; *d = (*d << 16) | (*d >> 16);
    *c += *d; *b ^= *c; *b = (*b << 12) | (*b >> 20);
    *a += *b; *d ^= *a; *d = (*d << 8)  | (*d >> 24);
    *c += *d; *b ^= *c; *b = (*b << 7)  | (*b >> 25);
}


// -----------------------------------------------------------------------------
// 2. Fixed-Point Arithmetic & DSP Digital Filters
// -----------------------------------------------------------------------------

typedef int32_t q16_t; // 16.16 fixed point

q16_t q16_mul(q16_t a, q16_t b) {
    int64_t temp = (int64_t)a * (int64_t)b;
    return (q16_t)(temp >> 16);
}

q16_t q16_div_pow2(q16_t a, int shift) {
    // Shift right division
    return a >> shift;
}

int32_t dsp_biquad_process(int32_t x, int32_t b0, int32_t b1, int32_t b2,
                           int32_t a1, int32_t a2, int32_t *w1, int32_t *w2) {
    int32_t w0 = x - ((a1 * (*w1)) >> 14) - ((a2 * (*w2)) >> 14);
    int32_t y = ((b0 * w0) >> 14) + ((b1 * (*w1)) >> 14) + ((b2 * (*w2)) >> 14);
    *w2 = *w1;
    *w1 = w0;
    return y;
}

int32_t dsp_scale_by_factors(int32_t val) {
    int32_t s1 = val * 8;       // Opportunity: mul 8 -> shl 3
    int32_t s2 = s1 * 1;       // Opportunity: mul 1 -> identity
    int32_t s3 = s2 + 0;       // Opportunity: add 0 -> identity
    int32_t s4 = s3 / 16;      // Opportunity: division by 16
    int32_t s5 = s4 & 0xFFFFFFFF; // Opportunity: identity mask
    return s5;
}


// -----------------------------------------------------------------------------
// 3. Pixel Blending, Graphics, & Packing
// -----------------------------------------------------------------------------

uint32_t blend_pixels_alpha(uint32_t fg, uint32_t bg, uint8_t alpha) {
    uint32_t rb_fg = fg & 0x00FF00FF;
    uint32_t g_fg  = fg & 0x0000FF00;
    uint32_t rb_bg = bg & 0x00FF00FF;
    uint32_t g_bg  = bg & 0x0000FF00;

    uint32_t rb = ((rb_fg * alpha + rb_bg * (256 - alpha)) >> 8) & 0x00FF00FF;
    uint32_t g  = ((g_fg  * alpha + g_bg  * (256 - alpha)) >> 8) & 0x0000FF00;

    return rb | g;
}

uint16_t pack_rgb888_to_rgb565(uint8_t r, uint8_t g, uint8_t b) {
    uint16_t r5 = (r >> 3) & 0x1F;
    uint16_t g6 = (g >> 2) & 0x3F;
    uint16_t b5 = (b >> 3) & 0x1F;
    return (r5 << 11) | (g6 << 5) | b5;
}

uint32_t unpack_rgb565_to_rgb888(uint16_t rgb565) {
    uint32_t r = (rgb565 >> 11) & 0x1F;
    uint32_t g = (rgb565 >> 5) & 0x3F;
    uint32_t b = rgb565 & 0x1F;

    uint32_t r8 = (r * 527 + 23) >> 6;
    uint32_t g8 = (g * 259 + 33) >> 6;
    uint32_t b8 = (b * 527 + 23) >> 6;

    return (r8 << 16) | (g8 << 8) | b8;
}


// -----------------------------------------------------------------------------
// 4. Classical Bit-Manipulation Algorithms (Hacker's Delight)
// -----------------------------------------------------------------------------

uint32_t bit_isolate_lowest_set(uint32_t x) {
    return x & (-x); // Opportunity: x & -x
}

uint32_t bit_clear_lowest_set(uint32_t x) {
    return x & (x - 1);
}

bool bit_is_power_of_two(uint32_t x) {
    return (x != 0) && ((x & (x - 1)) == 0);
}

uint32_t bit_mask_trailing_zeros(uint32_t x) {
    return (x - 1) & ~x;
}

uint32_t bit_reverse_32(uint32_t x) {
    x = (((x & 0xaaaaaaaa) >> 1) | ((x & 0x55555555) << 1));
    x = (((x & 0xcccccccc) >> 2) | ((x & 0x33333333) << 2));
    x = (((x & 0xf0f0f0f0) >> 4) | ((x & 0x0f0f0f0f) << 4));
    x = (((x & 0xff00ff00) >> 8) | ((x & 0x00ff00ff) << 8));
    return ((x >> 16) | (x << 16));
}

int32_t bit_parity(uint32_t x) {
    x ^= x >> 16;
    x ^= x >> 8;
    x ^= x >> 4;
    x ^= x >> 2;
    x ^= x >> 1;
    return x & 1;
}


// -----------------------------------------------------------------------------
// 5. Fast Branchless Math & Numerical Routines
// -----------------------------------------------------------------------------

int32_t branchless_abs(int32_t x) {
    int32_t mask = x >> 31;
    return (x ^ mask) - mask;
}

int32_t branchless_clamp(int32_t x, int32_t min_val, int32_t max_val) {
    int32_t t = x < min_val ? min_val : x;
    return t > max_val ? max_val : t;
}

int32_t branchless_sign(int32_t x) {
    return (x >> 31) | (int32_t)((uint32_t)(-x) >> 31);
}

int32_t polynomial_horner_eval(int32_t x, int32_t c0, int32_t c1, int32_t c2, int32_t c3) {
    // c0 + x * (c1 + x * (c2 + x * c3))
    int32_t t1 = c3 * x + c2;
    int32_t t2 = t1 * x + c1;
    int32_t r  = t2 * x + c0;
    return r;
}

uint32_t matrix_index_calc(uint32_t row, uint32_t col, uint32_t stride) {
    uint32_t offset1 = row * 64; // mul 64 -> shl 6
    uint32_t offset2 = col * 4;  // mul 4  -> shl 2
    uint32_t base = offset1 + 0; // add 0  -> identity
    return base + offset2;
}

int32_t redundant_math_chain(int32_t a, int32_t b) {
    int32_t v1 = a + 0;
    int32_t v2 = v1 - 0;
    int32_t v3 = v2 * 1;
    int32_t v4 = v3 & -1;
    int32_t v5 = v4 | 0;
    int32_t v6 = v5 ^ 0;
    int32_t v7 = v6 * 4; // opportunity: shl 2
    int32_t v8 = v7 * 8; // opportunity: shl 3
    return v8 + (b - b); // opportunity: b - b -> 0
}
