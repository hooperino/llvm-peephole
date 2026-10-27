; ModuleID = 'data/input_code.c'
source_filename = "data/input_code.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: nounwind uwtable
define dso_local i32 @murmur3_32_scramble(i32 noundef %k) #0 {
entry:
  %k.addr = alloca i32, align 4
  store i32 %k, ptr %k.addr, align 4, !tbaa !5
  %0 = load i32, ptr %k.addr, align 4, !tbaa !5
  %mul = mul i32 %0, -862048943
  store i32 %mul, ptr %k.addr, align 4, !tbaa !5
  %1 = load i32, ptr %k.addr, align 4, !tbaa !5
  %shl = shl i32 %1, 15
  %2 = load i32, ptr %k.addr, align 4, !tbaa !5
  %shr = lshr i32 %2, 17
  %or = or i32 %shl, %shr
  store i32 %or, ptr %k.addr, align 4, !tbaa !5
  %3 = load i32, ptr %k.addr, align 4, !tbaa !5
  %mul1 = mul i32 %3, 461845907
  store i32 %mul1, ptr %k.addr, align 4, !tbaa !5
  %4 = load i32, ptr %k.addr, align 4, !tbaa !5
  ret i32 %4
}

; Function Attrs: nounwind uwtable
define dso_local i32 @murmur3_32_finalize(i32 noundef %h) #0 {
entry:
  %h.addr = alloca i32, align 4
  store i32 %h, ptr %h.addr, align 4, !tbaa !5
  %0 = load i32, ptr %h.addr, align 4, !tbaa !5
  %shr = lshr i32 %0, 16
  %1 = load i32, ptr %h.addr, align 4, !tbaa !5
  %xor = xor i32 %1, %shr
  store i32 %xor, ptr %h.addr, align 4, !tbaa !5
  %2 = load i32, ptr %h.addr, align 4, !tbaa !5
  %mul = mul i32 %2, -2048144789
  store i32 %mul, ptr %h.addr, align 4, !tbaa !5
  %3 = load i32, ptr %h.addr, align 4, !tbaa !5
  %shr1 = lshr i32 %3, 13
  %4 = load i32, ptr %h.addr, align 4, !tbaa !5
  %xor2 = xor i32 %4, %shr1
  store i32 %xor2, ptr %h.addr, align 4, !tbaa !5
  %5 = load i32, ptr %h.addr, align 4, !tbaa !5
  %mul3 = mul i32 %5, -1028477387
  store i32 %mul3, ptr %h.addr, align 4, !tbaa !5
  %6 = load i32, ptr %h.addr, align 4, !tbaa !5
  %shr4 = lshr i32 %6, 16
  %7 = load i32, ptr %h.addr, align 4, !tbaa !5
  %xor5 = xor i32 %7, %shr4
  store i32 %xor5, ptr %h.addr, align 4, !tbaa !5
  %8 = load i32, ptr %h.addr, align 4, !tbaa !5
  ret i32 %8
}

; Function Attrs: nounwind uwtable
define dso_local i64 @splitmix64_next(ptr noundef %state) #0 {
entry:
  %state.addr = alloca ptr, align 8
  %z = alloca i64, align 8
  store ptr %state, ptr %state.addr, align 8, !tbaa !9
  call void @llvm.lifetime.start.p0(i64 8, ptr %z) #2
  %0 = load ptr, ptr %state.addr, align 8, !tbaa !9
  %1 = load i64, ptr %0, align 8, !tbaa !12
  %add = add i64 %1, -7046029254386353131
  store i64 %add, ptr %0, align 8, !tbaa !12
  store i64 %add, ptr %z, align 8, !tbaa !12
  %2 = load i64, ptr %z, align 8, !tbaa !12
  %3 = load i64, ptr %z, align 8, !tbaa !12
  %shr = lshr i64 %3, 30
  %xor = xor i64 %2, %shr
  %mul = mul i64 %xor, -4658895280553007687
  store i64 %mul, ptr %z, align 8, !tbaa !12
  %4 = load i64, ptr %z, align 8, !tbaa !12
  %5 = load i64, ptr %z, align 8, !tbaa !12
  %shr1 = lshr i64 %5, 27
  %xor2 = xor i64 %4, %shr1
  %mul3 = mul i64 %xor2, -7723592293110705685
  store i64 %mul3, ptr %z, align 8, !tbaa !12
  %6 = load i64, ptr %z, align 8, !tbaa !12
  %7 = load i64, ptr %z, align 8, !tbaa !12
  %shr4 = lshr i64 %7, 31
  %xor5 = xor i64 %6, %shr4
  call void @llvm.lifetime.end.p0(i64 8, ptr %z) #2
  ret i64 %xor5
}

; Function Attrs: nocallback nofree nosync nounwind willreturn memory(argmem: readwrite)
declare void @llvm.lifetime.start.p0(i64 immarg, ptr captures(none)) #1

; Function Attrs: nocallback nofree nosync nounwind willreturn memory(argmem: readwrite)
declare void @llvm.lifetime.end.p0(i64 immarg, ptr captures(none)) #1

