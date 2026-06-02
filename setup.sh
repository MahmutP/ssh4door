#!/usr/bin/env bash
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

echo "[+] ssh4door kurulum basliyor..."

if [ ! -d venv ]; then
    python3 -m venv venv
    echo "[+] Sanal ortam (venv) olusturuldu."
fi

source venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q

echo "[+] Kurulum tamam. Ornek kullanim:"
echo ""
echo "    source venv/bin/activate"
echo "    sudo python3 ssh4door.py                  # foreground"
echo "    sudo python3 ssh4door.py --bg             # background"
echo "    sudo python3 ssh4door.py -p 2222 -P sifre # custom port/sifre"
echo "    ./kill.sh                                 # durdur"
