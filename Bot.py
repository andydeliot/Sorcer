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

from random import choice

running = True

p1, p2, p3, p4 = Sorcer(spells), Sorcer(spells), Sorcer(spells), Sorcer(spells)

# --------------------------------------------------------------------------
# Rappel : dans la vue reçue du serveur, p1 = soi-même, p2 = allié, p3/p4 =
# ennemis. cible=0 -> p1 (soi), 1 -> p2 (allié), 2 -> p3 (ennemi), 3 -> p4
# (ennemi). C'est exactement ce que loop() attend côté serveur.
#
# Chaque sort est classé selon qui il est censé avantager, pour que la cible
# choisie corresponde à son effet réel plutôt qu'à un tirage aveugle.
# --------------------------------------------------------------------------
SELF = "self"                     # l'effet ignore c, ou c'est un buff purement personnel.
SUPPORT = "support"                # bénéfique -> vise soi ou l'allié, selon qui en a le plus besoin.
ENEMY = "enemy"                    # offensif -> vise l'ennemi vivant le plus faible (achever).
ENEMY_HIGH = "enemy_high"          # vise l'ennemi vivant le plus fort (comeback / neutralisation).
ENEMY_CASTING = "enemy_casting"    # inutile si aucun ennemi n'a de sort en cours.
CLEANSE = "cleanse"                # dynamique : purge un allié affaibli ou un ennemi buffé.
EXTEND = "extend"                  # dynamique : prolonge un debuff ennemi ou un buff allié.
MIRROR = "mirror"                  # rejoue le dernier sort -> reprend sa catégorie.

CATEGORIE = {
    Boule_feu: ENEMY, Laser: ENEMY, Poison: ENEMY, VolDeVie: ENEMY,
    Soin: SUPPORT, Vitesse: SUPPORT, Interdiction: ENEMY_CASTING,
    LienSpirituel: SUPPORT, Silence: ENEMY, Renvoi: SUPPORT,
    Exodia: ENEMY, Multiplicateur: ENEMY, TicTac: ENEMY, Balance: ENEMY_HIGH,
    Renforcement: SUPPORT, Specialisation: SELF, Invincibilite: SUPPORT,
    Treve: SELF, Clone: SUPPORT, Retour: SUPPORT, Flash: ENEMY, Canon: ENEMY,
    Coagulation: SUPPORT, Regeneration: SUPPORT, Annulation: ENEMY_CASTING,
    VolDeSort: ENEMY_CASTING, Earthquake: ENEMY,
    Acceleration: SUPPORT, Ralentissement: ENEMY, VolDeTemps: ENEMY,
    Reanimation: SUPPORT, LagKick: ENEMY, Deviation: ENEMY_HIGH, Baffe: ENEMY,
    Bouclier: SUPPORT, ConcentrationMagique: ENEMY, PeineDeMort: ENEMY,
    Esprit: ENEMY, Difference: ENEMY, RayonDeSoleil: ENEMY,
    ConcentrationSorts: ENEMY, Repetition: MIRROR, Impatience: ENEMY,
    Nettoyage: CLEANSE, Inversion: ENEMY, ProjectileMagique: ENEMY,
    Canalisation: SUPPORT, Aveuglement: ENEMY_HIGH, Troc: ENEMY, Tempo: SUPPORT,
    Prolongation: EXTEND, Marque: ENEMY,
}

# Compteurs de statut considérés comme un désavantage (bon à purger sur soi/allié,
# bon à prolonger sur un ennemi) ou un avantage (inverse) pour Nettoyage/Prolongation.
DEBUFFS = [
    "time_poison", "time_silence", "time_slow", "time_marque",
    "time_death_penalty", "time_aveuglement", "time_lag_kick",
    "time_deviation", "time_inversion",
]
BUFFS = [
    "time_invincibilite", "time_treve", "time_clone", "time_regeneration",
    "time_acceleration", "time_reanimation", "time_shield", "time_canalisation",
]