; Function Attrs: nounwind uwtable
define dso_local void @chacha_quarter_round(ptr noundef %a, ptr noundef %b, ptr noundef %c, ptr noundef %d) #0 {
entry:
  %a.addr = alloca ptr, align 8
  %b.addr = alloca ptr, align 8
  %c.addr = alloca ptr, align 8
  %d.addr = alloca ptr, align 8
  store ptr %a, ptr %a.addr, align 8, !tbaa !14
  store ptr %b, ptr %b.addr, align 8, !tbaa !14
  store ptr %c, ptr %c.addr, align 8, !tbaa !14
  store ptr %d, ptr %d.addr, align 8, !tbaa !14
  %0 = load ptr, ptr %b.addr, align 8, !tbaa !14
  %1 = load i32, ptr %0, align 4, !tbaa !5
  %2 = load ptr, ptr %a.addr, align 8, !tbaa !14
  %3 = load i32, ptr %2, align 4, !tbaa !5
  %add = add i32 %3, %1
  store i32 %add, ptr %2, align 4, !tbaa !5
  %4 = load ptr, ptr %a.addr, align 8, !tbaa !14
  %5 = load i32, ptr %4, align 4, !tbaa !5
  %6 = load ptr, ptr %d.addr, align 8, !tbaa !14
  %7 = load i32, ptr %6, align 4, !tbaa !5
  %xor = xor i32 %7, %5
  store i32 %xor, ptr %6, align 4, !tbaa !5
  %8 = load ptr, ptr %d.addr, align 8, !tbaa !14
  %9 = load i32, ptr %8, align 4, !tbaa !5
  %shl = shl i32 %9, 16
  %10 = load ptr, ptr %d.addr, align 8, !tbaa !14
  %11 = load i32, ptr %10, align 4, !tbaa !5
  %shr = lshr i32 %11, 16
  %or = or i32 %shl, %shr
  %12 = load ptr, ptr %d.addr, align 8, !tbaa !14
  store i32 %or, ptr %12, align 4, !tbaa !5
  %13 = load ptr, ptr %d.addr, align 8, !tbaa !14
  %14 = load i32, ptr %13, align 4, !tbaa !5
  %15 = load ptr, ptr %c.addr, align 8, !tbaa !14
  %16 = load i32, ptr %15, align 4, !tbaa !5
  %add1 = add i32 %16, %14
  store i32 %add1, ptr %15, align 4, !tbaa !5
  %17 = load ptr, ptr %c.addr, align 8, !tbaa !14
  %18 = load i32, ptr %17, align 4, !tbaa !5
  %19 = load ptr, ptr %b.addr, align 8, !tbaa !14
  %20 = load i32, ptr %19, align 4, !tbaa !5
  %xor2 = xor i32 %20, %18
  store i32 %xor2, ptr %19, align 4, !tbaa !5
  %21 = load ptr, ptr %b.addr, align 8, !tbaa !14
  %22 = load i32, ptr %21, align 4, !tbaa !5
  %shl3 = shl i32 %22, 12
  %23 = load ptr, ptr %b.addr, align 8, !tbaa !14
  %24 = load i32, ptr %23, align 4, !tbaa !5
  %shr4 = lshr i32 %24, 20
  %or5 = or i32 %shl3, %shr4
  %25 = load ptr, ptr %b.addr, align 8, !tbaa !14
  store i32 %or5, ptr %25, align 4, !tbaa !5
  %26 = load ptr, ptr %b.addr, align 8, !tbaa !14
  %27 = load i32, ptr %26, align 4, !tbaa !5
  %28 = load ptr, ptr %a.addr, align 8, !tbaa !14
  %29 = load i32, ptr %28, align 4, !tbaa !5
  %add6 = add i32 %29, %27
  store i32 %add6, ptr %28, align 4, !tbaa !5
  %30 = load ptr, ptr %a.addr, align 8, !tbaa !14
  %31 = load i32, ptr %30, align 4, !tbaa !5
  %32 = load ptr, ptr %d.addr, align 8, !tbaa !14
  %33 = load i32, ptr %32, align 4, !tbaa !5
  %xor7 = xor i32 %33, %31
  store i32 %xor7, ptr %32, align 4, !tbaa !5
  %34 = load ptr, ptr %d.addr, align 8, !tbaa !14
  %35 = load i32, ptr %34, align 4, !tbaa !5
  %shl8 = shl i32 %35, 8
  %36 = load ptr, ptr %d.addr, align 8, !tbaa !14
  %37 = load i32, ptr %36, align 4, !tbaa !5
  %shr9 = lshr i32 %37, 24
  %or10 = or i32 %shl8, %shr9
  %38 = load ptr, ptr %d.addr, align 8, !tbaa !14
  store i32 %or10, ptr %38, align 4, !tbaa !5
  %39 = load ptr, ptr %d.addr, align 8, !tbaa !14
  %40 = load i32, ptr %39, align 4, !tbaa !5
  %41 = load ptr, ptr %c.addr, align 8, !tbaa !14
  %42 = load i32, ptr %41, align 4, !tbaa !5
  %add11 = add i32 %42, %40
  store i32 %add11, ptr %41, align 4, !tbaa !5
  %43 = load ptr, ptr %c.addr, align 8, !tbaa !14
  %44 = load i32, ptr %43, align 4, !tbaa !5
  %45 = load ptr, ptr %b.addr, align 8, !tbaa !14
  %46 = load i32, ptr %45, align 4, !tbaa !5
  %xor12 = xor i32 %46, %44
  store i32 %xor12, ptr %45, align 4, !tbaa !5
  %47 = load ptr, ptr %b.addr, align 8, !tbaa !14
  %48 = load i32, ptr %47, align 4, !tbaa !5
  %shl13 = shl i32 %48, 7
  %49 = load ptr, ptr %b.addr, align 8, !tbaa !14
  %50 = load i32, ptr %49, align 4, !tbaa !5
  %shr14 = lshr i32 %50, 25
  %or15 = or i32 %shl13, %shr14
  %51 = load ptr, ptr %b.addr, align 8, !tbaa !14
  store i32 %or15, ptr %51, align 4, !tbaa !5
  ret void
}

; Function Attrs: nounwind uwtable
define dso_local i32 @q16_mul(i32 noundef %a, i32 noundef %b) #0 {
entry:
  %a.addr = alloca i32, align 4
  %b.addr = alloca i32, align 4
  %temp = alloca i64, align 8
  store i32 %a, ptr %a.addr, align 4, !tbaa !5
  store i32 %b, ptr %b.addr, align 4, !tbaa !5
  call void @llvm.lifetime.start.p0(i64 8, ptr %temp) #2
  %0 = load i32, ptr %a.addr, align 4, !tbaa !5
  %conv = sext i32 %0 to i64
  %1 = load i32, ptr %b.addr, align 4, !tbaa !5
  %conv1 = sext i32 %1 to i64
  %mul = mul nsw i64 %conv, %conv1
  store i64 %mul, ptr %temp, align 8, !tbaa !12
  %2 = load i64, ptr %temp, align 8, !tbaa !12
  %shr = ashr i64 %2, 16
  %conv2 = trunc i64 %shr to i32
  call void @llvm.lifetime.end.p0(i64 8, ptr %temp) #2
  ret i32 %conv2
}

; Function Attrs: nounwind uwtable
define dso_local i32 @q16_div_pow2(i32 noundef %a, i32 noundef %shift) #0 {
entry:
  %a.addr = alloca i32, align 4
  %shift.addr = alloca i32, align 4
  store i32 %a, ptr %a.addr, align 4, !tbaa !5
  store i32 %shift, ptr %shift.addr, align 4, !tbaa !5
  %0 = load i32, ptr %a.addr, align 4, !tbaa !5
  %1 = load i32, ptr %shift.addr, align 4, !tbaa !5
  %shr = ashr i32 %0, %1
  ret i32 %shr
}

