#!/usr/bin/env bash
set -euo pipefail

PID_FILE="${1:-/tmp/ssh4door.pid}"

if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if kill -0 "$PID" 2>/dev/null; then
        echo "[+] ssh4door (PID: $PID) durduruluyor..."
        kill "$PID"
        rm -f "$PID_FILE"
        echo "[+] ssh4door durduruldu."
    else
        echo "[-] ssh4door (PID: $PID) calismiyor. PID dosyasi temizleniyor..."
        rm -f "$PID_FILE"
    fi
else
    echo "[-] PID dosyasi bulunamadi: $PID_FILE"
    if PIDS=$(pgrep -f "python3.*ssh4door" 2>/dev/null); then
        echo "[+] ssh4door process(leri) bulundu: $PIDS"
        kill $PIDS 2>/dev/null
        echo "[+] Durduruldu."
    else
        echo "[-] ssh4door process'i bulunamadi."
        exit 1
    fi
fi
