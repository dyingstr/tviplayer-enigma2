#!/bin/bash
# Build script for enigma2-plugin-extensions-tviplayer.ipk
# Run from the TVIPlayer/ directory: bash build_ipk.sh

set -e

PACKAGE="enigma2-plugin-extensions-tviplayer"
VERSION="1.0.0"
OUT="${PACKAGE}_${VERSION}_all.ipk"

echo "==> A criar $OUT ..."

# Cleanup any previous build artefacts
rm -f data.tar.gz control.tar.gz "$OUT"

# --- data.tar.gz (plugin files) ---
tar --owner=0 --group=0 -czf data.tar.gz \
    usr/lib/enigma2/python/Plugins/Extensions/TVIPlayer

# --- control.tar.gz ---
tar --owner=0 --group=0 -czf control.tar.gz \
    -C CONTROL .

# --- debian-binary (required by opkg) ---
echo "2.0" > debian-binary

# --- wrap everything into an ar archive (.ipk) ---
ar r "$OUT" debian-binary control.tar.gz data.tar.gz

# Cleanup temp files
rm -f data.tar.gz control.tar.gz debian-binary

echo "==> Concluído: $OUT"
echo ""
echo "Para instalar na box:"
echo "  scp $OUT root@<IP_DA_BOX>:/tmp/"
echo "  ssh root@<IP_DA_BOX> 'opkg install /tmp/$OUT && killall -9 enigma2'"
