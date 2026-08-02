from Gameplay import *
import socket
import pickle
import struct
import threading
import pygame
from pygame import *

pygame.init()

HOST = "127.0.0.1"
PORT = 5000

client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client.connect((HOST, PORT))


def send_obj(obj):
    data = pickle.dumps(obj)
    size = struct.pack("!I", len(data))
    client.sendto(size + data, (HOST, PORT))


def recv_loop():
    global p1, p2, p3, p4
    while True:
        data, _ = client.recvfrom(65536)
        size = struct.unpack("!I", data[:4])[0]
        p1, p2, p3, p4 = pickle.loads(data[4:4 + size])


threading.Thread(target=recv_loop, daemon=True).start()

p1, p2, p3, p4 = Sorcer(spells), Sorcer(spells), Sorcer(spells), Sorcer(spells)

running = True
clock = pygame.time.Clock()
last_sent = 0

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    now = pygame.time.get_ticks()
    if now - last_sent >= 100:
        # Envoyer une action valide au serveur pour démarrer la manche.
        # Le format ";0" sélectionne une cible sans lancer de sort.
        send_obj(";0")
        last_sent = now

    clock.tick(50)