; Function Attrs: nounwind uwtable
define dso_local i32 @dsp_biquad_process(i32 noundef %x, i32 noundef %b0, i32 noundef %b1, i32 noundef %b2, i32 noundef %a1, i32 noundef %a2, ptr noundef %w1, ptr noundef %w2) #0 {
entry:
  %x.addr = alloca i32, align 4
  %b0.addr = alloca i32, align 4
  %b1.addr = alloca i32, align 4
  %b2.addr = alloca i32, align 4
  %a1.addr = alloca i32, align 4
  %a2.addr = alloca i32, align 4
  %w1.addr = alloca ptr, align 8
  %w2.addr = alloca ptr, align 8
  %w0 = alloca i32, align 4
  %y = alloca i32, align 4
  store i32 %x, ptr %x.addr, align 4, !tbaa !5
  store i32 %b0, ptr %b0.addr, align 4, !tbaa !5
  store i32 %b1, ptr %b1.addr, align 4, !tbaa !5
  store i32 %b2, ptr %b2.addr, align 4, !tbaa !5
  store i32 %a1, ptr %a1.addr, align 4, !tbaa !5
  store i32 %a2, ptr %a2.addr, align 4, !tbaa !5
  store ptr %w1, ptr %w1.addr, align 8, !tbaa !14
  store ptr %w2, ptr %w2.addr, align 8, !tbaa !14
  call void @llvm.lifetime.start.p0(i64 4, ptr %w0) #2
  %0 = load i32, ptr %x.addr, align 4, !tbaa !5
  %1 = load i32, ptr %a1.addr, align 4, !tbaa !5
  %2 = load ptr, ptr %w1.addr, align 8, !tbaa !14
  %3 = load i32, ptr %2, align 4, !tbaa !5
  %mul = mul nsw i32 %1, %3
  %shr = ashr i32 %mul, 14
  %sub = sub nsw i32 %0, %shr
  %4 = load i32, ptr %a2.addr, align 4, !tbaa !5
  %5 = load ptr, ptr %w2.addr, align 8, !tbaa !14
  %6 = load i32, ptr %5, align 4, !tbaa !5
  %mul1 = mul nsw i32 %4, %6
  %shr2 = ashr i32 %mul1, 14
  %sub3 = sub nsw i32 %sub, %shr2
  store i32 %sub3, ptr %w0, align 4, !tbaa !5
  call void @llvm.lifetime.start.p0(i64 4, ptr %y) #2
  %7 = load i32, ptr %b0.addr, align 4, !tbaa !5
  %8 = load i32, ptr %w0, align 4, !tbaa !5
  %mul4 = mul nsw i32 %7, %8
  %shr5 = ashr i32 %mul4, 14
  %9 = load i32, ptr %b1.addr, align 4, !tbaa !5
  %10 = load ptr, ptr %w1.addr, align 8, !tbaa !14
  %11 = load i32, ptr %10, align 4, !tbaa !5
  %mul6 = mul nsw i32 %9, %11
  %shr7 = ashr i32 %mul6, 14
  %add = add nsw i32 %shr5, %shr7
  %12 = load i32, ptr %b2.addr, align 4, !tbaa !5
  %13 = load ptr, ptr %w2.addr, align 8, !tbaa !14
  %14 = load i32, ptr %13, align 4, !tbaa !5
  %mul8 = mul nsw i32 %12, %14
  %shr9 = ashr i32 %mul8, 14
  %add10 = add nsw i32 %add, %shr9
  store i32 %add10, ptr %y, align 4, !tbaa !5
  %15 = load ptr, ptr %w1.addr, align 8, !tbaa !14
  %16 = load i32, ptr %15, align 4, !tbaa !5
  %17 = load ptr, ptr %w2.addr, align 8, !tbaa !14
  store i32 %16, ptr %17, align 4, !tbaa !5
  %18 = load i32, ptr %w0, align 4, !tbaa !5
  %19 = load ptr, ptr %w1.addr, align 8, !tbaa !14
  store i32 %18, ptr %19, align 4, !tbaa !5
  %20 = load i32, ptr %y, align 4, !tbaa !5
  call void @llvm.lifetime.end.p0(i64 4, ptr %y) #2
  call void @llvm.lifetime.end.p0(i64 4, ptr %w0) #2
  ret i32 %20
}

; Function Attrs: nounwind uwtable
define dso_local i32 @dsp_scale_by_factors(i32 noundef %val) #0 {
entry:
  %val.addr = alloca i32, align 4
  %s1 = alloca i32, align 4
  %s2 = alloca i32, align 4
  %s3 = alloca i32, align 4
  %s4 = alloca i32, align 4
  %s5 = alloca i32, align 4
  store i32 %val, ptr %val.addr, align 4, !tbaa !5
  call void @llvm.lifetime.start.p0(i64 4, ptr %s1) #2
  %0 = load i32, ptr %val.addr, align 4, !tbaa !5
  %mul = mul nsw i32 %0, 8
  store i32 %mul, ptr %s1, align 4, !tbaa !5
  call void @llvm.lifetime.start.p0(i64 4, ptr %s2) #2
  %1 = load i32, ptr %s1, align 4, !tbaa !5
  %mul1 = mul nsw i32 %1, 1
  store i32 %mul1, ptr %s2, align 4, !tbaa !5
  call void @llvm.lifetime.start.p0(i64 4, ptr %s3) #2
  %2 = load i32, ptr %s2, align 4, !tbaa !5
  %add = add nsw i32 %2, 0
  store i32 %add, ptr %s3, align 4, !tbaa !5
  call void @llvm.lifetime.start.p0(i64 4, ptr %s4) #2
  %3 = load i32, ptr %s3, align 4, !tbaa !5
  %div = sdiv i32 %3, 16
  store i32 %div, ptr %s4, align 4, !tbaa !5
  call void @llvm.lifetime.start.p0(i64 4, ptr %s5) #2
  %4 = load i32, ptr %s4, align 4, !tbaa !5
  %and = and i32 %4, -1
  store i32 %and, ptr %s5, align 4, !tbaa !5
  %5 = load i32, ptr %s5, align 4, !tbaa !5
  call void @llvm.lifetime.end.p0(i64 4, ptr %s5) #2
  call void @llvm.lifetime.end.p0(i64 4, ptr %s4) #2
  call void @llvm.lifetime.end.p0(i64 4, ptr %s3) #2
  call void @llvm.lifetime.end.p0(i64 4, ptr %s2) #2
  call void @llvm.lifetime.end.p0(i64 4, ptr %s1) #2
  ret i32 %5
}

