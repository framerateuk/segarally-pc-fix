# Sega Rally Championship (PC, 1997) on modern PCs and the Steam Deck

## Why this exists

I have fond memories of playing Sega Rally for hours on my friend's Saturn. I got the PC version
later, but my Pentium 120 always struggled with it. On a modern PC it runs as well as the Saturn
version, at a higher resolution. Getting there means a CD check, no quit key, CD-audio music and,
for the Direct3D version, half-minute loads; this kit sorts that out.

## What this does

Turns **your own** Sega Rally Championship PC CD into a folder that runs on the Steam Deck (Proton)
or on Windows 10/11, with no installer and no registry entries, in one or both of its two versions:

- **The software version** (`RALLY.EXE`), from Sega's official patch 2.1 (MMX), patched here so it
  needs no CD and keeps its settings in the game folder.
- **The Direct3D version** (`RALLYD3D.EXE`), from vetz's 2012 Unofficial Direct3D patch, through
  dgVoodoo2 at your screen's height, 4:3 with black bars. Loading no longer takes 30-50 seconds
  (it redrew a loading bar in a way that waited for the screen at every step).
- Optionally **VirtuaIceMan and vetz's mod**: engine sounds without clipping, smoother loading
  screens, better 2D backdrops, and the Direct3D version's game-over music from the CD.
- **CD soundtrack** from OGG files ripped from your disc.
- **Gamepad** set up from the start in both versions, the D-pad steering, and **Tab quits** (Sega
  gave the game no quit key).
- 30 frames a second, as on the Saturn.

**No game files are in this repository, and neither are the patches or the mod.** Everything comes
from your disc and the downloads below when you run `build.py`.

## What you need

