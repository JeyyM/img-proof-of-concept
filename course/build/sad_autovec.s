	.file	"sad_scalar.c"
	.text
	.p2align 4
	.globl	sad_autovec
	.def	sad_autovec;	.scl	2;	.type	32;	.endef
	.seh_proc	sad_autovec
sad_autovec:
	.seh_endprologue
	movq	%rcx, %r10
	movq	%rdx, %r11
	testq	%r8, %r8
	je	.L10
	leaq	-1(%r8), %rax
	cmpq	$30, %rax
	jbe	.L11
	movq	%r8, %rax
	xorl	%edx, %edx
	vpxor	%xmm3, %xmm3, %xmm3
	andq	$-32, %rax
	.p2align 4
	.p2align 3
.L4:
	vmovdqu	(%r10,%rdx), %ymm0
	vmovdqu	(%r11,%rdx), %ymm2
	addq	$32, %rdx
	vpmovzxbw	%xmm2, %ymm4
	vpmovzxbw	%xmm0, %ymm1
	vextracti128	$0x1, %ymm2, %xmm2
	vextracti128	$0x1, %ymm0, %xmm0
	vpsubw	%ymm4, %ymm1, %ymm1
	vpmovzxbw	%xmm2, %ymm2
	vpmovzxbw	%xmm0, %ymm0
	vpabsw	%ymm1, %ymm1
	vpsubw	%ymm2, %ymm0, %ymm0
	vpmovsxwd	%xmm1, %ymm5
	vextracti128	$0x1, %ymm1, %xmm1
	vpabsw	%ymm0, %ymm0
	vpmovsxdq	%xmm5, %ymm2
	vextracti128	$0x1, %ymm5, %xmm5
	vpmovsxwd	%xmm0, %ymm4
	vextracti128	$0x1, %ymm0, %xmm0
	vpmovsxdq	%xmm5, %ymm5
	vpmovsxwd	%xmm0, %ymm0
	vpaddq	%ymm5, %ymm2, %ymm2
	vpmovsxwd	%xmm1, %ymm1
	vpmovsxdq	%xmm0, %ymm5
	vextracti128	$0x1, %ymm0, %xmm0
	vpaddq	%ymm5, %ymm2, %ymm2
	vpmovsxdq	%xmm4, %ymm5
	vextracti128	$0x1, %ymm4, %xmm4
	vpmovsxdq	%xmm4, %ymm4
	vpmovsxdq	%xmm0, %ymm0
	vpaddq	%ymm4, %ymm5, %ymm4
	vpaddq	%ymm4, %ymm2, %ymm2
	vpmovsxdq	%xmm1, %ymm4
	vextracti128	$0x1, %ymm1, %xmm1
	vpmovsxdq	%xmm1, %ymm1
	vpaddq	%ymm1, %ymm4, %ymm1
	vpaddq	%ymm0, %ymm1, %ymm0
	vpaddq	%ymm0, %ymm2, %ymm0
	vpaddq	%ymm0, %ymm3, %ymm3
	cmpq	%rdx, %rax
	jne	.L4
	vextracti128	$0x1, %ymm3, %xmm0
	vpaddq	%xmm3, %xmm0, %xmm3
	vpsrldq	$8, %xmm3, %xmm0
	vpaddq	%xmm0, %xmm3, %xmm0
	vmovq	%xmm0, %r9
	cmpq	%rax, %r8
	je	.L17
	vzeroupper
.L3:
	movq	%r8, %rdx
	subq	%rax, %rdx
	leaq	-1(%rdx), %rcx
	cmpq	$14, %rcx
	jbe	.L9
	vmovdqu	(%r10,%rax), %xmm0
	vmovdqu	(%r11,%rax), %xmm4
	vpmovzxbw	%xmm0, %xmm2
	vpmovzxbw	%xmm4, %xmm1
	vpsubw	%xmm1, %xmm2, %xmm2
	vpsrldq	$8, %xmm4, %xmm4
	vpsrldq	$8, %xmm0, %xmm1
	vpmovzxbw	%xmm4, %xmm4
	vpabsw	%xmm2, %xmm2
	vpmovzxbw	%xmm1, %xmm1
	vpmovsxwd	%xmm2, %xmm5
	vpsubw	%xmm4, %xmm1, %xmm1
	vpsrldq	$8, %xmm2, %xmm2
	vpmovsxdq	%xmm5, %xmm0
	vpabsw	%xmm1, %xmm1
	vpsrldq	$8, %xmm5, %xmm5
	vpmovsxwd	%xmm2, %xmm2
	vpmovsxwd	%xmm1, %xmm4
	vpsrldq	$8, %xmm1, %xmm1
	vpmovsxdq	%xmm5, %xmm5
	vpmovsxwd	%xmm1, %xmm1
	vpaddq	%xmm5, %xmm0, %xmm0
	vpsrldq	$8, %xmm1, %xmm5
	vpmovsxdq	%xmm1, %xmm1
	vpmovsxdq	%xmm5, %xmm5
	vpaddq	%xmm5, %xmm0, %xmm0
	vpmovsxdq	%xmm2, %xmm5
	vpsrldq	$8, %xmm2, %xmm2
	vpmovsxdq	%xmm2, %xmm2
	vpaddq	%xmm2, %xmm5, %xmm2
	vpaddq	%xmm1, %xmm2, %xmm1
	vpaddq	%xmm1, %xmm0, %xmm0
	vpmovsxdq	%xmm4, %xmm1
	vpsrldq	$8, %xmm4, %xmm4
	vpmovsxdq	%xmm4, %xmm4
	vpaddq	%xmm4, %xmm1, %xmm1
	vpaddq	%xmm3, %xmm1, %xmm1
	vpaddq	%xmm1, %xmm0, %xmm0
	vpsrldq	$8, %xmm0, %xmm1
	vpaddq	%xmm1, %xmm0, %xmm0
	vmovq	%xmm0, %r9
	testb	$15, %dl
	je	.L1
	andq	$-16, %rdx
	addq	%rdx, %rax
	.p2align 6
	.p2align 4
	.p2align 3
.L9:
	movzbl	(%r11,%rax), %edx
	movzbl	(%r10,%rax), %ecx
	subl	%edx, %ecx
	movl	%ecx, %edx
	negl	%edx
	cmovs	%ecx, %edx
	addq	$1, %rax
	movslq	%edx, %rdx
	addq	%rdx, %r9
	cmpq	%r8, %rax
	jb	.L9
.L1:
	movq	%r9, %rax
	ret
	.p2align 4,,10
	.p2align 3
.L10:
	xorl	%r9d, %r9d
	movq	%r9, %rax
	ret
.L11:
	vpxor	%xmm3, %xmm3, %xmm3
	xorl	%eax, %eax
	xorl	%r9d, %r9d
	jmp	.L3
.L17:
	vzeroupper
	jmp	.L1
	.seh_endproc
	.ident	"GCC: (MinGW-W64 x86_64-msvcrt-posix-seh, built by Brecht Sanders, r1) 15.2.0"