; Function Attrs: nounwind uwtable
define dso_local i32 @blend_pixels_alpha(i32 noundef %fg, i32 noundef %bg, i8 noundef zeroext %alpha) #0 {
entry:
  %fg.addr = alloca i32, align 4
  %bg.addr = alloca i32, align 4
  %alpha.addr = alloca i8, align 1
  %rb_fg = alloca i32, align 4
  %g_fg = alloca i32, align 4
  %rb_bg = alloca i32, align 4
  %g_bg = alloca i32, align 4
  %rb = alloca i32, align 4
  %g = alloca i32, align 4
  store i32 %fg, ptr %fg.addr, align 4, !tbaa !5
  store i32 %bg, ptr %bg.addr, align 4, !tbaa !5
  store i8 %alpha, ptr %alpha.addr, align 1, !tbaa !16
  call void @llvm.lifetime.start.p0(i64 4, ptr %rb_fg) #2
  %0 = load i32, ptr %fg.addr, align 4, !tbaa !5
  %and = and i32 %0, 16711935
  store i32 %and, ptr %rb_fg, align 4, !tbaa !5
  call void @llvm.lifetime.start.p0(i64 4, ptr %g_fg) #2
  %1 = load i32, ptr %fg.addr, align 4, !tbaa !5
  %and1 = and i32 %1, 65280
  store i32 %and1, ptr %g_fg, align 4, !tbaa !5
  call void @llvm.lifetime.start.p0(i64 4, ptr %rb_bg) #2
  %2 = load i32, ptr %bg.addr, align 4, !tbaa !5
  %and2 = and i32 %2, 16711935
  store i32 %and2, ptr %rb_bg, align 4, !tbaa !5
  call void @llvm.lifetime.start.p0(i64 4, ptr %g_bg) #2
  %3 = load i32, ptr %bg.addr, align 4, !tbaa !5
  %and3 = and i32 %3, 65280
  store i32 %and3, ptr %g_bg, align 4, !tbaa !5
  call void @llvm.lifetime.start.p0(i64 4, ptr %rb) #2
  %4 = load i32, ptr %rb_fg, align 4, !tbaa !5
  %5 = load i8, ptr %alpha.addr, align 1, !tbaa !16
  %conv = zext i8 %5 to i32
  %mul = mul i32 %4, %conv
  %6 = load i32, ptr %rb_bg, align 4, !tbaa !5
  %7 = load i8, ptr %alpha.addr, align 1, !tbaa !16
  %conv4 = zext i8 %7 to i32
  %sub = sub nsw i32 256, %conv4
  %mul5 = mul i32 %6, %sub
  %add = add i32 %mul, %mul5
  %shr = lshr i32 %add, 8
  %and6 = and i32 %shr, 16711935
  store i32 %and6, ptr %rb, align 4, !tbaa !5
  call void @llvm.lifetime.start.p0(i64 4, ptr %g) #2
  %8 = load i32, ptr %g_fg, align 4, !tbaa !5
  %9 = load i8, ptr %alpha.addr, align 1, !tbaa !16
  %conv7 = zext i8 %9 to i32
  %mul8 = mul i32 %8, %conv7
  %10 = load i32, ptr %g_bg, align 4, !tbaa !5
  %11 = load i8, ptr %alpha.addr, align 1, !tbaa !16
  %conv9 = zext i8 %11 to i32
  %sub10 = sub nsw i32 256, %conv9
  %mul11 = mul i32 %10, %sub10
  %add12 = add i32 %mul8, %mul11
  %shr13 = lshr i32 %add12, 8
  %and14 = and i32 %shr13, 65280
  store i32 %and14, ptr %g, align 4, !tbaa !5
  %12 = load i32, ptr %rb, align 4, !tbaa !5
  %13 = load i32, ptr %g, align 4, !tbaa !5
  %or = or i32 %12, %13
  call void @llvm.lifetime.end.p0(i64 4, ptr %g) #2
  call void @llvm.lifetime.end.p0(i64 4, ptr %rb) #2
  call void @llvm.lifetime.end.p0(i64 4, ptr %g_bg) #2
  call void @llvm.lifetime.end.p0(i64 4, ptr %rb_bg) #2
  call void @llvm.lifetime.end.p0(i64 4, ptr %g_fg) #2
  call void @llvm.lifetime.end.p0(i64 4, ptr %rb_fg) #2
  ret i32 %or
}

; Function Attrs: nounwind uwtable
define dso_local zeroext i16 @pack_rgb888_to_rgb565(i8 noundef zeroext %r, i8 noundef zeroext %g, i8 noundef zeroext %b) #0 {
entry:
  %r.addr = alloca i8, align 1
  %g.addr = alloca i8, align 1
  %b.addr = alloca i8, align 1
  %r5 = alloca i16, align 2
  %g6 = alloca i16, align 2
  %b5 = alloca i16, align 2
  store i8 %r, ptr %r.addr, align 1, !tbaa !16
  store i8 %g, ptr %g.addr, align 1, !tbaa !16
  store i8 %b, ptr %b.addr, align 1, !tbaa !16
  call void @llvm.lifetime.start.p0(i64 2, ptr %r5) #2
  %0 = load i8, ptr %r.addr, align 1, !tbaa !16
  %conv = zext i8 %0 to i32
  %shr = ashr i32 %conv, 3
  %and = and i32 %shr, 31
  %conv1 = trunc i32 %and to i16
  store i16 %conv1, ptr %r5, align 2, !tbaa !17
  call void @llvm.lifetime.start.p0(i64 2, ptr %g6) #2
  %1 = load i8, ptr %g.addr, align 1, !tbaa !16
  %conv2 = zext i8 %1 to i32
  %shr3 = ashr i32 %conv2, 2
  %and4 = and i32 %shr3, 63
  %conv5 = trunc i32 %and4 to i16
  store i16 %conv5, ptr %g6, align 2, !tbaa !17
  call void @llvm.lifetime.start.p0(i64 2, ptr %b5) #2
  %2 = load i8, ptr %b.addr, align 1, !tbaa !16
  %conv6 = zext i8 %2 to i32
  %shr7 = ashr i32 %conv6, 3
  %and8 = and i32 %shr7, 31
  %conv9 = trunc i32 %and8 to i16
  store i16 %conv9, ptr %b5, align 2, !tbaa !17
  %3 = load i16, ptr %r5, align 2, !tbaa !17
  %conv10 = zext i16 %3 to i32
  %shl = shl i32 %conv10, 11
  %4 = load i16, ptr %g6, align 2, !tbaa !17
  %conv11 = zext i16 %4 to i32
  %shl12 = shl i32 %conv11, 5
  %or = or i32 %shl, %shl12
  %5 = load i16, ptr %b5, align 2, !tbaa !17
  %conv13 = zext i16 %5 to i32
  %or14 = or i32 %or, %conv13
  %conv15 = trunc i32 %or14 to i16
  call void @llvm.lifetime.end.p0(i64 2, ptr %b5) #2
  call void @llvm.lifetime.end.p0(i64 2, ptr %g6) #2
  call void @llvm.lifetime.end.p0(i64 2, ptr %r5) #2
  ret i16 %conv15
}

