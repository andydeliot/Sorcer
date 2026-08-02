from Gameplay import *
import socket
import pickle
import struct
import threading
import pygame
from pygame import *
pygame.init()
import math

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
font_name = pygame.font.match_font('Segoe UI')
if font_name is None:
    font_name = pygame.font.match_font('Arial')
if font_name is None:
    font_name = pygame.font.match_font('DejaVu Sans')
my_font = pygame.font.Font(font_name, 20)
small_font = pygame.font.Font(font_name, 16)
header_font = pygame.font.Font(font_name, 24)
from random import randint

fenetre = pygame.display.set_mode((1800, 900))
pygame.display.set_caption("Sorcer 2")


running = True

p1, p2, p3, p4 = Sorcer(spells), Sorcer(spells), Sorcer(spells), Sorcer(spells)
cible = 2
msg = ""
spell_description = ""
space_pressed = False
selected_spell_index = None

def get_effect_labels(player):
    labels = []
    if player.interdit is not None:
        blocked_name = getattr(player.interdit, "n", "Unknown")
        labels.append(f"Blocked:{blocked_name}")
    if player.linked:
        # A player can have multiple links; show all remaining timers.
        link_timers = sorted(
            [int(link[0]) for link in player.linked if isinstance(link, list) and len(link) >= 1],
            reverse=True,
        )
        if link_timers:
            labels.append("Link:" + "/".join(str(t) for t in link_timers))
        else:
            labels.append("Link")
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
    if player.time_puissance > 0:
        labels.append(f"Puissance:{player.time_puissance}")
    if player.time_renvoi > 0:
        labels.append(f"Counter:{player.time_renvoi}")
    if player.shield > 0:
        labels.append(f"Shield:{player.shield}")
    if player.time_reanimation > 0:
        labels.append(f"Reanimate:{player.time_reanimation}")
    return labels if labels else ["No effect"]

def draw_wrapped_text(surface, text, font, color, x, y, max_width):
    words = text.split()
    lines = []
    current = ""
    for word in words:
        candidate = f"{current} {word}" if current else word
        if font.size(candidate)[0] <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)

    for index, line in enumerate(lines):
        line_surface = font.render(line, False, color)
        surface.blit(line_surface, (x, y + index * 24))

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
                    if selected_spell_index is not None and 0 <= selected_spell_index < len(p1.s):
                        spell_description = p1.s[selected_spell_index].description
                    else:
                        spell_description = ""
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
                    selected_spell_index = spell_index
                    msg = spell_index
                    if 0 <= spell_index < len(p1.s):
                        spell_description = get_spell_preview_text(p1.s[spell_index])
                    else:
                        spell_description = ""
            except IndexError:
                print(event.key)
        elif event.type == pygame.KEYUP:
            if event.key == K_SPACE:
                space_pressed = False
                spell_description = ""


    fenetre.fill((0,0,0))

    players = [p1, p2, p3, p4]
    names = ["You", "Your ally", "First enemy", "Second enemy"]
    panel_width = 380
    panel_height = 220
    panel_margin = 18
    panel_y = 20
    spells_panel_width = 800
    spells_panel_x = 20

    player_centers = []
    for i, player in enumerate(players):
        if i < 2:
            x = spells_panel_x + spells_panel_width + 120
            y = panel_y + i * (panel_height + panel_margin)
        else:
            x = spells_panel_x + spells_panel_width + 120 + panel_width + panel_margin
            y = panel_y + (i - 2) * (panel_height + panel_margin)
        is_target = i == cible
        border_color = (0, 180, 255) if is_target else (120, 120, 120)
        pygame.draw.rect(fenetre, (30, 30, 30), (x, y, panel_width, panel_height))
        pygame.draw.rect(fenetre, border_color, (x, y, panel_width, panel_height), 3)

        title_surface = header_font.render(names[i], False, (255, 255, 255))
        fenetre.blit(title_surface, (x + 10, y + 10))

        hp_text = f"PV: {player.pv}/{player.pv_max}"
        hp_surface = my_font.render(hp_text, False, (255, 255, 255))
        fenetre.blit(hp_surface, (x + 10, y + 45))

        hp_ratio = max(0, min(1, player.pv / player.pv_max)) if player.pv_max > 0 else 0
        bar_width = 180
        bar_height = 12
        bar_x = x + 10
        bar_y = y + 75
        pygame.draw.rect(fenetre, (80, 80, 80), (bar_x, bar_y, bar_width, bar_height))
        pygame.draw.rect(fenetre, (0, 220, 0), (bar_x, bar_y, int(bar_width * hp_ratio), bar_height))

        effect_labels = get_effect_labels(player)
        effect_y = y + 100
        for j, label in enumerate(effect_labels[:5]):
            effect_surface = small_font.render(label, False, (255, 255, 255))
            fenetre.blit(effect_surface, (x + 10, effect_y + j * 18))

        # stocke le centre du panneau pour dessiner les flèches ensuite
        center_x = x + panel_width // 2
        center_y = y + panel_height // 2
        player_centers.append((center_x, center_y))

        if player.spell is not None:
            spell_text = f"Spell: {player.spell.n}"
            if player.spell.tc + player.spell.d + player.spell.tl > 0:
                time_end = player.spell.tc + player.spell.d + player.spell.tl - player.spell.time_charge - player.spell.duree - player.spell.time_lag
                spell_text += f" ({time_end})"
            spell_surface = small_font.render(spell_text, False, (255, 220, 120))
            fenetre.blit(spell_surface, (x + 10, y + 190))
        else:
            no_spell_surface = small_font.render("No spell in progress", False, (180, 180, 180))
            fenetre.blit(no_spell_surface, (x + 10, y + 190))

    # Dessiner les flèches colorées indiquant la cible de chaque joueur
    colors = [(255, 100, 100), (100, 255, 100), (100, 100, 255), (255, 255, 100)]
    for i, player in enumerate(players):
        if player.pv <= 0:
            continue
        try:
            src = player_centers[i]
        except IndexError:
            continue
        # trouver l'index de la cible dans la liste players
        try:
            tgt_index = players.index(player.cible)
        except ValueError:
            continue
        tgt = player_centers[tgt_index]
        color = colors[i % len(colors)]
        # dessiner la ligne principale
        pygame.draw.line(fenetre, color, src, tgt, 4)
        # dessiner la pointe de la flèche
        dx = tgt[0] - src[0]
        dy = tgt[1] - src[1]
        dist = math.hypot(dx, dy)
        if dist > 0:
            ux = dx / dist
            uy = dy / dist
            # taille de la flèche
            ah = 12
            aw = 8
            # point d'arrivée
            ax = tgt[0]
            ay = tgt[1]
            # deux points latéraux pour former un triangle
            left = (ax - ux * ah - uy * aw, ay - uy * ah + ux * aw)
            right = (ax - ux * ah + uy * aw, ay - uy * ah - ux * aw)
            pygame.draw.polygon(fenetre, color, [ (ax, ay), left, right ])

    if spell_description:
        draw_wrapped_text(
            fenetre,
            f"{spell_description}",
            my_font,
            (255, 255, 255),
            1000,
            500,
            600,
        )

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
