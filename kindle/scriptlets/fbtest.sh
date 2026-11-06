#!/bin/sh
FB=/mnt/us/libkh/bin/fbink
OUT=/mnt/us/fbtest.txt
{
  echo "== fbink -e"; $FB -e 2>&1
  echo "== fb0"; cat /sys/class/graphics/fb0/virtual_size /sys/class/graphics/fb0/rotate /sys/class/graphics/fb0/bits_per_pixel 2>&1
  echo "== version"; cat /etc/prettyversion.txt 2>&1; uname -a 2>&1
  echo "== tools"; command -v curl wget lipc-set-prop powerd_test initctl mntroot 2>&1
} > "$OUT"
$FB -c -m -y 10 "FBINK TEST OK - plug Kindle into PC" >> "$OUT" 2>&1