; Function Attrs: nounwind uwtable
define dso_local i32 @unpack_rgb565_to_rgb888(i16 noundef zeroext %rgb565) #0 {
entry:
  %rgb565.addr = alloca i16, align 2
  %r = alloca i32, align 4
  %g = alloca i32, align 4
  %b = alloca i32, align 4
  %r8 = alloca i32, align 4
  %g8 = alloca i32, align 4
  %b8 = alloca i32, align 4
  store i16 %rgb565, ptr %rgb565.addr, align 2, !tbaa !17
  call void @llvm.lifetime.start.p0(i64 4, ptr %r) #2
  %0 = load i16, ptr %rgb565.addr, align 2, !tbaa !17
  %conv = zext i16 %0 to i32
  %shr = ashr i32 %conv, 11
  %and = and i32 %shr, 31
  store i32 %and, ptr %r, align 4, !tbaa !5
  call void @llvm.lifetime.start.p0(i64 4, ptr %g) #2
  %1 = load i16, ptr %rgb565.addr, align 2, !tbaa !17
  %conv1 = zext i16 %1 to i32
  %shr2 = ashr i32 %conv1, 5
  %and3 = and i32 %shr2, 63
  store i32 %and3, ptr %g, align 4, !tbaa !5
  call void @llvm.lifetime.start.p0(i64 4, ptr %b) #2
  %2 = load i16, ptr %rgb565.addr, align 2, !tbaa !17
  %conv4 = zext i16 %2 to i32
  %and5 = and i32 %conv4, 31
  store i32 %and5, ptr %b, align 4, !tbaa !5
  call void @llvm.lifetime.start.p0(i64 4, ptr %r8) #2
  %3 = load i32, ptr %r, align 4, !tbaa !5
  %mul = mul i32 %3, 527
  %add = add i32 %mul, 23
  %shr6 = lshr i32 %add, 6
  store i32 %shr6, ptr %r8, align 4, !tbaa !5
  call void @llvm.lifetime.start.p0(i64 4, ptr %g8) #2
  %4 = load i32, ptr %g, align 4, !tbaa !5
  %mul7 = mul i32 %4, 259
  %add8 = add i32 %mul7, 33
  %shr9 = lshr i32 %add8, 6
  store i32 %shr9, ptr %g8, align 4, !tbaa !5
  call void @llvm.lifetime.start.p0(i64 4, ptr %b8) #2
  %5 = load i32, ptr %b, align 4, !tbaa !5
  %mul10 = mul i32 %5, 527
  %add11 = add i32 %mul10, 23
  %shr12 = lshr i32 %add11, 6
  store i32 %shr12, ptr %b8, align 4, !tbaa !5
  %6 = load i32, ptr %r8, align 4, !tbaa !5
  %shl = shl i32 %6, 16
  %7 = load i32, ptr %g8, align 4, !tbaa !5
  %shl13 = shl i32 %7, 8
  %or = or i32 %shl, %shl13
  %8 = load i32, ptr %b8, align 4, !tbaa !5
  %or14 = or i32 %or, %8
  call void @llvm.lifetime.end.p0(i64 4, ptr %b8) #2
  call void @llvm.lifetime.end.p0(i64 4, ptr %g8) #2
  call void @llvm.lifetime.end.p0(i64 4, ptr %r8) #2
  call void @llvm.lifetime.end.p0(i64 4, ptr %b) #2
  call void @llvm.lifetime.end.p0(i64 4, ptr %g) #2
  call void @llvm.lifetime.end.p0(i64 4, ptr %r) #2
  ret i32 %or14
}

; Function Attrs: nounwind uwtable
define dso_local i32 @bit_isolate_lowest_set(i32 noundef %x) #0 {
entry:
  %x.addr = alloca i32, align 4
  store i32 %x, ptr %x.addr, align 4, !tbaa !5
  %0 = load i32, ptr %x.addr, align 4, !tbaa !5
  %1 = load i32, ptr %x.addr, align 4, !tbaa !5
  %sub = sub i32 0, %1
  %and = and i32 %0, %sub
  ret i32 %and
}

; Function Attrs: nounwind uwtable
define dso_local i32 @bit_clear_lowest_set(i32 noundef %x) #0 {
entry:
  %x.addr = alloca i32, align 4
  store i32 %x, ptr %x.addr, align 4, !tbaa !5
  %0 = load i32, ptr %x.addr, align 4, !tbaa !5
  %1 = load i32, ptr %x.addr, align 4, !tbaa !5
  %sub = sub i32 %1, 1
  %and = and i32 %0, %sub
  ret i32 %and
}

; Function Attrs: nounwind uwtable
define dso_local zeroext i1 @bit_is_power_of_two(i32 noundef %x) #0 {
entry:
  %x.addr = alloca i32, align 4
  store i32 %x, ptr %x.addr, align 4, !tbaa !5
  %0 = load i32, ptr %x.addr, align 4, !tbaa !5
  %cmp = icmp ne i32 %0, 0
  br i1 %cmp, label %land.rhs, label %land.end