| | |
|---|---|
| The game | The **Sega Rally Championship PC CD** (Sega, December 1996; `SRALLY\RALLY.EXE` 1.0) as `.cue` + `.bin` or CloneCD `.ccd` + `.img`, with its 22 audio tracks. `build.py` checks the exe and stops on another version. |
| For the software version | **Sega's patch 2.1 (MMX)**, for example from [Race Sim Central](https://racesimcentral.net/?p=48545). Unpack it and give `build.py` its `RALLY.EXE` (or the folder or zip holding it). |
| For the Direct3D version | **vetz's Unofficial Direct3D patch** (2012), from his [VOGONS thread](https://www.vogons.org/viewtopic.php?p=266799). Give `build.py` the zip as downloaded, or its unpacked folder. |
| Optional | **The Sega Rally Championship Mod** by VirtuaIceMan and vetz, from the same thread. It's a `.rar`: unpack it (WinRAR, or The Unarchiver on a Mac; 7-Zip can't) and give `build.py` the folder. |
| Python | 3.8 or newer (python.org on Windows; already on macOS/Linux). |
| An OGG encoder | `oggenc` (vorbis-tools; Windows builds at rarewares.org) or `ffmpeg`, on the PATH. |
| dgVoodoo2 **2.79.3** | by Dege: [GitHub release v2.79.3](https://github.com/dege-diosg/dgVoodoo2/releases/tag/v2.79.3). Use 2.79.3: newer versions don't start under Wine/Proton. Keep the zip as downloaded. |
| ogg-winmm | by AyuanX: [GitHub releases](https://github.com/ayuanx/ogg-winmm/releases) (tested with v2025.01.16). Keep the zip as downloaded. |

`build.py` checks each download is the one the kit was made for. You need at least one of the two
patches; with both you get both versions in one folder.

## Build

```
python3 build.py SegaRally.ccd --mmx mmxrally/RALLY.EXE --d3d Sega_Rally_Championship_Unofficial_Direct3D_patch.zip \
    --mod Sega_Rally_Championship_Mod --dgvoodoo dgVoodoo2_79_3.zip --ogg-winmm ogg-winmm_binary.zip
```

creates `SegaRallyPC/` with `game/` and `segarally_launch.sh` (for the Steam Deck), in about a
minute. Leave out `--d3d`, `--mmx` or `--mod` for what you don't have. The same `game/` folder runs on
Windows; `--windows` leaves out the launch script. `--out DIR` puts the result somewhere else. The
disc's 1.0 exe and the untouched patch exes are kept in `game/_spare/`.

## Play on the Steam Deck

1. Copy `SegaRallyPC/` to the Deck, for example to `/home/deck/Games/SegaRallyPC/`.
2. Desktop Mode: Steam > Add a Non-Steam Game > Browse > `.../SegaRallyPC/game/RALLYD3D.EXE` (Direct3D)
   or `.../game/RALLY.EXE` (software). Add both as two shortcuts if you like. Rename the shortcut
   "Sega Rally Championship".
3. Properties > Compatibility: force **Proton 9.0**. Pin it rather than floating on Experimental.
4. Properties > Launch Options (the same for both):
   ```
   /home/deck/Games/SegaRallyPC/segarally_launch.sh %command%
   ```
5. Controller layout: the standard **Gamepad** layout, plus **Tab** on a spare button (View, say) in
   Steam's controller settings: Tab is the quit key. If a version comes up in a window, press
   Alt+Enter, the game's own toggle.

## Play on Windows

Run `game/RALLYD3D.EXE` (Direct3D) or `game/RALLY.EXE` (software). An Xbox pad works as on the Deck.

## Controls

| Pad | In a race | In the menus |
|---|---|---|
| Left stick or D-pad | steer | move |
| A | accelerate | select |
| X | brake | |
| B | | back |
| Y | change view | |
| RB / LB | gear up / down (manual gearbox) | |

Steering is on / off, as the game reads any pad (only its wheel mode is analogue). The triggers
aren't read by the game; map them to A and X in Steam's controller settings if you'd like them as
accelerate and brake. Tab quits; Esc is the game's second "back" key. The Direct3D version keeps its
settings in `game/RALLY.INI`, the software version in `game/SRMMX.INI` (the two can't share: the
same control format, different device numbering).

## Settings

- The Direct3D version's records (the Saturn's "backup RAM") are `game/SRALLY_0`; the ghost cars
  (`game/*.GST`) are shared by both versions.
- Sharper or softer (Direct3D): `[DirectX] Resolution` in `game/dgVoodoo.conf`.
- Frame rate: `FPSLimit = 30` in `game/dgVoodoo.conf`. The game has no limiter of its own and steps
  per frame, as the Saturn did at 30.
- Music level: `CDDAVolume` in `game/winmm.ini`.
- Deck renderer: `RENDERER=wined3d` before the script path in the launch options uses Wine's own
  DirectDraw / Direct3D instead of dgVoodoo (no frame cap).

## Troubleshooting

- *"Please insert Sega Rally CD."*: you're running the disc's 1.0 exe from `_spare/`.
- *Loads take half a minute*: you're running the unpatched Direct3D exe from `_spare/`.
- *No controls at all*: an INI from another install with an empty or preset controls section;
  rebuild, or copy the kit's `config/RALLY.INI` / `config/SRMMX.INI` over it.
- *The game runs too fast*: the frame cap isn't applied; check `ddraw.dll` and `dgVoodoo.conf` are
  beside the exe.
- *No music*: on the Deck `launch.log` must show `WINEDLLOVERRIDES=winmm=n,b;...` (no log: the
  launch option is missing `%command%`), and `game/Music/Track02.ogg` must exist.
- *Judder on a G-Sync / FreeSync monitor*: turn variable refresh off for this game.

## What's in this repository

| File | What |
|---|---|
| `build.py` | Builds the folder: the CD's full install, then the Direct3D patch and the mod laid over it, the exes patched, the soundtrack ripped, the wrappers and settings added. Python standard library only. |
| `patch_exe.py` | The exe patches for both versions, each explained; also runs on its own. |
| `expand_szdd.py` | Expands the Direct3D patch's Microsoft-compressed (SZDD) model and sky files, which made loading slow. |
| `disc.py` | Reads the CD image: `.cue`/`.bin` or `.ccd`/`.img`, ISO 9660 and audio tracks. |
| `config/` | The two versions' settings with the pad set up, and dgVoodoo2's. |
| `steamdeck/segarally_launch.sh` | Proton launch wrapper: DLL overrides. |
| `docs/TECHNICAL.md` | How the game works and what each patch does. |

## Credits

- **Sega** made and published Sega Rally Championship for the PC, and its patch 2.1. Please own the
  game: this kit needs your disc.
- **vetz**: the 2012 Unofficial Direct3D patch, which brought the Direct3D version (only ever bundled
  with the Orchid Righteous 3D card) to the retail game. **VirtuaIceMan** and **vetz**: the mod.
- **Dege**: dgVoodoo2. **AyuanX**: ogg-winmm.

## License

The scripts and docs in this repository: MIT (see `LICENSE`). The license covers only this
repository's own files, not the game, the patches, the mod, dgVoodoo2 or ogg-winmm.

Not affiliated with or endorsed by the game's rights holders.
