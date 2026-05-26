import socket
import subprocess
import sys
import threading
import os

def forward_port(local_port, remote_port, container_name):
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listener.bind(('127.0.0.1', local_port))
    listener.listen(128)
    listener.settimeout(1.0)
    print(f"[forward] 127.0.0.1:{local_port} -> container:{remote_port}", flush=True)

    # Simple relay script that runs inside the container
    relay_script = f'''
import socket, sys, select
remote = socket.create_connection(("127.0.0.1", {remote_port}))
try:
    while True:
        r, _, _ = select.select([remote, sys.stdin], [], [])
        if remote in r:
            data = remote.recv(65536)
            if not data: break
            sys.stdout.buffer.write(data)
            sys.stdout.buffer.flush()
        if sys.stdin in r:
            data = sys.stdin.buffer.read(65536)
            if not data: break
            remote.sendall(data)
except Exception:
    pass
finally:
    remote.close()
'''

    while True:
        try:
            client, addr = listener.accept()
        except socket.timeout:
            continue

        def handle(csock):
            try:
                proc = subprocess.Popen(
                    ['docker', 'exec', '-i', container_name, 'python3', '-c', relay_script],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                )

                def client_to_proc():
                    try:
                        while True:
                            data = csock.recv(65536)
                            if not data: break
                            proc.stdin.write(data)
                            proc.stdin.flush()
                    except: pass
                    finally:
                        try: proc.stdin.close()
                        except: pass

                def proc_to_client():
                    try:
                        while True:
                            data = proc.stdout.read(65536)
                            if not data: break
                            csock.sendall(data)
                    except: pass
                    finally:
                        try: csock.close()
                        except: pass

                t1 = threading.Thread(target=client_to_proc, daemon=True)
                t2 = threading.Thread(target=proc_to_client, daemon=True)
                t1.start()
                t2.start()
                t1.join(timeout=300)
                t2.join(timeout=300)
            except Exception as e:
                print(f"[forward] error: {e}", flush=True)
            finally:
                try: csock.close()
                except: pass
                try: proc.terminate()
                except: pass

        t = threading.Thread(target=handle, args=(client,), daemon=True)
        t.start()


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} CONTAINER_NAME LOCAL_PORT:REMOTE_PORT [...]")
        sys.exit(1)
    container = sys.argv[1]
    threads = []
    for mapping in sys.argv[2:]:
        lp, rp = mapping.split(':')
        t = threading.Thread(target=forward_port, args=(int(lp), int(rp), container), daemon=True)
        t.start()
        threads.append(t)
    try:
        for t in threads:
            t.join()
    except KeyboardInterrupt:
        print("\n[forward] stopping...")