land.rhs:                                         ; preds = %entry
  %1 = load i32, ptr %x.addr, align 4, !tbaa !5
  %2 = load i32, ptr %x.addr, align 4, !tbaa !5
  %sub = sub i32 %2, 1
  %and = and i32 %1, %sub
  %cmp1 = icmp eq i32 %and, 0
  br label %land.end

land.end:                                         ; preds = %land.rhs, %entry
  %3 = phi i1 [ false, %entry ], [ %cmp1, %land.rhs ]
  ret i1 %3
}

; Function Attrs: nounwind uwtable
define dso_local i32 @bit_mask_trailing_zeros(i32 noundef %x) #0 {
entry:
  %x.addr = alloca i32, align 4
  store i32 %x, ptr %x.addr, align 4, !tbaa !5
  %0 = load i32, ptr %x.addr, align 4, !tbaa !5
  %sub = sub i32 %0, 1
  %1 = load i32, ptr %x.addr, align 4, !tbaa !5
  %not = xor i32 %1, -1
  %and = and i32 %sub, %not
  ret i32 %and
}

; Function Attrs: nounwind uwtable
define dso_local i32 @bit_reverse_32(i32 noundef %x) #0 {
entry:
  %x.addr = alloca i32, align 4
  store i32 %x, ptr %x.addr, align 4, !tbaa !5
  %0 = load i32, ptr %x.addr, align 4, !tbaa !5
  %and = and i32 %0, -1431655766
  %shr = lshr i32 %and, 1
  %1 = load i32, ptr %x.addr, align 4, !tbaa !5
  %and1 = and i32 %1, 1431655765
  %shl = shl i32 %and1, 1
  %or = or i32 %shr, %shl
  store i32 %or, ptr %x.addr, align 4, !tbaa !5
  %2 = load i32, ptr %x.addr, align 4, !tbaa !5
  %and2 = and i32 %2, -858993460
  %shr3 = lshr i32 %and2, 2
  %3 = load i32, ptr %x.addr, align 4, !tbaa !5
  %and4 = and i32 %3, 858993459
  %shl5 = shl i32 %and4, 2
  %or6 = or i32 %shr3, %shl5
  store i32 %or6, ptr %x.addr, align 4, !tbaa !5
  %4 = load i32, ptr %x.addr, align 4, !tbaa !5
  %and7 = and i32 %4, -252645136
  %shr8 = lshr i32 %and7, 4
  %5 = load i32, ptr %x.addr, align 4, !tbaa !5
  %and9 = and i32 %5, 252645135
  %shl10 = shl i32 %and9, 4
  %or11 = or i32 %shr8, %shl10
  store i32 %or11, ptr %x.addr, align 4, !tbaa !5
  %6 = load i32, ptr %x.addr, align 4, !tbaa !5
  %and12 = and i32 %6, -16711936
  %shr13 = lshr i32 %and12, 8
  %7 = load i32, ptr %x.addr, align 4, !tbaa !5
  %and14 = and i32 %7, 16711935
  %shl15 = shl i32 %and14, 8
  %or16 = or i32 %shr13, %shl15
  store i32 %or16, ptr %x.addr, align 4, !tbaa !5
  %8 = load i32, ptr %x.addr, align 4, !tbaa !5
  %shr17 = lshr i32 %8, 16
  %9 = load i32, ptr %x.addr, align 4, !tbaa !5
  %shl18 = shl i32 %9, 16
  %or19 = or i32 %shr17, %shl18
  ret i32 %or19
}

; Function Attrs: nounwind uwtable
define dso_local i32 @bit_parity(i32 noundef %x) #0 {
entry:
  %x.addr = alloca i32, align 4
  store i32 %x, ptr %x.addr, align 4, !tbaa !5
  %0 = load i32, ptr %x.addr, align 4, !tbaa !5
  %shr = lshr i32 %0, 16
  %1 = load i32, ptr %x.addr, align 4, !tbaa !5
  %xor = xor i32 %1, %shr
  store i32 %xor, ptr %x.addr, align 4, !tbaa !5
  %2 = load i32, ptr %x.addr, align 4, !tbaa !5
  %shr1 = lshr i32 %2, 8
  %3 = load i32, ptr %x.addr, align 4, !tbaa !5
  %xor2 = xor i32 %3, %shr1
  store i32 %xor2, ptr %x.addr, align 4, !tbaa !5
  %4 = load i32, ptr %x.addr, align 4, !tbaa !5
  %shr3 = lshr i32 %4, 4
  %5 = load i32, ptr %x.addr, align 4, !tbaa !5
  %xor4 = xor i32 %5, %shr3
  store i32 %xor4, ptr %x.addr, align 4, !tbaa !5
  %6 = load i32, ptr %x.addr, align 4, !tbaa !5
  %shr5 = lshr i32 %6, 2
  %7 = load i32, ptr %x.addr, align 4, !tbaa !5
  %xor6 = xor i32 %7, %shr5
  store i32 %xor6, ptr %x.addr, align 4, !tbaa !5
  %8 = load i32, ptr %x.addr, align 4, !tbaa !5
  %shr7 = lshr i32 %8, 1
  %9 = load i32, ptr %x.addr, align 4, !tbaa !5
  %xor8 = xor i32 %9, %shr7
  store i32 %xor8, ptr %x.addr, align 4, !tbaa !5
  %10 = load i32, ptr %x.addr, align 4, !tbaa !5
  %and = and i32 %10, 1
  ret i32 %and
}

; Function Attrs: nounwind uwtable
define dso_local i32 @branchless_abs(i32 noundef %x) #0 {
entry:
  %x.addr = alloca i32, align 4
  %mask = alloca i32, align 4
  store i32 %x, ptr %x.addr, align 4, !tbaa !5
  call void @llvm.lifetime.start.p0(i64 4, ptr %mask) #2
  %0 = load i32, ptr %x.addr, align 4, !tbaa !5
  %shr = ashr i32 %0, 31
  store i32 %shr, ptr %mask, align 4, !tbaa !5
  %1 = load i32, ptr %x.addr, align 4, !tbaa !5
  %2 = load i32, ptr %mask, align 4, !tbaa !5
  %xor = xor i32 %1, %2
  %3 = load i32, ptr %mask, align 4, !tbaa !5
  %sub = sub nsw i32 %xor, %3
  call void @llvm.lifetime.end.p0(i64 4, ptr %mask) #2
  ret i32 %sub
}

