#!/usr/bin/env python3
"""Clean a third-party Bruma patch of records that Beyond Skyrim - Bruma 2.0.0 and Beyond Skyrim - Assets SE
(2026.11.11) no longer contain.

  DFNF - Bruma.esp              drops the NPC_ overrides of removed Bruma/Assets records and the BS_DLC_patch.esp master

A record is dangling when it overrides a record of BSHeartland.esm or BSAssets.esm whose object ID is absent from the
2.0 plugin. Nothing is remapped: the EditorIDs are in neither new plugin. Personal use only: these are other
author's plugin with records removed, not for release.

Usage: python3 build.py          dry run: lists what would go, writes build/review.txt, writes no plugin
       python3 build.py --write  serialize, remove, deserialize to dist/, then verify the result
Needs the toolkit's tools/spriggit-cli.sh (SKYRIM_TOOLKIT overrides the default path) and inputs/ (see BUILDING.md).
"""
import collections, hashlib, os, pathlib, re, shutil, struct, subprocess, sys, zlib

HERE = pathlib.Path(__file__).resolve().parent
INPUTS, BUILD, DIST = HERE / 'inputs', HERE / 'build', HERE / 'dist'
TOOLKIT = pathlib.Path(os.environ.get('SKYRIM_TOOLKIT', '/Volumes/S512/Projects/ETC/skyrim-ai-toolkit'))
PLUGINS = ['DFNF - Bruma.esp']
REFERENCE = ['BSHeartland.esm', 'BSAssets.esm']
DROP_MASTERS = {'DFNF - Bruma.esp': ['BS_DLC_patch.esp']}


def check_inputs():
    for line in (HERE / 'inputs.sha256').read_text().splitlines():
        want, name = line.split(None, 1)
        f = INPUTS / name.strip()
        if not f.is_file() or hashlib.sha256(f.read_bytes()).hexdigest() != want:
            sys.exit(f'inputs/{name.strip()} is missing or not the version this was written against (BUILDING.md)')


def read(path):
    """(masters, records): records = [(type, formid, flags, decompressed body)]."""
    d = pathlib.Path(path).read_bytes()
    sz = struct.unpack_from('<I', d, 4)[0]
    masters, i = [], 24
    while i < 24 + sz:
        t, l = d[i:i + 4], struct.unpack_from('<H', d, i + 4)[0]
        if t == b'MAST':
            masters.append(d[i + 6:i + 6 + l].rstrip(b'\0').decode())
        i += 6 + l
    out = []

    def walk(a, b):
        while a < b:
            t, s = d[a:a + 4], struct.unpack_from('<I', d, a + 4)[0]
            if t == b'GRUP':
                walk(a + 24, a + s)
                a += s
                continue
            fl, fid = struct.unpack_from('<II', d, a + 8)
            body = d[a + 24:a + 24 + s]
            if fl & 0x40000:
                body = zlib.decompress(body[4:])
            out.append((t.decode(), fid, fl, body))
            a += 24 + s
    walk(24 + sz, len(d))
    return masters, out


def edid(body):
    if body[:4] == b'EDID':
        return body[6:6 + struct.unpack_from('<H', body, 4)[0]].rstrip(b'\0').decode('latin1')
    return ''


def key(masters, fid, self_name):  # a FormKey: (plugin name, object id)
    i = fid >> 24
    return (masters[i] if i < len(masters) else self_name, fid & 0xFFFFFF)


def reference_ids():
    own = {}
    for name in REFERENCE:
        ms, recs = read(INPUTS / name)
        own[name] = {f & 0xFFFFFF for t, f, fl, b in recs if f >> 24 == len(ms)}
    return own


def plan(name, own):
    ms, recs = read(INPUTS / name)
    dangling = {f for t, f, fl, b in recs
                if key(ms, f, name)[0] in own and key(ms, f, name)[1] not in own[key(ms, f, name)[0]]}
    pats = {struct.pack('<I', f): f for f in dangling}
    ref = {(t, f): [p for p in pats if p in b] for t, f, fl, b in recs if f not in dangling}
    ref = {k: v for k, v in ref.items() if v}
    drop = dangling | {f for t, f in ref}
    return ms, recs, dangling, ref, drop


def run(*cmd):
    r = subprocess.run(['bash', str(TOOLKIT / 'tools/spriggit-cli.sh'), *cmd], capture_output=True, text=True)
    if r.returncode:
        sys.exit(r.stdout[-1500:] + r.stderr[-1500:])


