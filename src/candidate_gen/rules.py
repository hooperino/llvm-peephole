"""Peephole transformation rules and bug patterns.

This module provides templates for generating realistic LLVM peephole optimizations
across arithmetic, bitwise logic, shifts, comparisons, strength reductions, and
subtly unsound/poison mutations.
"""

import random
from typing import Tuple, List, Callable, Dict, Any


RuleFunc = Callable[[int, bool, random.Random], Tuple[str, str, str, str]]
# Returns: (src_ir, tgt_ir, name, description)


# ----------------------------------------------------------------------
# 1. Algebraic & Arithmetic Rules
# ----------------------------------------------------------------------

def rule_add_zero(bw: int, sound: bool, rng: random.Random) -> Tuple[str, str, str, str]:
    """Identity: x + 0 -> x"""
    if sound:
        src = f"define i{bw} @src(i{bw} %x) {{\n  %r = add i{bw} %x, 0\n  ret i{bw} %r\n}}"
        tgt = f"define i{bw} @tgt(i{bw} %x) {{\n  ret i{bw} %x\n}}"
        return src, tgt, "add_zero_sound", "Eliminate addition by constant zero"
    else:
        c = rng.choice([1, 2, -1])
        src = f"define i{bw} @src(i{bw} %x) {{\n  %r = add i{bw} %x, 0\n  ret i{bw} %r\n}}"
        tgt = f"define i{bw} @tgt(i{bw} %x) {{\n  %r = add i{bw} %x, {c}\n  ret i{bw} %r\n}}"
        return src, tgt, "add_zero_unsound_mutated_const", f"Invalidly changed constant zero to {c}"


def rule_sub_zero(bw: int, sound: bool, rng: random.Random) -> Tuple[str, str, str, str]:
    """Identity: x - 0 -> x (vs 0 - x -> x)"""
    if sound:
        src = f"define i{bw} @src(i{bw} %x) {{\n  %r = sub i{bw} %x, 0\n  ret i{bw} %r\n}}"
        tgt = f"define i{bw} @tgt(i{bw} %x) {{\n  ret i{bw} %x\n}}"
        return src, tgt, "sub_zero_sound", "Eliminate subtraction of constant zero"
    else:
        # 0 - x is negation, not identity
        src = f"define i{bw} @src(i{bw} %x) {{\n  %r = sub i{bw} 0, %x\n  ret i{bw} %r\n}}"
        tgt = f"define i{bw} @tgt(i{bw} %x) {{\n  ret i{bw} %x\n}}"
        return src, tgt, "sub_zero_unsound_negation_identity", "Treated negation (0 - x) as identity"


def rule_sub_self(bw: int, sound: bool, rng: random.Random) -> Tuple[str, str, str, str]:
    """Identity: x - x -> 0"""
    if sound:
        src = f"define i{bw} @src(i{bw} %x) {{\n  %r = sub i{bw} %x, %x\n  ret i{bw} %r\n}}"
        tgt = f"define i{bw} @tgt(i{bw} %x) {{\n  ret i{bw} 0\n}}"
        return src, tgt, "sub_self_sound", "Simplify x - x to 0"
    else:
        src = f"define i{bw} @src(i{bw} %x) {{\n  %r = sub i{bw} %x, %x\n  ret i{bw} %r\n}}"
        tgt = f"define i{bw} @tgt(i{bw} %x) {{\n  ret i{bw} %x\n}}"
        return src, tgt, "sub_self_unsound_returned_x", "Erroneously reduced x - x to x instead of 0"


def rule_mul_one(bw: int, sound: bool, rng: random.Random) -> Tuple[str, str, str, str]:
    """Identity: x * 1 -> x"""
    if sound:
        src = f"define i{bw} @src(i{bw} %x) {{\n  %r = mul i{bw} %x, 1\n  ret i{bw} %r\n}}"
        tgt = f"define i{bw} @tgt(i{bw} %x) {{\n  ret i{bw} %x\n}}"
        return src, tgt, "mul_one_sound", "Simplify multiplication by 1 to identity"
    else:
        src = f"define i{bw} @src(i{bw} %x) {{\n  %r = mul i{bw} %x, 1\n  ret i{bw} %r\n}}"
        tgt = f"define i{bw} @tgt(i{bw} %x) {{\n  ret i{bw} 1\n}}"
        return src, tgt, "mul_one_unsound_return_const", "Erroneously returned 1 for x * 1"