; Function Attrs: nounwind uwtable
define dso_local i32 @branchless_clamp(i32 noundef %x, i32 noundef %min_val, i32 noundef %max_val) #0 {
entry:
  %x.addr = alloca i32, align 4
  %min_val.addr = alloca i32, align 4
  %max_val.addr = alloca i32, align 4
  %t = alloca i32, align 4
  store i32 %x, ptr %x.addr, align 4, !tbaa !5
  store i32 %min_val, ptr %min_val.addr, align 4, !tbaa !5
  store i32 %max_val, ptr %max_val.addr, align 4, !tbaa !5
  call void @llvm.lifetime.start.p0(i64 4, ptr %t) #2
  %0 = load i32, ptr %x.addr, align 4, !tbaa !5
  %1 = load i32, ptr %min_val.addr, align 4, !tbaa !5
  %cmp = icmp slt i32 %0, %1
  br i1 %cmp, label %cond.true, label %cond.false

cond.true:                                        ; preds = %entry
  %2 = load i32, ptr %min_val.addr, align 4, !tbaa !5
  br label %cond.end

cond.false:                                       ; preds = %entry
  %3 = load i32, ptr %x.addr, align 4, !tbaa !5
  br label %cond.end

cond.end:                                         ; preds = %cond.false, %cond.true
  %cond = phi i32 [ %2, %cond.true ], [ %3, %cond.false ]
  store i32 %cond, ptr %t, align 4, !tbaa !5
  %4 = load i32, ptr %t, align 4, !tbaa !5
  %5 = load i32, ptr %max_val.addr, align 4, !tbaa !5
  %cmp1 = icmp sgt i32 %4, %5
  br i1 %cmp1, label %cond.true2, label %cond.false3

cond.true2:                                       ; preds = %cond.end
  %6 = load i32, ptr %max_val.addr, align 4, !tbaa !5
  br label %cond.end4

cond.false3:                                      ; preds = %cond.end
  %7 = load i32, ptr %t, align 4, !tbaa !5
  br label %cond.end4

cond.end4:                                        ; preds = %cond.false3, %cond.true2
  %cond5 = phi i32 [ %6, %cond.true2 ], [ %7, %cond.false3 ]
  call void @llvm.lifetime.end.p0(i64 4, ptr %t) #2
  ret i32 %cond5
}

; Function Attrs: nounwind uwtable
define dso_local i32 @branchless_sign(i32 noundef %x) #0 {
entry:
  %x.addr = alloca i32, align 4
  store i32 %x, ptr %x.addr, align 4, !tbaa !5
  %0 = load i32, ptr %x.addr, align 4, !tbaa !5
  %shr = ashr i32 %0, 31
  %1 = load i32, ptr %x.addr, align 4, !tbaa !5
  %sub = sub nsw i32 0, %1
  %shr1 = lshr i32 %sub, 31
  %or = or i32 %shr, %shr1
  ret i32 %or
}

; Function Attrs: nounwind uwtable
define dso_local i32 @polynomial_horner_eval(i32 noundef %x, i32 noundef %c0, i32 noundef %c1, i32 noundef %c2, i32 noundef %c3) #0 {
entry:
  %x.addr = alloca i32, align 4
  %c0.addr = alloca i32, align 4
  %c1.addr = alloca i32, align 4
  %c2.addr = alloca i32, align 4
  %c3.addr = alloca i32, align 4
  %t1 = alloca i32, align 4
  %t2 = alloca i32, align 4
  %r = alloca i32, align 4
  store i32 %x, ptr %x.addr, align 4, !tbaa !5
  store i32 %c0, ptr %c0.addr, align 4, !tbaa !5
  store i32 %c1, ptr %c1.addr, align 4, !tbaa !5
  store i32 %c2, ptr %c2.addr, align 4, !tbaa !5
  store i32 %c3, ptr %c3.addr, align 4, !tbaa !5
  call void @llvm.lifetime.start.p0(i64 4, ptr %t1) #2
  %0 = load i32, ptr %c3.addr, align 4, !tbaa !5
  %1 = load i32, ptr %x.addr, align 4, !tbaa !5
  %mul = mul nsw i32 %0, %1
  %2 = load i32, ptr %c2.addr, align 4, !tbaa !5
  %add = add nsw i32 %mul, %2
  store i32 %add, ptr %t1, align 4, !tbaa !5
  call void @llvm.lifetime.start.p0(i64 4, ptr %t2) #2
  %3 = load i32, ptr %t1, align 4, !tbaa !5
  %4 = load i32, ptr %x.addr, align 4, !tbaa !5
  %mul1 = mul nsw i32 %3, %4
  %5 = load i32, ptr %c1.addr, align 4, !tbaa !5
  %add2 = add nsw i32 %mul1, %5
  store i32 %add2, ptr %t2, align 4, !tbaa !5
  call void @llvm.lifetime.start.p0(i64 4, ptr %r) #2
  %6 = load i32, ptr %t2, align 4, !tbaa !5
  %7 = load i32, ptr %x.addr, align 4, !tbaa !5
  %mul3 = mul nsw i32 %6, %7
  %8 = load i32, ptr %c0.addr, align 4, !tbaa !5
  %add4 = add nsw i32 %mul3, %8
  store i32 %add4, ptr %r, align 4, !tbaa !5
  %9 = load i32, ptr %r, align 4, !tbaa !5
  call void @llvm.lifetime.end.p0(i64 4, ptr %r) #2
  call void @llvm.lifetime.end.p0(i64 4, ptr %t2) #2
  call void @llvm.lifetime.end.p0(i64 4, ptr %t1) #2
  ret i32 %9
}

