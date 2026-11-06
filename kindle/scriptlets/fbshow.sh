#!/bin/sh
OUT=/mnt/us/fbshow.txt
FB=/mnt/us/libkh/bin/fbink
curl -fsS --connect-timeout 8 --max-time 20 -o /mnt/us/fbshow.png http://192.168.0.135:8787/dashboard-kindle.png > "$OUT" 2>&1 || { $FB -c -m -y 10 "FETCH FAILED - see fbshow.txt"; exit 1; }
( sleep 5; $FB -c -f -W GC16 -g file=/mnt/us/fbshow.png >> "$OUT" 2>&1 ) > /dev/null 2>&1 &