def rule_mul_zero(bw: int, sound: bool, rng: random.Random) -> Tuple[str, str, str, str]:
    """Annihilator: x * 0 -> 0"""
    if sound:
        src = f"define i{bw} @src(i{bw} %x) {{\n  %r = mul i{bw} %x, 0\n  ret i{bw} %r\n}}"
        tgt = f"define i{bw} @tgt(i{bw} %x) {{\n  ret i{bw} 0\n}}"
        return src, tgt, "mul_zero_sound", "Simplify multiplication by 0 to constant 0"
    else:
        src = f"define i{bw} @src(i{bw} %x) {{\n  %r = mul i{bw} %x, 0\n  ret i{bw} %r\n}}"
        tgt = f"define i{bw} @tgt(i{bw} %x) {{\n  ret i{bw} %x\n}}"
        return src, tgt, "mul_zero_unsound_return_x", "Erroneously simplified x * 0 to x"


def rule_add_constant_combine(bw: int, sound: bool, rng: random.Random) -> Tuple[str, str, str, str]:
    """Reassociation: (x + C1) + C2 -> x + (C1 + C2)"""
    c1 = rng.randint(1, 15)
    c2 = rng.randint(1, 15)
    c_sum = (c1 + c2) % (1 << bw)
    if sound:
        src = (
            f"define i{bw} @src(i{bw} %x) {{\n"
            f"  %t1 = add i{bw} %x, {c1}\n"
            f"  %r = add i{bw} %t1, {c2}\n"
            f"  ret i{bw} %r\n"
            f"}}"
        )
        tgt = (
            f"define i{bw} @tgt(i{bw} %x) {{\n"
            f"  %r = add i{bw} %x, {c_sum}\n"
            f"  ret i{bw} %r\n"
            f"}}"
        )
        return src, tgt, "add_const_combine_sound", f"Fold (x + {c1}) + {c2} into x + {c_sum}"
    else:
        c_bad = (c1 + c2 + rng.choice([1, -1, 2])) % (1 << bw)
        src = (
            f"define i{bw} @src(i{bw} %x) {{\n"
            f"  %t1 = add i{bw} %x, {c1}\n"
            f"  %r = add i{bw} %t1, {c2}\n"
            f"  ret i{bw} %r\n"
            f"}}"
        )
        tgt = (
            f"define i{bw} @tgt(i{bw} %x) {{\n"
            f"  %r = add i{bw} %x, {c_bad}\n"
            f"  ret i{bw} %r\n"
            f"}}"
        )
        return src, tgt, "add_const_combine_unsound_off_by_one", f"Off-by-one constant folding error ({c_bad} != {c_sum})"


def rule_sdiv_by_one(bw: int, sound: bool, rng: random.Random) -> Tuple[str, str, str, str]:
    """Identity: x / 1 -> x"""
    if sound:
        src = f"define i{bw} @src(i{bw} %x) {{\n  %r = sdiv i{bw} %x, 1\n  ret i{bw} %r\n}}"
        tgt = f"define i{bw} @tgt(i{bw} %x) {{\n  ret i{bw} %x\n}}"
        return src, tgt, "sdiv_one_sound", "Simplify signed division by 1"
    else:
        src = f"define i{bw} @src(i{bw} %x) {{\n  %r = sdiv i{bw} 1, %x\n  ret i{bw} %r\n}}"
        tgt = f"define i{bw} @tgt(i{bw} %x) {{\n  ret i{bw} %x\n}}"
        return src, tgt, "sdiv_one_unsound_reversed_args", "Erroneously simplified 1 / x to x"


def rule_neg_sub(bw: int, sound: bool, rng: random.Random) -> Tuple[str, str, str, str]:
    """Negation reordering: 0 - (x - y) -> y - x"""
    if sound:
        src = (
            f"define i{bw} @src(i{bw} %x, i{bw} %y) {{\n"
            f"  %t1 = sub i{bw} %x, %y\n"
            f"  %r = sub i{bw} 0, %t1\n"
            f"  ret i{bw} %r\n"
            f"}}"
        )
        tgt = (
            f"define i{bw} @tgt(i{bw} %x, i{bw} %y) {{\n"
            f"  %r = sub i{bw} %y, %x\n"
            f"  ret i{bw} %r\n"
            f"}}"
        )
        return src, tgt, "neg_sub_sound", "Transform -(x - y) to y - x"
    else:
        src = (
            f"define i{bw} @src(i{bw} %x, i{bw} %y) {{\n"
            f"  %t1 = sub i{bw} %x, %y\n"
            f"  %r = sub i{bw} 0, %t1\n"
            f"  ret i{bw} %r\n"
            f"}}"
        )
        tgt = (
            f"define i{bw} @tgt(i{bw} %x, i{bw} %y) {{\n"
            f"  %r = sub i{bw} %x, %y\n"
            f"  ret i{bw} %r\n"
            f"}}"
        )
        return src, tgt, "neg_sub_unsound_dropped_negation", "Dropped unary negation without swapping operands"


