import socket, json, argparse, logging, threading, time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class RendezvousServer:
    def __init__(self, host='0.0.0.0', port=8888):
        self.addr = (host, int(port))
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(self.addr)
        self.lock = threading.Lock()
        # clients: client_id -> {'public': (ip,port), 'private': (ip,port), 'last_seen': ts}
        self.clients = {}
        logging.info(f"Rendezvous listening on {self.addr}")

    def run(self):
        while True:
            try:
                data, addr = self.sock.recvfrom(4096)
                try:
                    msg = json.loads(data.decode())
                except Exception:
                    logging.warning(f"Non-json packet from {addr}; ignoring control handler")
                    continue
                typ = msg.get('type')
                if typ == 'register':
                    self.handle_register(msg, addr)
                elif typ == 'connect':
                    self.handle_connect(msg, addr)
                elif typ == 'keepalive':
                    self.handle_keepalive(msg, addr)
                else:
                    logging.warning(f"Unknown message type {typ} from {addr}")
            except KeyboardInterrupt:
                logging.info('Server interrupted, exiting')
                break
            except Exception as e:
                logging.exception('Server error')

    def handle_register(self, msg, addr):
        client_id = str(msg.get('id'))
        private_port = int(msg.get('private_port', 0))
        private_ip = msg.get('private_ip') or addr[0]
        public = addr 
        private = (private_ip, private_port)
        with self.lock:
            self.clients[client_id] = {'public': public, 'private': private, 'last_seen': time.time()}
        logging.info(f"Registered {client_id}: public={public}, private={private}")
        reply = {'type': 'registered', 'id': client_id, 'public': public, 'private': private}
        self.sock.sendto(json.dumps(reply).encode(), addr)

    def handle_connect(self, msg, addr):
        requester = str(msg.get('id'))
        target = str(msg.get('target'))
        with self.lock:
            target_info = self.clients.get(target)
            requester_info = self.clients.get(requester)
        if not target_info:
            logging.info(f"Connect request: target {target} not found for {requester}")
            resp = {'type': 'peer_not_found', 'target': target}
            self.sock.sendto(json.dumps(resp).encode(), addr)
            return
        payload_for_requester = {'type': 'peer_info',
                                 'peer_id': target,
                                 'peer_public': target_info['public'],
                                 'peer_private': target_info['private']}
        payload_for_target = {'type': 'peer_info',
                              'peer_id': requester,
                              'peer_public': requester_info['public'] if requester_info else addr,
                              'peer_private': requester_info['private'] if requester_info else (addr[0], msg.get('private_port', addr[1]))}
        self.sock.sendto(json.dumps(payload_for_requester).encode(), requester_info['public'] if requester_info else addr)
        self.sock.sendto(json.dumps(payload_for_target).encode(), target_info['public'])
        logging.info(f"Sent peer info: {requester} <-> {target}")

    def handle_keepalive(self, msg, addr):
        client_id = str(msg.get('id'))
        with self.lock:
            if client_id in self.clients:
                self.clients[client_id]['last_seen'] = time.time()

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--host', default='0.0.0.0')
    p.add_argument('--port', default=8888, type=int)
    args = p.parse_args()
    srv = RendezvousServer(args.host, args.port)
    srv.run()
