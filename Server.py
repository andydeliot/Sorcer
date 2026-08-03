import socket
import pickle
import struct
import time
import threading
import argparse
import Gameplay as gp

from Gameplay import *
import pygame
from pygame import *

pygame.init()


# Print local ip.
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
try:
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]
finally:
    s.close()
print("Adresse ip locale : ", ip)


def parse_args():
    parser = argparse.ArgumentParser(description="Sorcer UDP server")
    parser.add_argument("--host", default="0.0.0.0", help="Listening host")
    parser.add_argument("--port", type=int, default=5000, help="Listening port")
    return parser.parse_args()


args = parse_args()


HOST = args.host
PORT = args.port

server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server.bind((HOST, PORT))

print(f"Serveur UDP en écoute {HOST}:{PORT}")

clients = {}  # addr -> {"last_msg": ...}
lock = threading.Lock()

MAX_CLIENTS = 4

# -------------------------
# utils UDP
# -------------------------
def send_obj(addr, obj):
    data = pickle.dumps(obj)
    size = struct.pack("!I", len(data))
    server.sendto(size + data, addr)


def recv_obj(data):
    size = struct.unpack("!I", data[:4])[0]
    return pickle.loads(data[4:4+size])


# -------------------------
# thread réception UDP
# -------------------------
def receive_loop():
    print("Receive loop started")

    while True:
        try:
            data, addr = server.recvfrom(65536)

            obj = recv_obj(data)

            with lock:
                if addr not in clients and len(clients) < MAX_CLIENTS:
                    print(f"[+] Nouveau client: {addr}")
                    clients[addr] = {"last_msg": None}

                if addr in clients:
                    clients[addr]["last_msg"] = obj

        except Exception as e:
            print("Erreur recv:", e)

threading.Thread(target=receive_loop, daemon=True).start()

# -------------------------
# game loop
# -------------------------

def game_loop():
    clock = pygame.time.Clock()
    gp.start(reset_scores=True)
    round_active = False

    def clear_client_inputs():
        with lock:
            for data in clients.values():
                data["last_msg"] = None

    clear_client_inputs()

    while True:
        clock.tick(50)

        with lock:
            addrs = list(clients.keys())

        if len(addrs) == 4:
            adr_p1, adr_p2, adr_p3, adr_p4 = addrs[0], addrs[1], addrs[2], addrs[3]
            
            msg_p1 = clients[adr_p1]["last_msg"]
            msg_p2 = clients[adr_p2]["last_msg"]
            msg_p3 = clients[adr_p3]["last_msg"]
            msg_p4 = clients[adr_p4]["last_msg"]

            s_p1, s_p2, s_p3, s_p4 = gp.p1, gp.p2, gp.p3, gp.p4

            if not round_active:
                if all(m is not None and m != "" for m in [msg_p1, msg_p2, msg_p3, msg_p4]):
                    round_active = True
                    clear_client_inputs()
                else:
                    try:
                        scores = gp.get_team_scores()
                        send_obj(adr_p1, {"players": [s_p1, s_p2, s_p3, s_p4], "scores": [scores[0], scores[1]]})
                        send_obj(adr_p2, {"players": [s_p2, s_p1, s_p4, s_p3], "scores": [scores[0], scores[1]]})
                        send_obj(adr_p3, {"players": [s_p3, s_p4, s_p1, s_p2], "scores": [scores[1], scores[0]]})
                        send_obj(adr_p4, {"players": [s_p4, s_p3, s_p2, s_p1], "scores": [scores[1], scores[0]]})
                    except Exception as e:
                        print("send error:", e)
                    continue

            msg_p1 = None if msg_p1 == "" else msg_p1
            msg_p2 = None if msg_p2 == "" else msg_p2
            msg_p3 = None if msg_p3 == "" else msg_p3
            msg_p4 = None if msg_p4 == "" else msg_p4


            s_p1, s_p2, s_p3, s_p4 = gp.loop([msg_p1, msg_p2, msg_p3, msg_p4])
            if (s_p1.pv <= 0 and s_p2.pv <= 0) or (s_p3.pv <= 0 and s_p4.pv <= 0):
                gp.start(reset_scores=False)
                round_active = False
                clear_client_inputs()
                s_p1, s_p2, s_p3, s_p4 = gp.p1, gp.p2, gp.p3, gp.p4
            try:
                scores = gp.get_team_scores()
                send_obj(adr_p1, {"players": [s_p1, s_p2, s_p3, s_p4], "scores": [scores[0], scores[1]]})
                send_obj(adr_p2, {"players": [s_p2, s_p1, s_p4, s_p3], "scores": [scores[0], scores[1]]})
                send_obj(adr_p3, {"players": [s_p3, s_p4, s_p1, s_p2], "scores": [scores[1], scores[0]]})
                send_obj(adr_p4, {"players": [s_p4, s_p3, s_p2, s_p1], "scores": [scores[1], scores[0]]})
            except Exception as e:
                print("send error:", e)


game_loop()