# ----------------------------------------------------------------------
# 2. Bitwise Logic & Boolean Rings
# ----------------------------------------------------------------------

def rule_and_self(bw: int, sound: bool, rng: random.Random) -> Tuple[str, str, str, str]:
    """Idempotence: x & x -> x"""
    if sound:
        src = f"define i{bw} @src(i{bw} %x) {{\n  %r = and i{bw} %x, %x\n  ret i{bw} %r\n}}"
        tgt = f"define i{bw} @tgt(i{bw} %x) {{\n  ret i{bw} %x\n}}"
        return src, tgt, "and_self_sound", "Simplify x & x to x"
    else:
        src = f"define i{bw} @src(i{bw} %x) {{\n  %r = and i{bw} %x, %x\n  ret i{bw} %r\n}}"
        tgt = f"define i{bw} @tgt(i{bw} %x) {{\n  ret i{bw} 0\n}}"
        return src, tgt, "and_self_unsound_zero", "Erroneously reduced x & x to 0"


def rule_or_self(bw: int, sound: bool, rng: random.Random) -> Tuple[str, str, str, str]:
    """Idempotence: x | x -> x"""
    if sound:
        src = f"define i{bw} @src(i{bw} %x) {{\n  %r = or i{bw} %x, %x\n  ret i{bw} %r\n}}"
        tgt = f"define i{bw} @tgt(i{bw} %x) {{\n  ret i{bw} %x\n}}"
        return src, tgt, "or_self_sound", "Simplify x | x to x"
    else:
        src = f"define i{bw} @src(i{bw} %x) {{\n  %r = or i{bw} %x, %x\n  ret i{bw} %r\n}}"
        tgt = f"define i{bw} @tgt(i{bw} %x) {{\n  ret i{bw} -1\n}}"
        return src, tgt, "or_self_unsound_all_ones", "Erroneously reduced x | x to -1"


def rule_xor_self(bw: int, sound: bool, rng: random.Random) -> Tuple[str, str, str, str]:
    """Identity: x ^ x -> 0"""
    if sound:
        src = f"define i{bw} @src(i{bw} %x) {{\n  %r = xor i{bw} %x, %x\n  ret i{bw} %r\n}}"
        tgt = f"define i{bw} @tgt(i{bw} %x) {{\n  ret i{bw} 0\n}}"
        return src, tgt, "xor_self_sound", "Simplify x ^ x to 0"
    else:
        src = f"define i{bw} @src(i{bw} %x) {{\n  %r = xor i{bw} %x, %x\n  ret i{bw} %r\n}}"
        tgt = f"define i{bw} @tgt(i{bw} %x) {{\n  ret i{bw} %x\n}}"
        return src, tgt, "xor_self_unsound_return_x", "Erroneously reduced x ^ x to x"


def rule_and_zero(bw: int, sound: bool, rng: random.Random) -> Tuple[str, str, str, str]:
    """Annihilator: x & 0 -> 0"""
    if sound:
        src = f"define i{bw} @src(i{bw} %x) {{\n  %r = and i{bw} %x, 0\n  ret i{bw} %r\n}}"
        tgt = f"define i{bw} @tgt(i{bw} %x) {{\n  ret i{bw} 0\n}}"
        return src, tgt, "and_zero_sound", "Simplify x & 0 to 0"
    else:
        src = f"define i{bw} @src(i{bw} %x) {{\n  %r = and i{bw} %x, 0\n  ret i{bw} %r\n}}"
        tgt = f"define i{bw} @tgt(i{bw} %x) {{\n  ret i{bw} %x\n}}"
        return src, tgt, "and_zero_unsound_return_x", "Erroneously preserved x on x & 0"


def rule_or_zero(bw: int, sound: bool, rng: random.Random) -> Tuple[str, str, str, str]:
    """Identity: x | 0 -> x"""
    if sound:
        src = f"define i{bw} @src(i{bw} %x) {{\n  %r = or i{bw} %x, 0\n  ret i{bw} %r\n}}"
        tgt = f"define i{bw} @tgt(i{bw} %x) {{\n  ret i{bw} %x\n}}"
        return src, tgt, "or_zero_sound", "Simplify x | 0 to x"
    else:
        src = f"define i{bw} @src(i{bw} %x) {{\n  %r = or i{bw} %x, 0\n  ret i{bw} %r\n}}"
        tgt = f"define i{bw} @tgt(i{bw} %x) {{\n  ret i{bw} 0\n}}"
        return src, tgt, "or_zero_unsound_zero", "Erroneously reduced x | 0 to 0"


