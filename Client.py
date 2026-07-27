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

fenetre = pygame.display.set_mode((1000, 900))
pygame.display.set_caption("Sorcer 2")


running = True

p1, p2, p3, p4 = Sorcer(spells), Sorcer(spells), Sorcer(spells), Sorcer(spells)
cible = 2
msg = ""
spell_description = ""
space_pressed = False

def get_effect_labels(player):
    labels = []
    if player.time_invincibilite > 0:
        labels.append(f"Invinc:{player.time_invincibilite}")
    if player.time_aveuglement > 0:
        labels.append(f"Blind:{player.time_aveuglement}")
    if player.time_silence > 0:
        labels.append(f"Silence:{player.time_silence}")
    if player.time_deviation > 0:
        labels.append(f"Deviation:{player.time_deviation}")
    if player.time_treve > 0:
        labels.append(f"Truce:{player.time_treve}")
    if player.time_clone > 0:
        labels.append(f"Clone:{player.time_clone}")
    if player.time_regeneration > 0:
        labels.append(f"Regen:{player.time_regeneration}")
    if player.time_poison > 0:
        labels.append(f"Poison:{player.time_poison}")
    if player.time_death_penalty > 0:
        labels.append(f"Death:{player.time_death_penalty}")
    if player.time_canalisation > 0:
        labels.append(f"Channel:{player.time_canalisation}")
    if player.time_inversion > 0:
        labels.append(f"Invert:{player.time_inversion}")
    if player.time_acceleration > 0:
        labels.append(f"Haste:{player.time_acceleration}")
    if player.time_slow > 0:
        labels.append(f"Slow:{player.time_slow}")
    if player.time_marque > 0:
        labels.append(f"Mark:{player.time_marque}")
    if player.time_lag_kick > 0:
        labels.append(f"LagKick:{player.time_lag_kick}")
    if player.time_renvoi > 0:
        labels.append(f"Counter:{player.time_renvoi}")
    if player.shield > 0:
        labels.append(f"Shield:{player.shield}")
    if player.time_reanimation > 0:
        labels.append(f"Reanimate:{player.time_reanimation}")
    if player.interdit is not None:
        labels.append("Blocked")
    if player.linked:
        labels.append("Linked")
    return labels if labels else ["No effect"]

clock = pygame.time.Clock()
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            try:
                base = None
                if event.key == K_SPACE:
                    space_pressed = True
                elif event.key == K_a:
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
                    spell_index = base + 26 if maj else base
                    if space_pressed:
                        if 0 <= spell_index < len(p1.s):
                            spell_description = p1.s[spell_index].description
                        else:
                            spell_description = ""
                    else:
                        msg = spell_index
                        spell_description = ""
            except IndexError:
                print(event.key)
        elif event.type == pygame.KEYUP:
            if event.key == K_SPACE:
                space_pressed = False


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
        fenetre.blit(text_surface, (80, 0))
        if p1.cible is p1:
            pygame.draw.line(fenetre, (0, 0, 255), (80,10), (0, 10), 2)
        if p1.cible is p2:
            pygame.draw.line(fenetre, (0, 0, 255), (80,10), (250, 10), 2)
        if p1.cible is p3:
            pygame.draw.line(fenetre, (0, 0, 255), (80,10), (500, 10), 2)
        if p1.cible is p4:
            pygame.draw.line(fenetre, (0, 0, 255), (80,10), (750, 10), 2)
    if p2.spell is not None:
        text_surface = my_font.render(str(f"{p2.spell.n}"), False, (255, 255, 255))
        fenetre.blit(text_surface, (330, 0))
        if p2.cible is p1:
            pygame.draw.line(fenetre, (0, 0, 255), (330,10), (0, 10), 2)
        if p2.cible is p2:
            pygame.draw.line(fenetre, (0, 0, 255), (330,10), (250, 10), 2)
        if p2.cible is p3:
            pygame.draw.line(fenetre, (0, 0, 255), (330,10), (500, 10), 2)
        if p2.cible is p4:
            pygame.draw.line(fenetre, (0, 0, 255), (330,10), (750, 10), 2)
    if p3.spell is not None:
        text_surface = my_font.render(str(f"{p3.spell.n}"), False, (255, 255, 255))
        fenetre.blit(text_surface, (580, 0))
        if p3.cible is p1:
            pygame.draw.line(fenetre, (255, 0, 0), (580,10), (0, 10), 2)
        if p3.cible is p2:
            pygame.draw.line(fenetre, (255, 0, 0), (580,10), (250, 10), 2)
        if p3.cible is p3:
            pygame.draw.line(fenetre, (255, 0, 0), (580,10), (500, 10), 2)
        if p3.cible is p4:
            pygame.draw.line(fenetre, (255, 0, 0), (580,10), (750, 10), 2)
    if p4.spell is not None:
        text_surface = my_font.render(str(f"{p4.spell.n}"), False, (255, 255, 255))
        fenetre.blit(text_surface, (830, 0))
        if p4.cible is p1:
            pygame.draw.line(fenetre, (255, 0, 0), (830,10), (0, 10), 2)
        if p4.cible is p2:
            pygame.draw.line(fenetre, (255, 0, 0), (830,10), (250, 10), 2)
        if p4.cible is p3:
            pygame.draw.line(fenetre, (255, 0, 0), (830,10), (500, 10), 2)
        if p4.cible is p4:
            pygame.draw.line(fenetre, (255, 0, 0), (830,10), (750, 10), 2)

    for i, player in enumerate([p1, p2, p3, p4]):
        base_x = i * 250
        labels = get_effect_labels(player)
        for j, label in enumerate(labels):
            text_surface = my_font.render(label, False, (255, 255, 255))
            fenetre.blit(text_surface, (base_x, 18 + j * 18))

    if spell_description:
        text_surface = my_font.render(f"Description : {spell_description}", False, (255, 255, 255))
        fenetre.blit(text_surface, (20, 760))

    espace = 30
    azerty = "azertyuiopqsdfghjklmwxcvbn"
    colonne2_x = 500  # colonne des sorts accessibles via Maj + lettre (indices 26 à 51)

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
