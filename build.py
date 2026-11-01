#!/usr/bin/env python3
"""Build a ready-to-run Sega Rally Championship (PC) folder for modern PCs from your own CD.

Usage:
  python3 build.py DISC.cue|DISC.ccd [--mmx PATCH] [--d3d D3DPATCH] [--mod MODDIR]
                   --dgvoodoo DGVOODOO.zip --ogg-winmm OGG-WINMM.zip [--out DIR] [--windows]

  DISC          your Sega Rally Championship PC CD (Sega, December 1996) as .cue + .bin or .ccd + .img, with its
                audio tracks
  --mmx         Sega's official patch 2.1 (MMX): its RALLY.EXE, or a folder or zip holding it -> the software
                version, game/RALLY.EXE
  --d3d         vetz's Unofficial Direct3D patch (2012) as downloaded (zip), or its unpacked folder -> the
                Direct3D version, game/RALLYD3D.EXE
  --mod         VirtuaIceMan / vetz's Sega Rally Championship Mod, unpacked (a folder): engine sounds without
                clipping, smoother loading screens, better 2D backdrops and GAMEOVER.wav. Optional
  At least one of --mmx and --d3d: each gives one version of the game. None of them is in this repository;
  README.md says where to find them.
  --dgvoodoo    dgVoodoo2 2.79.3 zip (or its unpacked folder)
  --ogg-winmm   ogg-winmm release zip (or folder)
  --out         where to create SegaRallyPC/ (default: this folder)
  --windows     a folder for Windows only: the same game/ folder, without the Steam Deck launch script

Needs Python 3.8+ and an Ogg Vorbis encoder on the PATH: oggenc (vorbis-tools) or ffmpeg.
"""
import argparse, hashlib, os, shutil, struct, subprocess, sys, tempfile, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import disc, expand_szdd, patch_exe

DISC_EXE_MD5 = "4a59c82bd8bb4f59667351f6543ae9bf"       # SRALLY\Rally.exe on the retail CD, 1.0
MMX_MD5 = "d3bf3bc7ca8e02dee4bbec3abf578696"            # RALLY.EXE of Sega's patch 2.1 (MMX)
D3D_MD5 = "bdd18610c1e2593882d3d41662994df4"            # RALLYD3D.EXE of vetz's 2012 patch
PATCHED = {"RALLY.EXE": "7c2c5de8d4276437e2724808bf7d0e28", "RALLYD3D.EXE": "2f1d60be1334c74069c9b22e7e990dfd"}
# Not copied from the disc's SRALLY\ folder or the patches: the 1.0 exe (wants the CD; kept in _spare/), its map,
# vetz's CPU hog (CPUGRAB: dgVoodoo's frame cap does that job), the help index and the readmes
SKIP = {"rally.exe", "rally.map", "cpugrab", "srally.gid",
        "sega rally direct3d readme.txt", "sega rally direct3d patch readme.txt", "sega rally mod readme.txt"}


def md5(data): return hashlib.md5(data).hexdigest()


def layer_files(src):
    """[(relative path with /, bytes)] of a zip or a folder (a single top folder in it is looked through)."""
    files = []
    if os.path.isdir(src):
        for d, _, fs in os.walk(src):
            for f in fs:
                if f.startswith("."): continue
                p = os.path.join(d, f); files.append((os.path.relpath(p, src).replace(os.sep, "/"), open(p, "rb").read()))
    else:
        with zipfile.ZipFile(src) as z:
            files = [(n, z.read(n)) for n in z.namelist() if not n.endswith("/")]
    tops = {p.split("/")[0] for p, _ in files}
    if len(tops) == 1 and all("/" in p for p, _ in files):        # everything inside one folder: drop it
        files = [(p.split("/", 1)[1], d) for p, d in files]
    return files


def merge(game, files):
    """Lays files over game/, reusing existing names whatever their case (the disc has Wave\\, the patches WAVE\\;
    on a case-sensitive disk they'd become two folders)."""
    for rel, data in sorted(files):
        parts = rel.split("/")
        if any(p.lower() in SKIP for p in parts): continue
        path = game
        for i, part in enumerate(parts):
            have = {n.lower(): n for n in os.listdir(path)} if os.path.isdir(path) else {}
            path = os.path.join(path, have.get(part.lower(), part))
            if i < len(parts) - 1: os.makedirs(path, exist_ok=True)
        if os.path.exists(path): os.remove(path)
        open(path, "wb").write(data)


