define i32 @src(i32 %x) {
  %r = add i32 %x, 0
  ret i32 %r
}
define i32 @tgt(i32 %x) {
  %r = add i32 %x, 1
  ret i32 %r
}
