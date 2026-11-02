#!/usr/bin/env python3
"""Inspect a Strata STRP expert profile: top-N per layer and the overlap between two profiles."""
import struct, sys, collections

def load(p):
    b = open(p, 'rb').read()
    assert b[:4] == b'STRP', 'not STRP'
    ver, nl, ne, want, nr = struct.unpack('<5I', b[4:24])
    pairs = struct.unpack('<%dH' % (nr * 2), b[24:24 + nr * 4])
    return nl, ne, want, [(pairs[2*i], pairs[2*i+1]) for i in range(nr)]

def top(prof, n):
    nl, ne, want, pairs = prof
    return pairs[:n]

if __name__ == '__main__':
    a = load(sys.argv[1]); n = int(sys.argv[2]) if len(sys.argv) > 2 else 7903
    t = top(a, n); c = collections.Counter(l for l, e in t)
    print(f'{sys.argv[1]}: {a[0]}x{a[1]}, want {a[2]}, ranked {len(a[3])}, top {n}')
    print('per layer:', [c[i] for i in range(a[0])])
    print('min/max/mean', min(c.values()), max(c.values()), sum(c.values()) / a[0])
    if len(sys.argv) > 3:
        b = load(sys.argv[3]); tb = top(b, n); sa, sb = set(t), set(tb)
        print(f'{sys.argv[3]}: overlap top{n} = {len(sa & sb)} ({100*len(sa&sb)/n:.1f}%), only A {len(sa-sb)}, only B {len(sb-sa)}')
        cb = collections.Counter(l for l, e in tb)
        print('per layer B:', [cb[i] for i in range(a[0])])