def find_exe(src, name, want, what):
    if os.path.isfile(src) and not zipfile.is_zipfile(src): d = open(src, "rb").read()
    else:
        hits = [b for p, b in layer_files(src) if p.split("/")[-1].upper() == name]
        if not hits: sys.exit(f"{src}: no {name} in it: is it {what}?")
        d = hits[0]
    if md5(d) != want: sys.exit(f"{src}: its {name} is not {what} the kit was made for (MD5 {md5(d)})")
    return d


def encoder():
    if shutil.which("oggenc"): return lambda wav, ogg: ["oggenc", "-Q", "-q", "7", wav, "-o", ogg]
    if shutil.which("ffmpeg"):
        return lambda wav, ogg: ["ffmpeg", "-loglevel", "error", "-y", "-i", wav, "-c:a", "libvorbis", "-q:a", "7", ogg]
    sys.exit("needs oggenc (vorbis-tools) or ffmpeg on the PATH to encode the soundtrack")


def rip(tracks, music):
    enc = encoder(); os.makedirs(music, exist_ok=True); n = 0
    with tempfile.TemporaryDirectory() as tmp:
        for t in tracks:
            if t.kind != "AUDIO": continue
            data = disc.audio(t)          # INDEX 01 to the next track's start: lengths match the disc's TOC
            wav = os.path.join(tmp, f"track{t.n:02d}.wav")
            with open(wav, "wb") as o:
                o.write(b"RIFF" + struct.pack("<I", 36 + len(data)) + b"WAVEfmt " +
                        struct.pack("<IHHIIHH", 16, 1, 2, 44100, 176400, 4, 16) + b"data" +
                        struct.pack("<I", len(data)) + data)
            subprocess.run(enc(wav, os.path.join(music, f"Track{t.n:02d}.ogg")), check=True); os.remove(wav)
            n += 1
    print(f"  Music/Track02..{n + 1:02d}.ogg")
    if n != 22: sys.exit(f"expected 22 audio tracks (the game's music), found {n}: is the image missing them?")


