# How it works

Notes on Sega Rally Championship for the PC (Sega, Windows 95, retail CD of December 1996), its two
versions and the downloads the kit uses. `patch_exe.py`'s header lists each patch's bytes and
addresses.

## The versions and the downloads

Sega released the PC game with two renderers. The retail **software** version (`Rally.exe`, 1.0 on
the disc) got **patch 2.1** (22 July 1997): MMX support and more pad options, a new `RALLY.EXE`. The
**Direct3D** version was only ever bundled on the Orchid Righteous 3D (Voodoo 1) driver disc. In
2012 vetz took that exe and its extra data, made it run on top of a retail full install and removed
its CD check: the **Unofficial Direct3D patch** (`RALLYD3D.EXE`, `LOCALIZE.DLL`, `DXENABLE.DLL` the
device chooser, `FF.DLL` force feedback, `MODELS\`, `SCROLL\`, palettes, `RALLY.INI`, `SRALLY_0`). A
companion **mod** by VirtuaIceMan and vetz reworks the engine WAVs to fix clipping, smooths the
`*_START.BG` loading screens and the `*16.BG` backdrops, and replaces the Direct3D version's
low-quality `GAMEOVER.wav` with a rip of the CD track.

`build.py` reproduces "full install, then the Direct3D patch, then the mod": the disc's `SRALLY\`
folder (what the installer's full install copies; the installer itself only adds `RALLY.INI`, the
help file and Start menu entries), each layer laid over the last. Names merge case-insensitively:
the disc has `Wave\`, the patches `WAVE\`. Left out: the 1.0 exe (in `_spare/`), its map file,
vetz's `CPUGRAB` (a CPU hog against the game running too fast; dgVoodoo's frame cap does that), the
help index and the readmes.

## Disc check

The retail exes scan every drive letter, keep the CD-ROM ones and look for `%c:\SRALLY\` files,
else "Please insert Sega Rally CD.". In `RALLYD3D.EXE` (0x4ca500) vetz changed the format string to
`.\`, removed the drive-type test and pointed the probes at `.\rallyd3d.exe` and
`.\scroll\sky\desert00.bm_`: the "CD" is the working directory, as is every data path built from it.
`patch_exe.py` does the same to patch 2.1's `RALLY.EXE` (`nocd`: 0x4f7b80, 0x4f7ca0): the format
`%c:\` -> `.\`, the two drive-type tests removed, the probes `rally.exe` and `lake.tex` in the game
folder. Data paths come from `[Directory] ExePath` (empty = the working directory), so nothing reads
the "CD". So the shortcut's Start In must be the `game` folder.

## Settings (ini)

Patch 2.1's exe passes a bare `rally.ini`, which Windows looks for in the Windows folder. `ini` makes
it `.\SRMMX.INI`, its own file: the control format is the Direct3D exe's, but the device numbers
differ (Direct3D: 0 keyboard, 1 joystick, 2 SideWinder pad, 3 joypad, 4 wheel; MMX: 0 keyboard,
1 SideWinder pad, 2 joystick, 3 joypad, 4 wheel), so one file can't serve both.

Both read `[InputDevice1P]` / `[InputDevice2P]`: `DeviceSelect` (the active device), `DeviceTypeN`
(2 = Custom, the `keyNNN` values; anything else is one of the game's preset layouts, whatever
`keyNNN` says) and `keyNNN` (device N, slot NNN mod 10: virtual-key codes, 8001 / 8002 joystick Y
up / down, 8003-800c joystick buttons 1-10). A missing section reads as all zero: no controls at
all, the first symptom on the Deck. The kit's `RALLY.INI` and `SRMMX.INI` set a Custom joystick
layout for both players: A accelerate, X brake, Y view, RB / LB gears, A / B select / back.

## Gamepad (dpad)

The game reads the first joystick through winmm `joyGetPosEx`: X, Y and the buttons. Z, where an
Xbox pad's triggers are, is never read. Everything becomes a Saturn pad bit; accelerate and brake
are on / off even in the wheel mode, and in the joystick mode X is reduced to Left / Right too
(0x47de19), so steering with a pad is on / off. `dpad` makes the per-frame read (Direct3D 0x45b7c6,
MMX 0x49d6b2) also ask for the POV hat, and a 57-byte routine after it turns a pressed D-pad into a
fully pushed stick: left or right.

## Quitting (tabquit)

Sega gave the game no quit key: only Alt+F4 or the menu bar's Exit. Esc is a hard-wired second
"back" in every menu, and a letter would collide with the record name entry. So Tab quits: both
window classes point at a 43-byte stub in the zero slack at the end of `.text` (`slack` raises the
section's VirtualSize to cover it, still the same page) that turns `WM_KEYDOWN` + `VK_TAB` into
`WM_CLOSE`, the same road as Alt+F4, and passes everything else to the real window procedure.

## Loading (nobar, expand_szdd.py)

The Direct3D version took 30-50 s per load under dgVoodoo. Its loading-bar step (0x413320) drew on
the primary surface through `GetDC` / `ReleaseDC` at every step, and each release presents a frame
and waits for the display and the frame cap. `nobar` makes it return at once (its counter is read
only by the bar code). The Direct3D data (`MODELS\*.MD_ *.TE_`, `SCROLL\SKY\*.BM_`, 93 files) is
Microsoft COMPRESS (SZDD), read through `LZOpenFileA` / `LZRead`, which also read a plain file;
`expand_szdd.py` expands it in place (14 MB -> 58 MB), saving the work on every load.

## Graphics and speed

DirectDraw and Direct3D (DirectX 5) go through dgVoodoo2 2.79.3. The game offers 320x240 and
640x480; `[DirectX] Resolution = max` renders 640x480 at the largest 4:3 size that fits the screen.
Patch 2.1's software version plays only in 16-bit colour and switches itself to full screen at
640x480x16 when the desktop isn't 16-bit. The game has no frame limiter of its own (the Direct3D
patch's readme reports it running too fast on modern PCs) and steps per frame, as the Saturn
original did at 30 fps, so `dgVoodoo.conf` holds 30 with vsync.

## CD audio

`mciSendCommandA` opens the default `cdaudio` device, reads every track's position into a table
(0x41bf70) and plays from it, with no length check. Each track is ripped from its INDEX 01 to the
next track's start.
