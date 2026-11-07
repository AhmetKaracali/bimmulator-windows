#!/usr/bin/env python3
"""Check the trace shim against the staged dispatch order with a host fake vendor.

This checks forwarding, outputs, and sticky-error preservation without booting
QNX or claiming that host ABI checks validate the ARM loader/optional tail calls.
Run with the Nix shell's native clang; the real ARM library is built separately.
"""
from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path
import subprocess
import tempfile


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    here = Path(__file__).resolve().parent
    spec = importlib.util.spec_from_file_location("qnx_elf", here / "trace-qnx-gles-callers.py")
    elf_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(elf_module)
    elf = elf_module.Elf32(args.root / "lib/libEGL.so.1")
    names = []
    for index in range(34):
        address = elf.read_vaddr_u32(0xA6C8 + index * 4)
        for base, offset, size in elf.load_segments:
            if base <= address < base + size:
                names.append(elf_module.c_string(elf.data, offset + address - base))
                break
        else:
            raise RuntimeError("staged EGL core-name table no longer matches the recorded ABI")
    if names[0] != "eglGetError" or names[-1] != "eglGetProcAddress":
        raise RuntimeError("unexpected EGL dispatch order")
    selected = {
        "eglGetError", "eglGetDisplay", "eglInitialize", "eglQueryString",
        "eglGetConfigs", "eglChooseConfig", "eglCreateContext",
        "eglCreateWindowSurface", "eglMakeCurrent", "eglSwapBuffers",
    }
    source = r'''
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
typedef void (*Proc)(void);
extern const char *ID6eglQueryString(void *, int);
static int error_value, error_reads, fake_errno, fail_choose;
static const int *expected_attributes;
int *__get_errno_ptr(void) { return &fake_errno; }
unsigned IMGeglGetError(void) { unsigned v=error_value; error_value=0x3000; error_reads++; return v; }
void *IMGeglGetDisplay(void *n) { assert(n==(void*)0x42); return (void*)0x101; }
unsigned IMGeglInitialize(void *d,int *a,int *b) { assert(d==(void*)0x101); return 0; }
const char *IMGeglQueryString(void *d,int n) {
    if(!d && n==0x6000) { error_value=0x3008; return 0; }
    return "fake-vendor";
}
unsigned IMGeglGetConfigs(void*d,void**c,int n,int*count) {
    assert(d==(void*)0x101 && !c && n==0); *count=3; return 1;
}
unsigned IMGeglChooseConfig(void*d,const int*a,void**c,int n,int*count) {
    assert(d==(void*)0x101 && a==expected_attributes);
    if(fail_choose) return 0;
    assert(n==1 && c); c[0]=(void*)0x202; *count=1; return 1;
}
void *IMGeglCreateContext(void*d,void*c,void*s,const int*a) {
    assert(d==(void*)0x101 && c==(void*)0x202 && s==(void*)0x303 && a==expected_attributes);
    return (void*)0x404;
}
void *IMGeglCreateWindowSurface(void*d,void*c,void*w,const int*a) {
    assert(d==(void*)0x101 && c==(void*)0x202 && w==(void*)0x505 && a==expected_attributes);
    return (void*)0x606;
}
unsigned IMGeglMakeCurrent(void*d,void*w,void*r,void*c) {
    assert(d==(void*)0x101 && w==(void*)0x606 && r==(void*)0x707 && c==(void*)0x404); return 1;
}
unsigned IMGeglSwapBuffers(void*d,void*s) { assert(d==(void*)0x101 && s==(void*)0x606); return 1; }
'''
    source += "\n".join(f"void IMG{name}(void) {{}}" for name in names if name not in selected)
    source += "\nstatic Proc expected[34] = {" + ",".join(f"(Proc)IMG{n}" for n in names) + "};\n"
    source += r'''
int main(void) {
    const Proc *t=(const Proc*)ID6eglQueryString(0,0x6000);
    assert(t && error_reads==0);
    for(int i=0;i<34;i++) {
        assert(t[i]);
        if(i!=0&&i!=1&&i!=2&&i!=5&&i!=6&&i!=8&&i!=22&&i!=24&&i!=31) assert(t[i]==expected[i]);
    }
    assert(((unsigned(*)(void))t[0])()==0x3008);
    assert(error_reads==1);
    error_value=0x3001; fake_errno=73;
    assert(((void*(*)(void*))t[1])((void*)0x42)==(void*)0x101);
    int major=123,minor=456;
    assert(!((unsigned(*)(void*,int*,int*))t[2])((void*)0x101,&major,&minor));
    assert(major==123 && minor==456);
    int attrs[]={0x3024,8,0x3038}; expected_attributes=attrs;
    void *config=0; int count=0;
    assert(((unsigned(*)(void*,const int*,void**,int,int*))t[6])((void*)0x101,attrs,&config,1,&count));
    assert(config==(void*)0x202 && count==1);
    fail_choose=1;
    assert(!((unsigned(*)(void*,const int*,void**,int,int*))t[6])((void*)0x101,attrs,0,0,(int*)1));
    assert(((unsigned(*)(void*,void**,int,int*))t[5])((void*)0x101,0,0,&count) && count==3);
    assert(((void*(*)(void*,void*,void*,const int*))t[22])((void*)0x101,(void*)0x202,(void*)0x303,attrs)==(void*)0x404);
    assert(((void*(*)(void*,void*,void*,const int*))t[8])((void*)0x101,(void*)0x202,(void*)0x505,attrs)==(void*)0x606);
    assert(((unsigned(*)(void*,void*,void*,void*))t[24])((void*)0x101,(void*)0x606,(void*)0x707,(void*)0x404));
    assert(((unsigned(*)(void*,void*))t[31])((void*)0x101,(void*)0x606));
    assert(error_reads==1 && error_value==0x3001 && fake_errno==73);
    assert(((unsigned(*)(void))t[0])()==0x3001);
    assert(error_reads==2);
    puts("PASS: actual 34-slot dispatch order, argument/output forwarding, failed-output safety, sticky error and errno preservation");
    return 0;
}
'''
    with tempfile.TemporaryDirectory(prefix="idrive-egl-trace-check-") as directory:
        directory = Path(directory)
        fake = directory / "vendor-check.c"
        fake.write_text(source)
        executable = directory / "check"
        subprocess.run(["clang", "-O1", str(here / "qnx-egl-provider-trace.c"), str(fake), "-o", str(executable)], check=True)
        subprocess.run([str(executable)], check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