def ennemis_vivants():
    return [(idx, pl) for idx, pl in [(2, p3), (3, p4)] if pl.pv > 0]


def cible_ennemi_faible():
    """ Ennemi vivant avec le moins de PV (achever), sinon un repli arbitraire. """
    vivants = ennemis_vivants()
    return min(vivants, key=lambda t: t[1].pv)[0] if vivants else 2


def cible_ennemi_fort():
    """ Ennemi vivant avec le plus de PV. """
    vivants = ennemis_vivants()
    return max(vivants, key=lambda t: t[1].pv)[0] if vivants else 2


def cible_ennemi_en_train_de_lancer():
    """ Un ennemi actuellement en train de lancer un sort, sinon None (sort inutile ce tour-ci). """
    for idx, pl in ennemis_vivants():
        if pl.spell is not None:
            return idx
    return None


def cible_soutien():
    """ Entre soi et l'allié vivant, celui dont les PV proportionnels sont les plus bas. """
    if p2.pv <= 0:
        return 0
    if p1.pv <= 0:
        return 1
    ratio_self = p1.pv / p1.pv_max
    ratio_ally = p2.pv / p2.pv_max
    return 0 if ratio_self <= ratio_ally else 1


def a_un_debuff(joueur):
    return any(getattr(joueur, attr, 0) > 0 for attr in DEBUFFS)


def a_un_buff(joueur):
    return any(getattr(joueur, attr, 0) > 0 for attr in BUFFS)


def cible_purge():
    """ Nettoyage : soigne d'abord un allié gêné, sinon dépouille un ennemi de ses buffs. """
    if a_un_debuff(p1):
        return 0
    if p2.pv > 0 and a_un_debuff(p2):
        return 1
    for idx, pl in ennemis_vivants():
        if a_un_buff(pl):
            return idx
    return None


def cible_extension():
    """ Prolongation : aggrave un debuff ennemi actif, sinon prolonge un buff allié actif. """
    for idx, pl in ennemis_vivants():
        if a_un_debuff(pl):
            return idx
    if a_un_buff(p1):
        return 0
    if p2.pv > 0 and a_un_buff(p2):
        return 1
    return None


def choisir_cible(categorie):
    if categorie == SELF:
        return 0
    if categorie == SUPPORT:
        return cible_soutien()
    if categorie == ENEMY:
        return cible_ennemi_faible()
    if categorie == ENEMY_HIGH:
        return cible_ennemi_fort()
    if categorie == ENEMY_CASTING:
        return cible_ennemi_en_train_de_lancer()
    if categorie == CLEANSE:
        return cible_purge()
    if categorie == EXTEND:
        return cible_extension()
    if categorie == MIRROR:
        if p1.last_spell is not None:
            cat = CATEGORIE.get(type(p1.last_spell), ENEMY)
            if cat == MIRROR:
                cat = ENEMY
            return choisir_cible(cat)
        return None
    return cible_ennemi_faible()


clock = pygame.time.Clock()
while running:
    if p1.pv > 0 and p1.spell is None and p1.time_silence == 0:
        options = []
        for i, s in enumerate(p1.s):
            if s.time_cooldown > 0 or s is p1.interdit:
                continue
            cible = choisir_cible(CATEGORIE.get(type(s), ENEMY))
            if cible is not None:
                options.append((i, cible))

        if options:
            # En urgence, priorité au soutien si soi ou l'allié est en dessous de 40% de vie.
            urgence = [
                (i, c) for i, c in options
                if CATEGORIE.get(type(p1.s[i])) == SUPPORT and (
                    (c == 0 and p1.pv < p1.pv_max * 0.4) or
                    (c == 1 and p2.pv > 0 and p2.pv < p2.pv_max * 0.4)
                )
            ]
            n, cible = choice(urgence) if urgence else choice(options)
            send_obj(str(n) + ";" + str(cible))

    clock.tick(50)
