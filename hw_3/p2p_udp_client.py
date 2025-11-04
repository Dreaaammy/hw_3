#!/usr/bin/env python3
import socket, json, threading, argparse, logging, time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class P2PClient:
    def __init__(self, client_id, server_ip, server_port=8888, listen_port=0):
        self.id = str(client_id)
        self.server_addr = (server_ip, int(server_port))
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('0.0.0.0', int(listen_port)))
        self.listen_port = self.sock.getsockname()[1]
        self.peer_addr = None 
        self.peer_id = None
        self.running = True
        t = threading.Thread(target=self._listener, daemon=True)
        t.start()
        self.register()

    def register(self):
        msg = {'type': 'register', 'id': self.id, 'private_port': self.listen_port, 'private_ip': '0.0.0.0'}
        self.sock.sendto(json.dumps(msg).encode(), self.server_addr)
        logging.info(f"Sent register to {self.server_addr} from local port {self.listen_port}")

    def _listener(self):
        while self.running:
            try:
                data, addr = self.sock.recvfrom(4096)
                try:
                    obj = json.loads(data.decode())
                    self._handle_control(obj, addr)
                    continue
                except Exception:
                    pass
                text = data.decode(errors='replace')
                logging.info(f"[DATA] from {addr}: {text}")
            except Exception as e:
                logging.debug(f"Listener error: {e}")
                break

    def _handle_control(self, obj, addr):
        typ = obj.get('type')
        if typ == 'registered':
            logging.info(f"Registered OK, server saw you as public={obj.get('public')} private={obj.get('private')}")
        elif typ == 'peer_info':
            peer_id = obj.get('peer_id')
            pub = tuple(obj.get('peer_public'))
            priv = tuple(obj.get('peer_private'))
            logging.info(f"Peer info: id={peer_id} public={pub} private={priv}")
            self.peer_id = peer_id
            threading.Thread(target=self._do_hole_punch, args=(pub, priv), daemon=True).start()
        elif typ == 'peer_not_found':
            logging.warning("Server says peer not found")
        else:
            logging.info(f"Control message: {obj} from {addr}")

    def _do_hole_punch(self, pub, priv, attempts=10, interval=0.5):
        logging.info(f"Starting hole punching to public={pub} private={priv}")
        for i in range(attempts):
            if self.peer_addr:
                logging.info("Already connected to peer")
                return
            try:
                self.sock.sendto(f'ping-from-{self.id}'.encode(), pub)
                self.sock.sendto(f'ping-from-{self.id}'.encode(), priv)
            except Exception as e:
                logging.debug(f"Punch send error: {e}")
            time.sleep(interval)
        logging.info("Hole punching attempts finished; waiting for incoming or manual send to test connectivity")

    def connect(self, target_id):
        msg = {'type': 'connect', 'id': self.id, 'target': target_id, 'private_port': self.listen_port}
        self.sock.sendto(json.dumps(msg).encode(), self.server_addr)
        logging.info(f"Requested connection to {target_id} from rendezvous")

    def send(self, text):
        if not self.peer_addr:
            logging.error("No peer connected. Use connect <id> and complete punching first.")
            return
        self.sock.sendto(text.encode(), self.peer_addr)
        logging.info(f"Sent to {self.peer_addr}: {text}")

    def status(self):
        logging.info(f"id={self.id} local={self.sock.getsockname()} peer_id={self.peer_id} peer_addr={self.peer_addr}")

    def stop(self):
        self.running = False
        try:
            self.sock.close()
        except:
            pass

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('id')
    p.add_argument('server_ip')
    p.add_argument('server_port', nargs='?', default=8888)
    p.add_argument('--port', type=int, default=0, help='local UDP port to bind (0=auto)')
    args = p.parse_args()
    client = P2PClient(args.id, args.server_ip, args.server_port, args.port)

    # Simple interactive loop
    try:
        while True:
            cmd = input('> ').strip()
            if not cmd:
                continue
            parts = cmd.split(' ', 1)
            if parts[0] == 'connect' and len(parts) > 1:
                client.connect(parts[1].strip())
            elif parts[0] == 'send' and len(parts) > 1:
                client.send(parts[1])
            elif parts[0] == 'status':
                client.status()
            elif parts[0] in ('quit', 'exit'):
                break
            else:
                print('Commands: connect <id>, send <text>, status, quit')
    except KeyboardInterrupt:
        pass
    finally:
        client.stop()
