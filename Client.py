from Gameplay import *
import socket
import pickle
import struct
import threading
import pygame
from pygame import *
pygame.init()

HOST = "127.0.0.1" #input("Adresse ip : ")
PORT = 5000

client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client.connect((HOST, PORT))

# -------------------------
# send
# -------------------------
def send_obj(obj):
    data = pickle.dumps(obj)
    size = struct.pack("!I", len(data))
    client.sendto(size + data, (HOST, PORT))

# -------------------------
# receive
# -------------------------
def recv_loop():
    global p1, p2, p3, p4
    while True:
        data, _ = client.recvfrom(65536)
        size = struct.unpack("!I", data[:4])[0]
        p1, p2, p3, p4 = pickle.loads(data[4:4+size])

threading.Thread(target=recv_loop, daemon=True).start()

# -------------------------
# send loop
# -------------------------

pygame.font.init()
my_font = pygame.font.SysFont('Comic Sans MS', 20)
from random import randint

fenetre = pygame.display.set_mode((1000, 875))
pygame.display.set_caption("Sorcer 2")


running = True

p1, p2, p3, p4 = Sorcer(spells), Sorcer(spells), Sorcer(spells), Sorcer(spells)
cible = 2
msg = ""

clock = pygame.time.Clock()
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            try:
                base = None
                if event.key == K_a:
                    base = 0
                elif event.key == K_z:
                    base = 1
                elif event.key == K_e:
                    base = 2
                elif event.key == K_r:
                    base = 3
                elif event.key == K_t:
                    base = 4
                elif event.key == K_y:
                    base = 5
                elif event.key == K_u:
                    base = 6
                elif event.key == K_i:
                    base = 7
                elif event.key == K_o:
                    base = 8
                elif event.key == K_p:
                    base = 9
                elif event.key == K_q:
                    base = 10
                elif event.key == K_s:
                    base = 11
                elif event.key == K_d:
                    base = 12
                elif event.key == K_f:
                    base = 13
                elif event.key == K_g:
                    base = 14
                elif event.key == K_h:
                    base = 15
                elif event.key == K_j:
                    base = 16
                elif event.key == K_k:
                    base = 17
                elif event.key == K_l:
                    base = 18
                elif event.key == K_m:
                    base = 19
                elif event.key == K_w:
                    base = 20
                elif event.key == K_x:
                    base = 21
                elif event.key == K_c:
                    base = 22
                elif event.key == K_v:
                    base = 23
                elif event.key == K_b:
                    base = 24
                elif event.key == K_n:
                    base = 25
                elif event.key == K_TAB:
                    cible += 1
                    if cible >= 4:
                        cible = 0
                elif event.key == K_RETURN:
                    send_obj(str(msg) + ";" + str(cible))

                if base is not None:
                    # Maj + lettre -> les 26 sorts suivants (indices 26 à 51).
                    maj = pygame.key.get_mods() & pygame.KMOD_SHIFT
                    msg = base + 26 if maj else base
            except IndexError:
                print(event.key)


    fenetre.fill((0,0,0))
    l, h = 36, 30
    color = (0, 0, 255)
    if cible == 0:
        pygame.draw.rect(fenetre, color, (0, 0, l, h))
    if cible == 1:
        pygame.draw.rect(fenetre, color, (250, 0, l, h))
    if cible == 2:
        pygame.draw.rect(fenetre, color, (500, 0, l, h))
    if cible == 3:
        pygame.draw.rect(fenetre, color, (750, 0, l, h))

    text_surface = my_font.render(str(f"{p1.pv}"), False, (255, 255, 255))
    fenetre.blit(text_surface, (0,0))
    text_surface = my_font.render(str(f"{p2.pv}"), False, (255, 255, 255))
    fenetre.blit(text_surface, (250,0))
    text_surface = my_font.render(str(f"{p3.pv}"), False, (255, 255, 255))
    fenetre.blit(text_surface, (500,0))
    text_surface = my_font.render(str(f"{p4.pv}"), False, (255, 255, 255))
    fenetre.blit(text_surface, (750,0))
    if p1.spell is not None:
        time_end = p1.spell.tc + p1.spell.d + p1.spell.tl - p1.spell.time_charge - p1.spell.duree - p1.spell.time_lag
        text_surface = my_font.render(str(f"{p1.spell.n} end in {time_end}"), False, (255, 255, 255))
        fenetre.blit(text_surface, (0,25))
        if p1.cible is p1:
            pygame.draw.line(fenetre, (0, 0, 255), (0,25), (0, 0), 2)
        if p1.cible is p2:
            pygame.draw.line(fenetre, (0, 0, 255), (0,25), (250, 0), 2)
        if p1.cible is p3:
            pygame.draw.line(fenetre, (0, 0, 255), (0,25), (500, 0), 2)
        if p1.cible is p4:
            pygame.draw.line(fenetre, (0, 0, 255), (0,25), (750, 0), 2)
    if p2.spell is not None:
        text_surface = my_font.render(str(f"{p2.spell.n}"), False, (255, 255, 255))
        fenetre.blit(text_surface, (250,25))
        if p2.cible is p1:
            pygame.draw.line(fenetre, (0, 0, 255), (250,25), (0, 0), 2)
        if p2.cible is p2:
            pygame.draw.line(fenetre, (0, 0, 255), (250,25), (250, 0), 2)
        if p2.cible is p3:
            pygame.draw.line(fenetre, (0, 0, 255), (250,25), (500, 0), 2)
        if p2.cible is p4:
            pygame.draw.line(fenetre, (0, 0, 255), (250,25), (750, 0), 2)
    if p3.spell is not None:
        text_surface = my_font.render(str(f"{p3.spell.n}"), False, (255, 255, 255))
        fenetre.blit(text_surface, (500,25))
        if p3.cible is p1:
            pygame.draw.line(fenetre, (255, 0, 0), (500,25), (0, 0), 2)
        if p3.cible is p2:
            pygame.draw.line(fenetre, (255, 0, 0), (500,25), (250, 0), 2)
        if p3.cible is p3:
            pygame.draw.line(fenetre, (255, 0, 0), (500,25), (500, 0), 2)
        if p3.cible is p4:
            pygame.draw.line(fenetre, (255, 0, 0), (500,25), (750, 0), 2)
    if p4.spell is not None:
        text_surface = my_font.render(str(f"{p4.spell.n}"), False, (255, 255, 255))
        fenetre.blit(text_surface, (750,25))
        if p4.cible is p1:
            pygame.draw.line(fenetre, (255, 0, 0), (750,25), (0, 0), 2)
        if p4.cible is p2:
            pygame.draw.line(fenetre, (255, 0, 0), (750,25), (250, 0), 2)
        if p4.cible is p3:
            pygame.draw.line(fenetre, (255, 0, 0), (750,25), (500, 0), 2)
        if p4.cible is p4:
            pygame.draw.line(fenetre, (255, 0, 0), (750,25), (750, 0), 2)

    v = "0 effect"
    if p1.time_poison > 0:
        v = f"{p1.time_poison} Poison"
    elif p1.time_silence > 0:
        v = f"{p1.time_silence} Silence"
    elif p1.time_invincibilite > 0:
        v = f"{p1.time_invincibilite} Invincibility"
    elif p1.time_treve > 0:
        v = f"{p1.time_treve} Truce"
    elif p1.time_clone > 0:
        v = f"{p1.time_clone} Clone"
    elif p1.time_regeneration > 0:
        v = f"{p1.time_regeneration} Regeneration"

    text_surface = my_font.render(str(f"{v}"), False, (255, 255, 255))
    fenetre.blit(text_surface, (100,0))


    espace = 30
    azerty = "azertyuiopqsdfghjklmwxcvbn"
    colonne2_x = 500  # colonne des sorts accessibles via Maj + lettre (indices 26 à 51)

    x, y = 0, 25
    couleur = (255, 255, 255)
    text_surface = my_font.render(str(f"(Key) Name :"), False, couleur)
    fenetre.blit(text_surface, (x,y+25))
    text_surface = my_font.render(str(f"Cooldown"), False, couleur);
    fenetre.blit(text_surface, (x+150, y+25))
    text_surface = my_font.render(str(f"Time charge; Duration;"), False, couleur)
    fenetre.blit(text_surface, (x+250, y+25))
    text_surface = my_font.render(str(f"(Maj+Key) Name :"), False, couleur)
    fenetre.blit(text_surface, (colonne2_x,y+25))
    text_surface = my_font.render(str(f"Cooldown"), False, couleur);
    fenetre.blit(text_surface, (colonne2_x+150, y+25))
    text_surface = my_font.render(str(f"Time charge; Duration;"), False, couleur)
    fenetre.blit(text_surface, (colonne2_x+250, y+25))

    y0 = espace*2
    for i, s in enumerate(p1.s):
        lettre = azerty[i % 26]
        label = lettre if i < 26 else f"Maj+{lettre}"
        colonne_x = 0 if i < 26 else colonne2_x
        ligne_y = y0 + (i % 26) * espace

        c = ((s.c-s.time_cooldown) / s.c)*125+50
        couleur = (c, c, c)
        if s is p1.interdit:
            couleur = (255, 0, 0)
        elif s is p1.spell_specialisation:
            couleur = (c, c, 255)
        elif s.time_cooldown == 0:
            couleur = (0, 255, 0)
        text_surface = my_font.render(str(f"({label}) {s.n} :"), False, couleur)
        fenetre.blit(text_surface, (colonne_x,ligne_y+25))
        text_surface = my_font.render(str(f"{s.time_cooldown}"), False, couleur);
        fenetre.blit(text_surface, (colonne_x+180, ligne_y+25))
        text_surface = my_font.render(str(f"{(s.tc - s.time_charge)}; {(s.d - s.duree)};"), False, couleur)
        fenetre.blit(text_surface, (colonne_x+250, ligne_y+25))
    
    pygame.display.flip()

    clock.tick(50)

input()
