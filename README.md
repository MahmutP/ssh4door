<p align="center">
  <img src="https://img.shields.io/badge/python-3.8%2B-blue" alt="Python">
  <img src="https://img.shields.io/badge/license-Apache%202.0-green" alt="License">
  <img src="https://img.shields.io/badge/ssh-paramiko-orange" alt="Paramiko">
</p>

# ssh4door

> **EN:** A lightweight fake SSH server for remote access.  
> **TR:** Uzaktan erişim için hafif bir sahte SSH sunucusu.

Built with [Paramiko](https://github.com/paramiko/paramiko). Listens for SSH connections, authenticates clients, and provides shell access — all without a real SSH daemon.

---

## ⚠️ Warning / Uyarı

**EN:** This tool opens a backdoor to your system. Use only on your own machines or with explicit authorization. The author is not responsible for any misuse.

**TR:** Bu araç sisteminize bir arka kapı açar. Yalnızca kendi makinelerinizde veya açık izin alarak kullanın. Yazar, kötüye kullanımdan sorumlu değildir.

---

## Features / Özellikler

| English | Türkçe |
|---|---|
| Interactive shell and single-command (`exec`) support | Etkileşimli shell ve tek komut (`exec`) desteği |
| Root mode (passwordless login when run as root) | Root modu (root ile çalıştırılınca şifresiz giriş) |
| Custom port, password, and host binding | Özel port, şifre ve host tanımlama |
| Background daemon mode with PID file | PID dosyası ile background daemon modu |
| Simple process management (`kill.sh`) | Basit process yönetimi (`kill.sh`) |
| Turkish & English log output | Türkçe & İngilizce log çıktısı |

---

## Requirements / Gereksinimler

- **EN:** Python 3.8+, `sudo` (for privileged ports or root mode)
- **TR:** Python 3.8+, `sudo` (yetkili portlar veya root modu için)

---

## Quick Start / Hızlı Başlangıç

```bash
# Clone / Kopyala
git clone https://github.com/yourusername/ssh4door.git
cd ssh4door

# Setup / Kurulum
chmod +x setup.sh kill.sh
./setup.sh

# Activate venv / Sanal ortamı aktif et
source venv/bin/activate
```

---

## Usage / Kullanım

### Foreground / Ön Planda

```bash
# Default port 999, password 12345
sudo python3 ssh4door.py

# Custom port and password
sudo python3 ssh4door.py --port 2222 --password sifre123
```

### Background / Arka Planda (Daemon)

```bash
# Start / Başlat
sudo python3 ssh4door.py --bg

# Stop / Durdur
./kill.sh
```

### Options / Seçenekler

| Argument | Short | EN (Description) | TR (Açıklama) | Default |
|---|---|---|---|---|
| `--bg` | `-b` | Run in background (daemon) | Arka planda çalıştır | off |
| `--port` | `-p` | Listening port | Dinlenecek port | `999` |
| `--password` | `-P` | SSH password | SSH şifresi | `12345` |
| `--host` | `-H` | Bind address | Bağlanılacak adres | `0.0.0.0` |
| `--pid-file` | | PID file path | PID dosya yolu | `/tmp/ssh4door.pid` |
| `--log-file` | | Log file path (bg mode) | Log dosya yolu (bg modu) | `/tmp/ssh4door.log` |

---

## Connecting / Bağlanma

```bash
# EN: Password auth (non-root mode) | TR: Şifreli giriş (root değilken)
ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p 999 user@<host-ip>

# EN: Single command execution | TR: Tek komut çalıştırma
ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p 999 user@<host-ip> "uname -a"
```

> **EN:** Replace `<host-ip>` with the target IP. Use `curl ifconfig.me` to get your public IP.  
> **TR:** `<host-ip>` yerine hedef IP'yi yazın. Kendi public IP'nizi `curl ifconfig.me` ile öğrenebilirsiniz.

---

## How It Works / Nasıl Çalışır

1. **EN:** Creates an RSA host key (stored as `server.key`)  
   **TR:** Bir RSA host anahtarı oluşturur (`server.key` olarak kaydedilir)

2. **EN:** Listens for SSH connections on the specified port  
   **TR:** Belirtilen portta SSH bağlantılarını dinler

3. **EN:** Authenticates via password (or passwordless if running as root)  
   **TR:** Şifre ile doğrular (root ile çalışıyorsa şifresiz)

4. **EN:** Spawns a PTY-based shell for each connected client  
   **TR:** Her bağlı istemci için PTY tabanlı bir shell açar

5. **EN:** `exec` commands run in a subprocess and return output  
   **TR:** `exec` komutları bir alt süreçte çalışır ve çıktıyı döndürür

---

## Project Structure / Proje Yapısı

```
ssh4door/
├── ssh4door.py          # Main server / Ana sunucu
├── setup.sh             # Installation script / Kurulum betiği
├── kill.sh              # Stop daemon / Daemon durdurma betiği
├── requirements.txt     # Python dependencies / Bağımlılıklar
├── README.md            # This file / Bu dosya
└── server.key           # Generated RSA host key (auto) / Oluşturulan RSA anahtarı
```

---

## Logs / Günlükler

**EN:** In background mode, all output goes to `/tmp/ssh4door.log`. Monitor it with:

**TR:** Background modunda tüm çıktı `/tmp/ssh4door.log` dosyasına gider. İzlemek için:

```bash
tail -f /tmp/ssh4door.log
```

### Sample Log / Örnek Log

```
[+] Yeni RSA host key olusturuldu: .../ssh4door/server.key
[+] ssh4door hazir | 0.0.0.0:999
[+] ROOT MOD: sifresiz giris aktif
[+] Background modda calisiyor (PID: 12345)
[+] Baglanti: 192.168.1.100:54321
[+] kullanici basariyla giristi
[+] 192.168.1.100:54321 -> shell baslatiliyor
[-] 192.168.1.100:54321 -> baglanti kapandi
```

---

## Security Notes / Güvenlik Notları

- **EN:** Default credentials (`12345`) should be changed immediately.  
  **TR:** Varsayılan şifre (`12345`) hemen değiştirilmelidir.

- **EN:** Running as root grants passwordless access to everyone — use with caution.  
  **TR:** Root ile çalıştırmak herkese şifresiz erişim sağlar — dikkatli kullanın.

- **EN:** This is NOT a production SSH server. No encryption beyond Paramiko's defaults.  
  **TR:** Bu bir üretim SSH sunucusu DEĞİLDİR. Paramiko varsayılanlarının ötesinde şifreleme yoktur.

---

## License / Lisans

Apache 2.0