def main():
    write = '--write' in sys.argv
    check_inputs()
    own = reference_ids()
    BUILD.mkdir(exist_ok=True)
    review, results = [], {}
    for name in PLUGINS:
        ms, recs, dangling, ref, drop = plan(name, own)
        review.append(f'== {name}: {len(recs)} records, {len(dangling)} dangling, {len(ref)} kept records point at one, '
                      f'{len(drop)} dropped, {len(recs) - len(drop)} kept; masters {ms}')
        for t, f, fl, b in sorted(recs, key=lambda r: (r[0], r[1])):
            if f in drop:
                why = 'dangling override' if f in dangling else 'effect list names a dropped record'
                review.append(f'  drop {t} {key(ms, f, name)[1]:06X}:{key(ms, f, name)[0]} {edid(b)} ({why})')
        results[name] = (ms, recs, drop)
    (BUILD / 'review.txt').write_text('\n'.join(review) + '\n')
    print('\n'.join(l for l in review if l.startswith('==')))
    if not write:
        print('dry run: see build/review.txt; nothing written')
        return
    DIST.mkdir(exist_ok=True)
    for name, (ms, recs, drop) in results.items():
        stem = name[:-4]
        yaml = BUILD / f'yaml-{stem}'
        shutil.rmtree(yaml, ignore_errors=True)
        run('serialize', '--InputPath', str(INPUTS / name), '--OutputPath', str(yaml), '--GameRelease', 'SkyrimSE',
            '--PackageName', 'Spriggit.Yaml.Skyrim', '--PackageVersion', '0.41.0', '-u')
        gone = {key(ms, f, name) for f in drop}
        removed = 0
        for f in yaml.rglob('*.yaml'):
            m = re.search(r' - ([0-9A-Fa-f]{6})_(.+)\.yaml$', f.name)
            if m and (m.group(2), int(m.group(1), 16)) in gone:
                f.unlink()
                removed += 1
        assert removed == len(gone), (name, removed, len(gone))
        for m in DROP_MASTERS.get(name, []):
            rd = yaml / 'RecordData.yaml'
            t = rd.read_text()
            t2 = t.replace(f'  - Master: {m}\n    FileSize: 0\n', '')
            assert t2 != t, m
            rd.write_text(t2)
        out = DIST / name
        run('deserialize', '--InputPath', str(yaml), '--OutputPath', str(out))
        verify(name, ms, recs, drop, out, own)
        print('wrote', out)


def subrecords(b):
    out, i = collections.defaultdict(list), 0
    while i < len(b):
        l = struct.unpack_from('<H', b, i + 4)[0]
        out[b[i:i + 4].decode('latin1')].append(b[i + 6:i + 6 + l])
        i += 6 + l
    return out


def vmad_canon(d):
    """VMAD with each script's properties sorted (binding is by name): (header, scripts, tail), or None if unparsed."""
    try:
        ver, fmt, n = struct.unpack_from('<HHH', d, 0)
        i, scripts = 6, []

        def ws(i):
            l = struct.unpack_from('<H', d, i)[0]
            return i + 2 + l
        size = {1: 8, 3: 4, 4: 4, 5: 1}
        for _ in range(n):
            j = ws(i)
            name, flags, pc = d[i:j], d[j], struct.unpack_from('<H', d, j + 1)[0]
            i, props = j + 3, []
            for _ in range(pc):
                p0 = i
                i = ws(i)
                t = d[i]
                i += 2
                if t == 2:
                    i = ws(i)
                elif t in size:
                    i += size[t]
                elif 11 <= t <= 15:
                    cnt = struct.unpack_from('<I', d, i)[0]
                    i += 4
                    for _ in range(cnt):
                        i = ws(i) if t == 12 else i + size[{11: 1, 13: 3, 14: 4, 15: 5}[t]]
                else:
                    return None
                props.append(d[p0:i])
            scripts.append((name, flags, tuple(sorted(props))))
        return (ver, fmt), tuple(scripts), d[i:]
    except (struct.error, IndexError, KeyError):
        return None


def same_record(x, y):
    (t, bx), (t2, by) = x, y
    if t != t2:
        return False
    sx, sy = subrecords(bx), subrecords(by)
    if set(sx) != set(sy):
        return False
    for tag in sx:
        a, b = sorted(sx[tag]), sorted(sy[tag])
        if len(a) != len(b):
            return False
        for u, v in zip(a, b):
            if u == v:
                continue
            if tag == 'VMAD' and vmad_canon(u) is not None and vmad_canon(u) == vmad_canon(v):
                continue
            if t == 'NPC_' and tag == 'DNAM' and len(u) == len(v) == 52:
                mask = lambda d: d[:42] + d[44:49]
                if mask(u) == mask(v):
                    continue
            if t == 'NPC_' and tag == 'QNAM' and len(u) == len(v) == 12:
                if max(abs(p - q) for p, q in zip(struct.unpack('<3f', u), struct.unpack('<3f', v))) < 1e-6:
                    continue
            return False
    return True


def verify(name, ms, recs, drop, out, own):
    ms2, recs2 = read(out)
    want = {key(ms, f, name): (t, b) for t, f, fl, b in recs if f not in drop}
    got = {key(ms2, f, name): (t, b) for t, f, fl, b in recs2}
    assert set(want) == set(got), (name, len(want), len(got), sorted(set(want) ^ set(got))[:5])
    # Spriggit/Mutagen rewrite a few bytes of every record it round-trips. Allowed, nothing else:
    #  - list subrecords (CNTO, SPLO, SNAM, ...) come back in a different order: compared as sorted lists
    #  - VMAD script properties come back in a different order (binding is by name): compared as sorted lists
    #  - NPC_ DNAM bytes 42-43 and 49-51 are unused padding; Mutagen zeroes what the CK left as garbage
    #  - NPC_ QNAM floats differ in the last bit through the YAML text round trip (tolerance 1e-6)
    # Masters keep their order here, so FormIDs in a body are comparable byte for byte.
    assert [m for m in ms if m not in DROP_MASTERS.get(name, [])] == ms2, 'master order changed'
    diff = [k for k in want if not same_record(want[k], got[k])]
    assert not diff, (name, 'record bodies differ beyond the allowed normalisation', diff[:5])
    same = 'every kept record equal after the allowed normalisation'
    for m in ms2:
        assert m not in DROP_MASTERS.get(name, []), (name, m)
    dang = [k for k in got if k[0] in own and k[1] not in own[k[0]]]
    assert not dang, (name, 'still dangling', dang[:5])
    print(f'{name}: {len(got)} records, masters {ms2}; {same}; 0 dangling overrides')


if __name__ == '__main__':
    main()