def rule_and_all_ones(bw: int, sound: bool, rng: random.Random) -> Tuple[str, str, str, str]:
    """Identity: x & -1 -> x"""
    if sound:
        src = f"define i{bw} @src(i{bw} %x) {{\n  %r = and i{bw} %x, -1\n  ret i{bw} %r\n}}"
        tgt = f"define i{bw} @tgt(i{bw} %x) {{\n  ret i{bw} %x\n}}"
        return src, tgt, "and_all_ones_sound", "Simplify x & -1 to x"
    else:
        src = f"define i{bw} @src(i{bw} %x) {{\n  %r = and i{bw} %x, -1\n  ret i{bw} %r\n}}"
        tgt = f"define i{bw} @tgt(i{bw} %x) {{\n  ret i{bw} -1\n}}"
        return src, tgt, "and_all_ones_unsound_ones", "Erroneously returned -1 for x & -1"


def rule_or_all_ones(bw: int, sound: bool, rng: random.Random) -> Tuple[str, str, str, str]:
    """Annihilator: x | -1 -> -1"""
    if sound:
        src = f"define i{bw} @src(i{bw} %x) {{\n  %r = or i{bw} %x, -1\n  ret i{bw} %r\n}}"
        tgt = f"define i{bw} @tgt(i{bw} %x) {{\n  ret i{bw} -1\n}}"
        return src, tgt, "or_all_ones_sound", "Simplify x | -1 to -1"
    else:
        src = f"define i{bw} @src(i{bw} %x) {{\n  %r = or i{bw} %x, -1\n  ret i{bw} %r\n}}"
        tgt = f"define i{bw} @tgt(i{bw} %x) {{\n  ret i{bw} %x\n}}"
        return src, tgt, "or_all_ones_unsound_x", "Erroneously returned x for x | -1"


def rule_double_not(bw: int, sound: bool, rng: random.Random) -> Tuple[str, str, str, str]:
    """Involution: ~(~x) -> x  (encoded as (x ^ -1) ^ -1)"""
    if sound:
        src = (
            f"define i{bw} @src(i{bw} %x) {{\n"
            f"  %t1 = xor i{bw} %x, -1\n"
            f"  %r = xor i{bw} %t1, -1\n"
            f"  ret i{bw} %r\n"
            f"}}"
        )
        tgt = f"define i{bw} @tgt(i{bw} %x) {{\n  ret i{bw} %x\n}}"
        return src, tgt, "double_not_sound", "Simplify double bitwise NOT ~(~x) to x"
    else:
        src = (
            f"define i{bw} @src(i{bw} %x) {{\n"
            f"  %t1 = xor i{bw} %x, -1\n"
            f"  %r = xor i{bw} %t1, -1\n"
            f"  ret i{bw} %r\n"
            f"}}"
        )
        tgt = (
            f"define i{bw} @tgt(i{bw} %x) {{\n"
            f"  %r = xor i{bw} %x, -1\n"
            f"  ret i{bw} %r\n"
            f"}}"
        )
        return src, tgt, "double_not_unsound_single_not", "Erroneously kept single NOT for double NOT"


def rule_absorption_and_or(bw: int, sound: bool, rng: random.Random) -> Tuple[str, str, str, str]:
    """Absorption: (x | y) & x -> x"""
    if sound:
        src = (
            f"define i{bw} @src(i{bw} %x, i{bw} %y) {{\n"
            f"  %t1 = or i{bw} %x, %y\n"
            f"  %r = and i{bw} %t1, %x\n"
            f"  ret i{bw} %r\n"
            f"}}"
        )
        tgt = f"define i{bw} @tgt(i{bw} %x, i{bw} %y) {{\n  ret i{bw} %x\n}}"
        return src, tgt, "absorption_and_or_sound", "Absorption: (x | y) & x -> x"
    else:
        src = (
            f"define i{bw} @src(i{bw} %x, i{bw} %y) {{\n"
            f"  %t1 = or i{bw} %x, %y\n"
            f"  %r = and i{bw} %t1, %x\n"
            f"  ret i{bw} %r\n"
            f"}}"
        )
        tgt = f"define i{bw} @tgt(i{bw} %x, i{bw} %y) {{\n  ret i{bw} %y\n}}"
        return src, tgt, "absorption_and_or_unsound_y", "Erroneously absorbed to second operand y instead of x"


