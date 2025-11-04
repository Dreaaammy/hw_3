# HW3 - P2P NAT Hole Punching (rewritten)

This is a rewritten implementation of the provided homework solution for NAT hole punching.
It contains a rendezvous server and a universal UDP P2P client. The purpose is the same as the original:
- allow two clients (possibly behind NAT) to discover each other's addresses via a rendezvous server
- perform UDP hole punching so clients communicate directly (rendezvous server does not read data)

Files:
- rendezvous_udp.py  -- rewritten rendezvous server (UDP)
- p2p_udp_client.py  -- rewritten universal client which can register, connect, and exchange messages
- README.md (this file)
- traf/ (kept original pcap files for traffic analysis)

Quick start (simple local test):
1) Start the rendezvous server on a host reachable by both clients:
   ```bash
   python3 rendezvous_udp.py --host 0.0.0.0 --port 8888
   ```
2) Start two clients on different terminals (or machines) – each client needs a unique ID and the server IP:
   ```bash
   python3 p2p_udp_client.py alice 127.0.0.1 8888
   python3 p2p_udp_client.py bob   127.0.0.1 8888
   ```
   In real NAT tests replace `127.0.0.1` with the rendezvous server public IP.
3) On Alice's console run: `connect bob`
   The clients will attempt hole punching and then you can `send <text>` to send directly to the peer.
4) To stop, use `quit` or Ctrl-C.

Notes about privacy & requirements:
- Control messages (register/connect) are JSON and sent to the rendezvous server.
- Data messages (actual chat payloads) are sent directly peer-to-peer as UTF-8 text and are **not** forwarded or logged by the rendezvous server.
- For real NAT testing, use the CN-Alpine lab setup or Docker VMs with two interfaces for NAT.

Explanation of algorithm is included as comments in code.
