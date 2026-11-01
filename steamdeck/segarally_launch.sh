#!/bin/bash
# Sega Rally Championship (PC, 1997) Steam Deck / Proton launch wrapper.
#
# Keep it beside game/ (build.py puts it there). With the folder at /home/deck/Games/SegaRallyPC:
#   Shortcut target: /home/deck/Games/SegaRallyPC/game/RALLYD3D.EXE (Direct3D) or .../game/RALLY.EXE (software,
#   MMX), Start In: .../game/
#   Compatibility: Proton 9.0
#   Launch Options: /home/deck/Games/SegaRallyPC/segarally_launch.sh %command%
# Both exes are patched (patch_exe.py): no CD hunt, every asset loads from game/, so no fake CD-ROM drive and no
# registry are needed.
#
# Every launch sets DLL overrides so Wine loads the wrappers sitting beside the exe:
#   winmm.dll              ogg-winmm: CD audio from Music/TrackNN.ogg
#   ddraw.dll, d3dimm.dll  dgVoodoo2 2.79.3: DirectDraw + Direct3D -> D3D11 -> DXVK (30 fps cap, max resolution)
#
# RENDERER (set before the script path in Launch Options, default dgvoodoo):
#   dgvoodoo  ddraw+d3dimm from dgVoodoo2
#   wined3d   plain Wine ddraw/d3d (no fps cap)
#   Example:  RENDERER=wined3d /home/deck/Games/SegaRallyPC/segarally_launch.sh %command%

set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG="$HERE/launch.log"
RENDERER="${RENDERER:-dgvoodoo}"
log() { echo "[$(date '+%H:%M:%S')] $*" >>"$LOG"; }
: >"$LOG"
log "args: $*"
log "RENDERER=$RENDERER  STEAM_COMPAT_DATA_PATH=${STEAM_COMPAT_DATA_PATH:-unset}"

# Proton appends its own overrides after ours.
OVR="winmm=n,b"
case "$RENDERER" in
  dgvoodoo) OVR="$OVR;ddraw=n,b;d3dimm=n,b" ;;
  wined3d)  OVR="$OVR;ddraw=b;d3dimm=b" ;;
  *)        log "unknown RENDERER '$RENDERER', using dgvoodoo"; OVR="$OVR;ddraw=n,b;d3dimm=n,b" ;;
esac
export WINEDLLOVERRIDES="${OVR}${WINEDLLOVERRIDES:+;$WINEDLLOVERRIDES}"
log "WINEDLLOVERRIDES=$WINEDLLOVERRIDES"

# Debugging: if a file named PROTON_LOG exists beside this script, Proton writes steam-<appid>.log here (crash
# addresses, exceptions). Create / delete it from Desktop Mode; no launch-option edit.
if [ -e "$HERE/PROTON_LOG" ]; then
  export PROTON_LOG=1 PROTON_LOG_DIR="$HERE"
  log "PROTON_LOG on -> $HERE/steam-*.log"
  # Extra Wine debug channels for that log: a file WINEDEBUG beside this script holding e.g. +dsound
  if [ -s "$HERE/WINEDEBUG" ]; then
    export WINEDEBUG="+timestamp,+tid,+seh,+loaddll,$(tr -d ' \n' < "$HERE/WINEDEBUG")"
    log "WINEDEBUG=$WINEDEBUG"
  fi
fi

for f in winmm.dll winmm.ini ddraw.dll d3dimm.dll dgVoodoo.conf Music/Track02.ogg; do
  [ -e "$HERE/game/$f" ] || log "WARNING: game/$f missing"
done

log "exec: $*"
exec "$@"
