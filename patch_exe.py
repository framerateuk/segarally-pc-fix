#!/usr/bin/env python3
"""Patch the Sega Rally exes in place; which patches apply is chosen by the file name.

  patch_exe.py RALLYD3D.EXE               vetz's 2012 Direct3D exe (MD5 bdd18610c1e2593882d3d41662994df4)
  patch_exe.py RALLY.EXE                  Sega's patch 2.1 MMX exe (MD5 d3bf3bc7ca8e02dee4bbec3abf578696)

Applies every patch not yet applied and reports each; refuses (writes nothing) on unexpected bytes.

RALLYD3D.EXE (docs/TECHNICAL.md):
  nobar   0x413320: the loading-bar step returns at once. It drew the bar on the primary surface
          through GetDC/ReleaseDC at every loading step, and under dgVoodoo each release presents a
          frame and waits for the display (and the FPS cap), so a load took 30-50 s on the Deck.
          Its counter (0x524ce4) is read only by the bar code itself.

RALLY.EXE (docs/TECHNICAL.md): the CD hunt (0x4f7b80 and 0x4f7ca0, the routine vetz changed in the
D3D exe) scans every drive letter for a CD-ROM holding srally\\rally.exe and srally\\lake.tex.
  ini     "rally.ini" -> ".\\SRMMX.INI": a bare name makes Windows use C:\\windows\\rally.ini, and the
          D3D exe's .\\RALLY.INI can't be shared: same control format, different device numbering.
  nocd    the drive format "%c:\\" -> ".\\", the two drive-type tests (== DRIVE_CDROM) NOPed and the
          probes pointed at rally.exe and lake.tex in the game folder. Data paths come from
          [Directory] ExePath (empty = the working directory) unless [Install] Type is SELECT or
          MINIMUMONLY, so nothing else reads the "CD".

Both exes (docs/TECHNICAL.md):
  slack   .text's VirtualSize raised to its raw size (D3D 0x11ec4f -> 0x11ee00, MMX 0x10fbc8 -> 0x10fc00),
          still inside the same page, so the zero bytes after the code are mapped for tabquit and dpad.
  tabquit Tab quits, as Alt+F4 does (Sega gave the game no quit key). The window class's WndProc becomes
          a 43-byte stub in the zero slack at the end of .text (opened by slack): WM_KEYDOWN with VK_TAB -> PostMessageA(hwnd, WM_CLOSE,
          0, 0) and return 0; everything else jumps to the real WndProc (D3D 0x4ba7a0, MMX 0x4d6e00,
          whose own WM_KEYDOWN case handles only F1-F12). WM_CLOSE reaches DefWindowProc ->
          DestroyWindow -> the game's WM_DESTROY clean-up -> PostQuitMessage. Not Esc: Esc is the game's
          hard-wired second "back" in every menu (Saturn B, D3D input routine 0x47dd57). Not a letter:
          the record name entry types WM_CHARs. Alt+Tab arrives as WM_SYSKEYDOWN, so it doesn't quit.
          D3D: stub 0x51fc50, PostMessageA IAT 0x123c6a0, WndProc set at 0x4bb928.
          MMX: stub 0x510bc8, PostMessageA IAT 0x11055b4, WndProc set at 0x4d89af.
  dpad    the D-pad steers (Windows without Steam Input; on the Deck Steam Input can map it to the arrow keys).
          The per-frame joyGetPosEx (D3D 0x45b7c6, MMX 0x49d6b2) asked only for X, Y and buttons (0x83);
          it now also asks for the POV hat (0xC3), and the two lea instructions right after the call
          (D3D 0x45b7cc, MMX 0x49d6b8) become a call to a 57-byte routine that runs them itself after:
          POV strictly between 0 and 180 degrees (up-right, right, down-right) sets the record's X to
          0xFFFF, strictly between 180 and 360 sets it to 0; centred (0xFFFF), straight up or down leaves
          the stick's X alone. The game then reads a fully pushed stick: Left/Right, as before.
          D3D: routine at 0x51fc80 (.text slack); record esi+0x68c478 (POV +0x28, X +0x8).
          MMX: routine at 0x511d48, the zero slack after .rdata, whose VirtualSize goes 0xd48 -> 0xe00
          and which is marked executable (0x40000040 -> 0x60000040): MMX's .text slack holds only the
          Tab stub, and a 4,000-byte zero block inside .text (0x4253db) is the end address the Saturn
          layer loads into an emulated register (0x42637b), so it is not spare. Record edi+0x660538.
"""
import os, sys