def rule_and_not_self(bw: int, sound: bool, rng: random.Random) -> Tuple[str, str, str, str]:
    """Complement: x & ~x -> 0"""
    if sound:
        src = (
            f"define i{bw} @src(i{bw} %x) {{\n"
            f"  %notx = xor i{bw} %x, -1\n"
            f"  %r = and i{bw} %x, %notx\n"
            f"  ret i{bw} %r\n"
            f"}}"
        )
        tgt = f"define i{bw} @tgt(i{bw} %x) {{\n  ret i{bw} 0\n}}"
        return src, tgt, "and_not_self_sound", "Complement law: x & ~x -> 0"
    else:
        src = (
            f"define i{bw} @src(i{bw} %x) {{\n"
            f"  %notx = xor i{bw} %x, -1\n"
            f"  %r = and i{bw} %x, %notx\n"
            f"  ret i{bw} %r\n"
            f"}}"
        )
        tgt = f"define i{bw} @tgt(i{bw} %x) {{\n  ret i{bw} -1\n}}"
        return src, tgt, "and_not_self_unsound_ones", "Erroneously evaluated x & ~x to -1"


# ----------------------------------------------------------------------
# 3. Shifts & Strength Reductions
# ----------------------------------------------------------------------

def rule_mul_pow2_to_shl(bw: int, sound: bool, rng: random.Random) -> Tuple[str, str, str, str]:
    """Strength reduction: x * 2^k -> x << k"""
    k = rng.randint(1, min(6, bw - 1))
    c = 1 << k
    if sound:
        src = f"define i{bw} @src(i{bw} %x) {{\n  %r = mul i{bw} %x, {c}\n  ret i{bw} %r\n}}"
        tgt = f"define i{bw} @tgt(i{bw} %x) {{\n  %r = shl i{bw} %x, {k}\n  ret i{bw} %r\n}}"
        return src, tgt, "mul_pow2_to_shl_sound", f"Transform multiplication by 2^{k} ({c}) to left shift by {k}"
    else:
        k_bad = (k + 1) if (k + 1) < bw else (k - 1)
        src = f"define i{bw} @src(i{bw} %x) {{\n  %r = mul i{bw} %x, {c}\n  ret i{bw} %r\n}}"
        tgt = f"define i{bw} @tgt(i{bw} %x) {{\n  %r = shl i{bw} %x, {k_bad}\n  ret i{bw} %r\n}}"
        return src, tgt, "mul_pow2_to_shl_unsound_bad_shift", f"Shift exponent mismatch: shifted by {k_bad} instead of {k}"


def rule_udiv_pow2_to_lshr(bw: int, sound: bool, rng: random.Random) -> Tuple[str, str, str, str]:
    """Strength reduction: udiv x, 2^k -> lshr x, k"""
    k = rng.randint(1, min(4, bw - 1))
    c = 1 << k
    if sound:
        src = f"define i{bw} @src(i{bw} %x) {{\n  %r = udiv i{bw} %x, {c}\n  ret i{bw} %r\n}}"
        tgt = f"define i{bw} @tgt(i{bw} %x) {{\n  %r = lshr i{bw} %x, {k}\n  ret i{bw} %r\n}}"
        return src, tgt, "udiv_pow2_to_lshr_sound", f"Transform unsigned division by {c} to logical right shift by {k}"
    else:
        # Transforming sdiv (signed) to ashr is subtly UNSOUND due to negative number rounding!
        src = f"define i{bw} @src(i{bw} %x) {{\n  %r = sdiv i{bw} %x, {c}\n  ret i{bw} %r\n}}"
        tgt = f"define i{bw} @tgt(i{bw} %x) {{\n  %r = ashr i{bw} %x, {k}\n  ret i{bw} %r\n}}"
        return src, tgt, "sdiv_pow2_to_ashr_unsound_signed_rounding", "Erroneously converted signed sdiv to ashr (breaks rounding on negatives)"


def rule_shl_zero(bw: int, sound: bool, rng: random.Random) -> Tuple[str, str, str, str]:
    """Identity: x << 0 -> x"""
    if sound:
        src = f"define i{bw} @src(i{bw} %x) {{\n  %r = shl i{bw} %x, 0\n  ret i{bw} %r\n}}"
        tgt = f"define i{bw} @tgt(i{bw} %x) {{\n  ret i{bw} %x\n}}"
        return src, tgt, "shl_zero_sound", "Eliminate shift by constant zero"
    else:
        src = f"define i{bw} @src(i{bw} %x) {{\n  %r = shl i{bw} %x, 0\n  ret i{bw} %r\n}}"
        tgt = f"define i{bw} @tgt(i{bw} %x) {{\n  ret i{bw} 0\n}}"
        return src, tgt, "shl_zero_unsound_zero", "Erroneously reduced x << 0 to 0"