; Function Attrs: nounwind uwtable
define dso_local i32 @matrix_index_calc(i32 noundef %row, i32 noundef %col, i32 noundef %stride) #0 {
entry:
  %row.addr = alloca i32, align 4
  %col.addr = alloca i32, align 4
  %stride.addr = alloca i32, align 4
  %offset1 = alloca i32, align 4
  %offset2 = alloca i32, align 4
  %base = alloca i32, align 4
  store i32 %row, ptr %row.addr, align 4, !tbaa !5
  store i32 %col, ptr %col.addr, align 4, !tbaa !5
  store i32 %stride, ptr %stride.addr, align 4, !tbaa !5
  call void @llvm.lifetime.start.p0(i64 4, ptr %offset1) #2
  %0 = load i32, ptr %row.addr, align 4, !tbaa !5
  %mul = mul i32 %0, 64
  store i32 %mul, ptr %offset1, align 4, !tbaa !5
  call void @llvm.lifetime.start.p0(i64 4, ptr %offset2) #2
  %1 = load i32, ptr %col.addr, align 4, !tbaa !5
  %mul1 = mul i32 %1, 4
  store i32 %mul1, ptr %offset2, align 4, !tbaa !5
  call void @llvm.lifetime.start.p0(i64 4, ptr %base) #2
  %2 = load i32, ptr %offset1, align 4, !tbaa !5
  %add = add i32 %2, 0
  store i32 %add, ptr %base, align 4, !tbaa !5
  %3 = load i32, ptr %base, align 4, !tbaa !5
  %4 = load i32, ptr %offset2, align 4, !tbaa !5
  %add2 = add i32 %3, %4
  call void @llvm.lifetime.end.p0(i64 4, ptr %base) #2
  call void @llvm.lifetime.end.p0(i64 4, ptr %offset2) #2
  call void @llvm.lifetime.end.p0(i64 4, ptr %offset1) #2
  ret i32 %add2
}

; Function Attrs: nounwind uwtable
define dso_local i32 @redundant_math_chain(i32 noundef %a, i32 noundef %b) #0 {
entry:
  %a.addr = alloca i32, align 4
  %b.addr = alloca i32, align 4
  %v1 = alloca i32, align 4
  %v2 = alloca i32, align 4
  %v3 = alloca i32, align 4
  %v4 = alloca i32, align 4
  %v5 = alloca i32, align 4
  %v6 = alloca i32, align 4
  %v7 = alloca i32, align 4
  %v8 = alloca i32, align 4
  store i32 %a, ptr %a.addr, align 4, !tbaa !5
  store i32 %b, ptr %b.addr, align 4, !tbaa !5
  call void @llvm.lifetime.start.p0(i64 4, ptr %v1) #2
  %0 = load i32, ptr %a.addr, align 4, !tbaa !5
  %add = add nsw i32 %0, 0
  store i32 %add, ptr %v1, align 4, !tbaa !5
  call void @llvm.lifetime.start.p0(i64 4, ptr %v2) #2
  %1 = load i32, ptr %v1, align 4, !tbaa !5
  %sub = sub nsw i32 %1, 0
  store i32 %sub, ptr %v2, align 4, !tbaa !5
  call void @llvm.lifetime.start.p0(i64 4, ptr %v3) #2
  %2 = load i32, ptr %v2, align 4, !tbaa !5
  %mul = mul nsw i32 %2, 1
  store i32 %mul, ptr %v3, align 4, !tbaa !5
  call void @llvm.lifetime.start.p0(i64 4, ptr %v4) #2
  %3 = load i32, ptr %v3, align 4, !tbaa !5
  %and = and i32 %3, -1
  store i32 %and, ptr %v4, align 4, !tbaa !5
  call void @llvm.lifetime.start.p0(i64 4, ptr %v5) #2
  %4 = load i32, ptr %v4, align 4, !tbaa !5
  %or = or i32 %4, 0
  store i32 %or, ptr %v5, align 4, !tbaa !5
  call void @llvm.lifetime.start.p0(i64 4, ptr %v6) #2
  %5 = load i32, ptr %v5, align 4, !tbaa !5
  %xor = xor i32 %5, 0
  store i32 %xor, ptr %v6, align 4, !tbaa !5
  call void @llvm.lifetime.start.p0(i64 4, ptr %v7) #2
  %6 = load i32, ptr %v6, align 4, !tbaa !5
  %mul1 = mul nsw i32 %6, 4
  store i32 %mul1, ptr %v7, align 4, !tbaa !5
  call void @llvm.lifetime.start.p0(i64 4, ptr %v8) #2
  %7 = load i32, ptr %v7, align 4, !tbaa !5
  %mul2 = mul nsw i32 %7, 8
  store i32 %mul2, ptr %v8, align 4, !tbaa !5
  %8 = load i32, ptr %v8, align 4, !tbaa !5
  %9 = load i32, ptr %b.addr, align 4, !tbaa !5
  %10 = load i32, ptr %b.addr, align 4, !tbaa !5
  %sub3 = sub nsw i32 %9, %10
  %add4 = add nsw i32 %8, %sub3
  call void @llvm.lifetime.end.p0(i64 4, ptr %v8) #2
  call void @llvm.lifetime.end.p0(i64 4, ptr %v7) #2
  call void @llvm.lifetime.end.p0(i64 4, ptr %v6) #2
  call void @llvm.lifetime.end.p0(i64 4, ptr %v5) #2
  call void @llvm.lifetime.end.p0(i64 4, ptr %v4) #2
  call void @llvm.lifetime.end.p0(i64 4, ptr %v3) #2
  call void @llvm.lifetime.end.p0(i64 4, ptr %v2) #2
  call void @llvm.lifetime.end.p0(i64 4, ptr %v1) #2
  ret i32 %add4
}

attributes #0 = { nounwind uwtable "min-legal-vector-width"="0" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cmov,+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" }
attributes #1 = { nocallback nofree nosync nounwind willreturn memory(argmem: readwrite) }
attributes #2 = { nounwind }

!llvm.module.flags = !{!0, !1, !2, !3}
!llvm.ident = !{!4}

!0 = !{i32 1, !"wchar_size", i32 4}
!1 = !{i32 8, !"PIC Level", i32 2}
!2 = !{i32 7, !"PIE Level", i32 2}
!3 = !{i32 7, !"uwtable", i32 2}
!4 = !{!"clang version 21.1.8 (https://github.com/llvm/llvm-project.git 2078da43e25a4623cab2d0d60decddf709aaea28)"}
!5 = !{!6, !6, i64 0}
!6 = !{!"int", !7, i64 0}
!7 = !{!"omnipotent char", !8, i64 0}
!8 = !{!"Simple C/C++ TBAA"}
!9 = !{!10, !10, i64 0}
!10 = !{!"p1 long", !11, i64 0}
!11 = !{!"any pointer", !7, i64 0}
!12 = !{!13, !13, i64 0}
!13 = !{!"long", !7, i64 0}
!14 = !{!15, !15, i64 0}
!15 = !{!"p1 int", !11, i64 0}
!16 = !{!7, !7, i64 0}
!17 = !{!18, !18, i64 0}
!18 = !{!"short", !7, i64 0}