def s(text, size):                     # string patch, NUL-padded to the original's room
    b = text.encode() + b"\0"
    assert len(b) <= size
    return b + b"\0" * (size - len(b))

PATCHES = {
    "RALLYD3D.EXE": {
        "slack": [(0x180, bytes.fromhex("4fec1100"),
                   bytes.fromhex("00ee1100"))],
        "tabquit": [(0x11f050, bytes.fromhex("00000000000000000000000000000000000000000000000000000000000000000000000000000000000000"),
                   bytes.fromhex("817c240800010000751c837c240c0975156a006a006a10ff742410ff15a0c6230131c0c21000e925abf9ff")),
                  (0xbad28, bytes.fromhex("c7442424a0a74b00"),
                   bytes.fromhex("c744242450fc5100"))],
        "dpad": [(0x5abc2, bytes.fromhex("83"),
                   bytes.fromhex("c3")),
                  (0x5abcc, bytes.fromhex("8d14bf8d04d2"),
                   bytes.fromhex("e8af440c0090")),
                  (0x11f080, bytes.fromhex("000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"),
                   bytes.fromhex("8b8ea0c4680081f9504600007424771085c9741ec78680c46800ffff0000eb1281f9a08c0000730ac78680c46800000000008d14bf8d04d2c3"))],
        "nobar": [(0x12720, bytes.fromhex("83ec14"), bytes.fromhex("c3ec14"))],   # sub esp,0x14 -> ret
    },
    "RALLY.EXE": {
        "slack": [(0x180, bytes.fromhex("c8fb1000"),
                   bytes.fromhex("00fc1000"))],
        "tabquit": [(0x10ffc8, bytes.fromhex("00000000000000000000000000000000000000000000000000000000000000000000000000000000000000"),
                   bytes.fromhex("817c240800010000751c837c240c0975156a006a006a10ff742410ff15b455100131c0c21000e90d62fcff")),
                  (0xd7daf, bytes.fromhex("c7442428006e4d00"),
                   bytes.fromhex("c7442428c80b5100"))],
        "dpad": [(0x1a8, bytes.fromhex("480d0000"),
                   bytes.fromhex("000e0000")),
                  (0x1c4, bytes.fromhex("40000040"),
                   bytes.fromhex("40000060")),
                  (0x9caae, bytes.fromhex("83"),
                   bytes.fromhex("c3")),
                  (0x9cab8, bytes.fromhex("8d0cb68d04c9"),
                   bytes.fromhex("e88b46070090")),
                  (0x110d48, bytes.fromhex("000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"),
                   bytes.fromhex("8b8f6005660081f9504600007424771085c9741ec78740056600ffff0000eb1281f9a08c0000730ac78740056600000000008d0cb68d04c9c3"))],
        "ini":  [(0x257d5c, s("rally.ini", 12), s(".\\SRMMX.INI", 12))],
        "nocd": [(0x257f08, s("%c:\\", 5), s(".\\", 5)),
                 (0xf6fda, bytes.fromhex("0f8593000000"), bytes.fromhex("909090909090")),
                 (0xf70fa, bytes.fromhex("0f8593000000"), bytes.fromhex("909090909090")),
                 (0x257f10, s("srally\\rally.exe", 17), s("rally.exe", 17)),
                 (0x257f24, s("srally\\lake.tex", 16), s("lake.tex", 16))],
    },
}

def patch(data, name):
    """Returns `data` (the exe called `name`: RALLYD3D.EXE or RALLY.EXE) with every patch applied; exits on
    unexpected bytes."""
    name = name.upper()
    if name not in PATCHES: sys.exit(f"no patches for {name} (known: {', '.join(PATCHES)})")
    data = bytearray(data)
    for pname, edits in PATCHES[name].items():
        state = set()
        for off, old, new in edits:
            cur = bytes(data[off:off + len(old)])
            state.add("new" if cur == new else "old" if cur == old else "bad")
        if state == {"new"}: print(f"  {name} {pname}: already applied"); continue
        if state != {"old"}: sys.exit(f"{name}: {pname}: unexpected bytes, not this exe? nothing written")
        for off, old, new in edits: data[off:off + len(new)] = new
        print(f"  {name} {pname}: applied")
    return bytes(data)

def main(path):
    out = patch(open(path, "rb").read(), os.path.basename(path))
    open(path, "wb").write(out)

if __name__ == "__main__":
    if len(sys.argv) != 2: sys.exit(__doc__)
    main(sys.argv[1])