def rule_combine_shifts(bw: int, sound: bool, rng: random.Random) -> Tuple[str, str, str, str]:
    """Reassociation: (x << k1) << k2 -> x << (k1 + k2)"""
    k1 = rng.randint(1, min(3, bw // 2))
    k2 = rng.randint(1, min(3, bw // 2))
    k_sum = k1 + k2
    if sound and k_sum < bw:
        src = (
            f"define i{bw} @src(i{bw} %x) {{\n"
            f"  %t1 = shl i{bw} %x, {k1}\n"
            f"  %r = shl i{bw} %t1, {k2}\n"
            f"  ret i{bw} %r\n"
            f"}}"
        )
        tgt = (
            f"define i{bw} @tgt(i{bw} %x) {{\n"
            f"  %r = shl i{bw} %x, {k_sum}\n"
            f"  ret i{bw} %r\n"
            f"}}"
        )
        return src, tgt, "combine_shifts_sound", f"Fold consecutive shifts: (x << {k1}) << {k2} -> x << {k_sum}"
    else:
        # Overshift UB in LLVM: shift amount >= bitwidth is poison/UB!
        k_ub = bw + rng.randint(0, 4)
        src = (
            f"define i{bw} @src(i{bw} %x) {{\n"
            f"  %t1 = shl i{bw} %x, {k1}\n"
            f"  %r = shl i{bw} %t1, {k2}\n"
            f"  ret i{bw} %r\n"
            f"}}"
        )
        tgt = (
            f"define i{bw} @tgt(i{bw} %x) {{\n"
            f"  %r = shl i{bw} %x, {k_ub}\n"
            f"  ret i{bw} %r\n"
            f"}}"
        )
        return src, tgt, "combine_shifts_unsound_overshift_ub", f"Generated overshift UB (shift by {k_ub} >= bitwidth {bw})"


def rule_mul_const_decompose(bw: int, sound: bool, rng: random.Random) -> Tuple[str, str, str, str]:
    """Strength reduction: x * 3 -> (x << 1) + x, x * 5 -> (x << 2) + x, x * 9 -> (x << 3) + x"""
    k = rng.choice([1, 2, 3])
    if k >= bw:
        k = 1
    c = (1 << k) + 1
    if sound:
        src = f"define i{bw} @src(i{bw} %x) {{\n  %r = mul i{bw} %x, {c}\n  ret i{bw} %r\n}}"
        tgt = (
            f"define i{bw} @tgt(i{bw} %x) {{\n"
            f"  %sh = shl i{bw} %x, {k}\n"
            f"  %r = add i{bw} %sh, %x\n"
            f"  ret i{bw} %r\n"
            f"}}"
        )
        return src, tgt, "mul_const_decompose_sound", f"Decompose x * {c} into (x << {k}) + x"
    else:
        # Subtracting instead of adding: (x << k) - x computes x * (c - 2)
        src = f"define i{bw} @src(i{bw} %x) {{\n  %r = mul i{bw} %x, {c}\n  ret i{bw} %r\n}}"
        tgt = (
            f"define i{bw} @tgt(i{bw} %x) {{\n"
            f"  %sh = shl i{bw} %x, {k}\n"
            f"  %r = sub i{bw} %sh, %x\n"
            f"  ret i{bw} %r\n"
            f"}}"
        )
        return src, tgt, "mul_const_decompose_unsound_sub", f"Erroneously subtracted operand: (x << {k}) - x computes x * {c - 2}"


# ----------------------------------------------------------------------
# 4. Comparisons & Conditionals (`icmp`, `select`)
# ----------------------------------------------------------------------

def rule_icmp_eq_self(bw: int, sound: bool, rng: random.Random) -> Tuple[str, str, str, str]:
    """Tautology: icmp eq x, x -> true (1)"""
    if sound:
        src = f"define i1 @src(i{bw} %x) {{\n  %r = icmp eq i{bw} %x, %x\n  ret i1 %r\n}}"
        tgt = "define i1 @tgt(i{bw} %x) {\n  ret i1 1\n}"
        return src, tgt, "icmp_eq_self_sound", "Simplify icmp eq x, x to constant true (1)"
    else:
        src = f"define i1 @src(i{bw} %x) {{\n  %r = icmp eq i{bw} %x, %x\n  ret i1 %r\n}}"
        tgt = "define i1 @tgt(i{bw} %x) {\n  ret i1 0\n}"
        return src, tgt, "icmp_eq_self_unsound_false", "Erroneously evaluated icmp eq x, x to false (0)"


def rule_icmp_ne_self(bw: int, sound: bool, rng: random.Random) -> Tuple[str, str, str, str]:
    """Contradiction: icmp ne x, x -> false (0)"""
    if sound:
        src = f"define i1 @src(i{bw} %x) {{\n  %r = icmp ne i{bw} %x, %x\n  ret i1 %r\n}}"
        tgt = "define i1 @tgt(i{bw} %x) {\n  ret i1 0\n}"
        return src, tgt, "icmp_ne_self_sound", "Simplify icmp ne x, x to constant false (0)"
    else:
        src = f"define i1 @src(i{bw} %x) {{\n  %r = icmp ne i{bw} %x, %x\n  ret i1 %r\n}}"
        tgt = "define i1 @tgt(i{bw} %x) {\n  ret i1 1\n}"
        return src, tgt, "icmp_ne_self_unsound_true", "Erroneously evaluated icmp ne x, x to true (1)"


def rule_icmp_ult_zero(bw: int, sound: bool, rng: random.Random) -> Tuple[str, str, str, str]:
    """Contradiction: icmp ult x, 0 -> false (0)"""
    if sound:
        src = f"define i1 @src(i{bw} %x) {{\n  %r = icmp ult i{bw} %x, 0\n  ret i1 %r\n}}"
        tgt = "define i1 @tgt(i{bw} %x) {\n  ret i1 0\n}"
        return src, tgt, "icmp_ult_zero_sound", "Simplify unsigned less than 0 (icmp ult x, 0) to false"
    else:
        # slt x, 0 is NOT false (true for negative numbers)
        src = f"define i1 @src(i{bw} %x) {{\n  %r = icmp slt i{bw} %x, 0\n  ret i1 %r\n}}"
        tgt = "define i1 @tgt(i{bw} %x) {\n  ret i1 0\n}"
        return src, tgt, "icmp_slt_zero_unsound_signed_confusion", "Confused signed slt with unsigned ult for comparison with 0"


def rule_select_same(bw: int, sound: bool, rng: random.Random) -> Tuple[str, str, str, str]:
    """Identity: select %cond, %x, %x -> %x"""
    if sound:
        src = (
            f"define i{bw} @src(i1 %c, i{bw} %x) {{\n"
            f"  %r = select i1 %c, i{bw} %x, i{bw} %x\n"
            f"  ret i{bw} %r\n"
            f"}}"
        )
        tgt = f"define i{bw} @tgt(i1 %c, i{bw} %x) {{\n  ret i{bw} %x\n}}"
        return src, tgt, "select_same_sound", "Simplify select with identical true/false arms to %x"
    else:
        src = (
            f"define i{bw} @src(i1 %c, i{bw} %x) {{\n"
            f"  %r = select i1 %c, i{bw} %x, i{bw} %x\n"
            f"  ret i{bw} %r\n"
            f"}}"
        )
        tgt = f"define i{bw} @tgt(i1 %c, i{bw} %x) {{\n  ret i{bw} 0\n}}"
        return src, tgt, "select_same_unsound_zero", "Erroneously evaluated select with identical arms to 0"


def rule_select_true(bw: int, sound: bool, rng: random.Random) -> Tuple[str, str, str, str]:
    """Constant condition: select 1, %x, %y -> %x"""
    if sound:
        src = (
            f"define i{bw} @src(i{bw} %x, i{bw} %y) {{\n"
            f"  %r = select i1 1, i{bw} %x, i{bw} %y\n"
            f"  ret i{bw} %r\n"
            f"}}"
        )
        tgt = f"define i{bw} @tgt(i{bw} %x, i{bw} %y) {{\n  ret i{bw} %x\n}}"
        return src, tgt, "select_true_sound", "Simplify select 1, %x, %y to %x"
    else:
        src = (
            f"define i{bw} @src(i{bw} %x, i{bw} %y) {{\n"
            f"  %r = select i1 1, i{bw} %x, i{bw} %y\n"
            f"  ret i{bw} %r\n"
            f"}}"
        )
        tgt = f"define i{bw} @tgt(i{bw} %x, i{bw} %y) {{\n  ret i{bw} %y\n}}"
        return src, tgt, "select_true_unsound_chose_false_arm", "Picked false arm on constant-true select"


# ----------------------------------------------------------------------
# 5. Poison, Undefined Behavior & Flag Mutations
# ----------------------------------------------------------------------

def rule_nsw_overflow_ub(bw: int, sound: bool, rng: random.Random) -> Tuple[str, str, str, str]:
    """Poison refinement:
    Source: add %x, 1 (no nsw, wraps on INT_MAX)
    Target with nsw is UNSOUND because it produces poison on overflow where source defined wrap-around!
    """
    if sound:
        # Dropping nsw in target is sound refinement (source has poison on overflow, target wraps)
        src = (
            f"define i{bw} @src(i{bw} %x) {{\n"
            f"  %r = add nsw i{bw} %x, 1\n"
            f"  ret i{bw} %r\n"
            f"}}"
        )
        tgt = (
            f"define i{bw} @tgt(i{bw} %x) {{\n"
            f"  %r = add i{bw} %x, 1\n"
            f"  ret i{bw} %r\n"
            f"}}"
        )
        return src, tgt, "drop_nsw_flag_sound", "Soundly drop nsw flag (refining poison to wrap-around)"
    else:
        # Adding nsw to target when source didn't have it introduces poison (UNSOUND!)
        src = (
            f"define i{bw} @src(i{bw} %x) {{\n"
            f"  %r = add i{bw} %x, 1\n"
            f"  ret i{bw} %r\n"
            f"}}"
        )
        tgt = (
            f"define i{bw} @tgt(i{bw} %x) {{\n"
            f"  %r = add nsw i{bw} %x, 1\n"
            f"  ret i{bw} %r\n"
            f"}}"
        )
        return src, tgt, "add_nsw_flag_unsound_poison_leak", "Illegally added nsw flag to target (causes poison on overflow)"


def rule_nuw_overflow_ub(bw: int, sound: bool, rng: random.Random) -> Tuple[str, str, str, str]:
    """Poison refinement with nuw (no unsigned wrap)"""
    if sound:
        src = (
            f"define i{bw} @src(i{bw} %x) {{\n"
            f"  %r = sub nuw i{bw} %x, 0\n"
            f"  ret i{bw} %r\n"
            f"}}"
        )
        tgt = f"define i{bw} @tgt(i{bw} %x) {{\n  ret i{bw} %x\n}}"
        return src, tgt, "sub_nuw_zero_sound", "Simplify sub nuw x, 0 to x"
    else:
        # Adding nuw to target when subtracting non-zero
        c = rng.randint(1, 5)
        src = (
            f"define i{bw} @src(i{bw} %x) {{\n"
            f"  %r = sub i{bw} %x, {c}\n"
            f"  ret i{bw} %r\n"
            f"}}"
        )
        tgt = (
            f"define i{bw} @tgt(i{bw} %x) {{\n"
            f"  %r = sub nuw i{bw} %x, {c}\n"
            f"  ret i{bw} %r\n"
            f"}}"
        )
        return src, tgt, "sub_nuw_unsound_unsigned_underflow", "Added nuw to subtraction causing poison on underflow"


def rule_exact_sdiv_poison(bw: int, sound: bool, rng: random.Random) -> Tuple[str, str, str, str]:
    """Exact division poison: sdiv exact x, 2 vs sdiv x, 2"""
    if sound:
        # Dropping exact is sound
        src = (
            f"define i{bw} @src(i{bw} %x) {{\n"
            f"  %r = sdiv exact i{bw} %x, 2\n"
            f"  ret i{bw} %r\n"
            f"}}"
        )
        tgt = (
            f"define i{bw} @tgt(i{bw} %x) {{\n"
            f"  %r = sdiv i{bw} %x, 2\n"
            f"  ret i{bw} %r\n"
            f"}}"
        )
        return src, tgt, "drop_exact_flag_sound", "Dropping exact flag on sdiv is sound refinement"
    else:
        # Adding exact introduces poison on odd numbers
        src = (
            f"define i{bw} @src(i{bw} %x) {{\n"
            f"  %r = sdiv i{bw} %x, 2\n"
            f"  ret i{bw} %r\n"
            f"}}"
        )
        tgt = (
            f"define i{bw} @tgt(i{bw} %x) {{\n"
            f"  %r = sdiv exact i{bw} %x, 2\n"
            f"  ret i{bw} %r\n"
            f"}}"
        )
        return src, tgt, "add_exact_flag_unsound_poison", "Added exact flag to sdiv when remainder is non-zero (poison bug)"


# Catalog of all registered rules grouped by category
RULE_CATALOG: Dict[str, List[RuleFunc]] = {
    "algebraic": [
        rule_add_zero,
        rule_sub_zero,
        rule_sub_self,
        rule_mul_one,
        rule_mul_zero,
        rule_add_constant_combine,
        rule_sdiv_by_one,
        rule_neg_sub,
    ],
    "bitwise": [
        rule_and_self,
        rule_or_self,
        rule_xor_self,
        rule_and_zero,
        rule_or_zero,
        rule_and_all_ones,
        rule_or_all_ones,
        rule_double_not,
        rule_absorption_and_or,
        rule_and_not_self,
    ],
    "shift_strength_reduction": [
        rule_mul_pow2_to_shl,
        rule_udiv_pow2_to_lshr,
        rule_shl_zero,
        rule_combine_shifts,
        rule_mul_const_decompose,
    ],
    "comparison": [
        rule_icmp_eq_self,
        rule_icmp_ne_self,
        rule_icmp_ult_zero,
        rule_select_same,
        rule_select_true,
    ],
    "poison_overflow_ub": [
        rule_nsw_overflow_ub,
        rule_nuw_overflow_ub,
        rule_exact_sdiv_poison,
    ],
}
