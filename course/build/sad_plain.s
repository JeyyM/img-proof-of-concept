	.file	"sad_scalar.c"
	.text
	.p2align 4
	.globl	sad_plain
	.def	sad_plain;	.scl	2;	.type	32;	.endef
	.seh_proc	sad_plain
sad_plain:
	.seh_endprologue
	testq	%r8, %r8
	je	.L4
	xorl	%r10d, %r10d
	xorl	%r11d, %r11d
	.p2align 6
	.p2align 4
	.p2align 3
.L3:
	movzbl	(%rdx,%r10), %eax
	movzbl	(%rcx,%r10), %r9d
	subl	%eax, %r9d
	movl	%r9d, %eax
	negl	%eax
	cmovs	%r9d, %eax
	addq	$1, %r10
	cltq
	addq	%rax, %r11
	cmpq	%r10, %r8
	jne	.L3
	movq	%r11, %rax
	ret
	.p2align 4,,10
	.p2align 3
.L4:
	xorl	%r11d, %r11d
	movq	%r11, %rax
	ret
	.seh_endproc
	.ident	"GCC: (MinGW-W64 x86_64-msvcrt-posix-seh, built by Brecht Sanders, r1) 15.2.0"
