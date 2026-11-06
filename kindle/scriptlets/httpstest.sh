#!/bin/sh
URL=https://YOUR-PC.YOUR-TAILNET.ts.net/dashboard-kindle.png
OUT=/mnt/us/httpstest.txt
FB=/mnt/us/libkh/bin/fbink
curl --version > "$OUT" 2>&1
if curl -fsS --connect-timeout 10 --max-time 30 -o /mnt/us/httpstest.png "$URL" >> "$OUT" 2>&1; then $FB -c -m -y 10 "HTTPS OK - plug Kindle into PC" > /dev/null 2>&1; else $FB -c -m -y 10 "HTTPS FAILED - plug Kindle into PC" > /dev/null 2>&1; fi
