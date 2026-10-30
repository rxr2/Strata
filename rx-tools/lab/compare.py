"""KL(ref || variant) of first-token distributions (top-20 union, rest lumped), per length; paired: which variant is closer;
agent tasks: characters in common with the reference before the first difference."""
import json, math, sys
def kl(a, b):
    pa = {t: math.exp(l) for t, l in a}; pb = {t: math.exp(l) for t, l in b}; fb = min(pb.values())
    ra, rb = max(1e-9, 1 - sum(pa.values())), max(1e-9, 1 - sum(pb.values()))
    return max(0.0, sum(p * math.log(p / pb.get(t, min(fb, 1e-6))) for t, p in pa.items()) + ra * math.log(ra / rb))
ref = json.load(open(sys.argv[1])); vs = {p.split('/')[-1][:-5]: json.load(open(p)) for p in sys.argv[2:]}
names = list(vs)
for L in ('4k', '16k', 'all'):
    idx = [i for i, r in enumerate(ref['first']) if L == 'all' or r['len'] == L]
    print(f"== first token, {L} ({len(idx)} prompts)")
    per = {}
    for n in names:
        k = [kl(ref['first'][i]['top'], vs[n]['first'][i]['top']) for i in idx]
        top1 = sum(ref['first'][i]['top'][0][0] == vs[n]['first'][i]['top'][0][0] for i in idx)
        per[n] = k; s = sorted(k)
        print(f"   {n:10} KL mean {sum(k)/len(k):.5f}  median {s[len(s)//2]:.5f}  max {s[-1]:.4f}  top-1 like ref {top1}/{len(idx)}")
    if len(names) == 2:
        a, b = names; closer = sum(x < y for x, y in zip(per[b], per[a]))
        print(f"   {b} closer to ref than {a} in {closer}/{len(idx)} prompts")
print("== agent tasks (temperature 0, 192 tokens): characters equal to the reference before the first difference")
for t, rt in ref['tasks'].items():
    line = f"   {t:8} ref {len(rt):4} chars |"
    for n in names:
        o = vs[n]['tasks'][t]; c = next((i for i, (x, y) in enumerate(zip(rt, o)) if x != y), min(len(rt), len(o)))
        line += f" {n} {c:4}{' (identical)' if o == rt else ''} |"
    print(line)