def take(src, member):
    """Bytes of the file whose path ends with `member` (case-insensitive) in a zip or folder."""
    want = member.lower()
    if os.path.isdir(src):
        for d, _, fs in os.walk(src):
            for f in fs:
                p = os.path.join(d, f)
                if os.path.relpath(p, src).replace(os.sep, "/").lower().endswith(want): return open(p, "rb").read()
    else:
        with zipfile.ZipFile(src) as z:
            for name in z.namelist():
                if name.lower().endswith(want): return z.read(name)
    sys.exit(f"{member} not found in {src}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("disc"); ap.add_argument("--mmx"); ap.add_argument("--d3d"); ap.add_argument("--mod")
    ap.add_argument("--dgvoodoo", required=True); ap.add_argument("--ogg-winmm", required=True)
    ap.add_argument("--out", default=HERE); ap.add_argument("--windows", action="store_true")
    a = ap.parse_args()
    if not (a.mmx or a.d3d): sys.exit("give --mmx (the software version) and / or --d3d (the Direct3D version)")

    tracks = disc.tracks(a.disc)
    data = [t for t in tracks if t.kind != "AUDIO"]
    if not data: sys.exit("no data track in " + a.disc)
    dt = disc.DataTrack(data[0])
    entries = {p.upper(): (p, is_dir, l, s) for p, is_dir, l, s in dt.walk()}
    if "SRALLY/RALLY.EXE" not in entries: sys.exit("no SRALLY\\RALLY.EXE on this CD: it isn't the Sega Rally PC disc")
    got = md5(dt.read_file(*entries["SRALLY/RALLY.EXE"][2:]))
    if got != DISC_EXE_MD5:
        sys.exit(f"this CD's RALLY.EXE is not the December 1996 retail one the kit was made for (MD5 {got})")
    mmx = find_exe(a.mmx, "RALLY.EXE", MMX_MD5, "Sega's patch 2.1 (MMX)") if a.mmx else None
    d3d = layer_files(a.d3d) if a.d3d else None
    if d3d is not None:
        exe = [b for p, b in d3d if p.upper() == "RALLYD3D.EXE"]
        if not exe or md5(exe[0]) != D3D_MD5: sys.exit(f"{a.d3d}: not vetz's 2012 Direct3D patch (no RALLYD3D.EXE as expected)")
    mod = layer_files(a.mod) if a.mod else None
    if mod is not None and not any(p.upper() == "WAVE/GAMEOVER.WAV" for p, _ in mod):
        sys.exit(f"{a.mod}: not the Sega Rally Championship Mod, unpacked (no WAVE/GAMEOVER.wav)")
    winmm = take(a.ogg_winmm, "winmm.dll")

    pkg = os.path.join(os.path.abspath(a.out), "SegaRallyPC"); game = os.path.join(pkg, "game")
    if os.path.exists(pkg): sys.exit(f"{pkg} already exists: move or delete it first")
    os.makedirs(os.path.join(game, "_spare"))

    print("1/5 game files: the CD's full install" + (", the Direct3D patch" if d3d else "") + (", the mod" if mod else ""))
    merge(game, [(p[len("SRALLY/"):], dt.read_file(l, s)) for key, (p, is_dir, l, s) in entries.items()
                 if key.startswith("SRALLY/") and not is_dir])
    if d3d: merge(game, d3d)
    if mod: merge(game, mod)
    expand_szdd.expand_dirs(*[os.path.join(game, d) for d in os.listdir(game) if d.upper() in ("MODELS", "SCROLL")])
    dt.copy_file(*entries["DOC/SRALLYE.HLP"][2:], os.path.join(game, "SRALLY.HLP"))     # what the installer does
    dt.copy_file(*entries["SRALLY/RALLY.EXE"][2:], os.path.join(game, "_spare", "Rally_retail_1.0.exe"))

    print("2/5 exe patches")
    if d3d:
        path = os.path.join(game, "RALLYD3D.EXE")
        shutil.copyfile(path, os.path.join(game, "_spare", "RALLYD3D_vetz_2012.exe"))
        out = patch_exe.patch(open(path, "rb").read(), "RALLYD3D.EXE")
        if md5(out) != PATCHED["RALLYD3D.EXE"]: sys.exit("patching gave an unexpected RALLYD3D.EXE")
        open(path, "wb").write(out)
        shutil.copyfile(os.path.join(HERE, "config", "RALLY.INI"), os.path.join(game, "RALLY.INI"))   # + the pad
    if mmx:
        open(os.path.join(game, "_spare", "Rally_mmx_2.1.exe"), "wb").write(mmx)
        out = patch_exe.patch(mmx, "RALLY.EXE")
        if md5(out) != PATCHED["RALLY.EXE"]: sys.exit("patching gave an unexpected RALLY.EXE")
        open(os.path.join(game, "RALLY.EXE"), "wb").write(out)
        shutil.copyfile(os.path.join(HERE, "config", "SRMMX.INI"), os.path.join(game, "SRMMX.INI"))   # its own INI

    print("3/5 soundtrack")
    rip(tracks, os.path.join(game, "Music"))

    print("4/5 wrappers and settings")
    for member, name in [("MS/x86/DDraw.dll", "ddraw.dll"), ("MS/x86/D3DImm.dll", "d3dimm.dll")]:
        open(os.path.join(game, name), "wb").write(take(a.dgvoodoo, member))
    open(os.path.join(game, "winmm.dll"), "wb").write(winmm)
    open(os.path.join(game, "winmm.ini"), "wb").write(take(a.ogg_winmm, "winmm.ini"))
    shutil.copyfile(os.path.join(HERE, "config", "dgVoodoo.conf"), os.path.join(game, "dgVoodoo.conf"))

    print("5/5 Steam Deck launch script" if not a.windows else "5/5 done")
    if not a.windows:
        launch = os.path.join(pkg, "segarally_launch.sh")
        shutil.copyfile(os.path.join(HERE, "steamdeck", "segarally_launch.sh"), launch); os.chmod(launch, 0o755)
    print(f"\ndone: {pkg}  (see README.md)")


if __name__ == "__main__":
    main()
