import copy

global cooldown_base
cooldown_base = 2000


def get_ally(player, p):
    """ Coéquipier de player dans p, en supposant des paires (p[0],p[1]), (p[2],p[3])... comme team_a/team_b. """
    if player not in p:
        return None
    i = p.index(player)
    j = i - 1 if i % 2 == 1 else i + 1
    return p[j] if 0 <= j < len(p) else None


class Spell:
    def __init__(self, n, c=cooldown_base, tc=200, d=1, tl=100):
        self.n = n  # Nom
        self.c = c  # Cooldown
        self.tc = tc  # Temps de charge
        self.d = d  # Durée
        self.tl = tl  # Temps de lag

        self.time_cooldown = 0
        self.time_charge = 0
        self.started = False
        self.duree = 0
        self.ended = False
        self.time_lag = 0

    def init(self):
        self.time_charge = 0
        self.started = False
        self.duree = 0
        self.ended = False
        self.time_lag = 0
    
    def start(self, l, c, p):
        """ Définir ici que faire au lancement du sort. """
        if not self.started and self.time_cooldown == 0:
            l.busy = True
            charge_gain = 1
            if l.time_acceleration > 0:
                charge_gain = 2
            elif l.time_slow > 0:
                charge_gain = 0.5
            self.time_charge += charge_gain
        if self.time_charge >= self.tc:
            if not self.started:
                self.started = True

    def action(self, l, c, p):
        """ Définir ici que faire durant la durée du sort. """
        if self.started and not self.ended:
            self.duree += 1
            if self.duree <= self.d:
                self.effet(l, c, p)
            else:
                self.ended = True

    def effet(self, l, c, p):
        """ Définir ici l'effet du sort lorsque l'action est prête. """
        pass

    def end(self, l, c, p):
        """ Définir ici que faire à la fin du sort. """
        if self.ended:
            self.time_lag += 2 if l.time_acceleration > 0 else 1
            if self.time_lag >= self.tl:
                self.init()
                self.time_cooldown = self.c * 2 if l.time_slow > 0 else self.c
                if l.spell_specialisation is self:
                    self.time_cooldown = int(self.time_cooldown/3)
                l.spell = None
                l.busy = False
                l.last_spell = self

    def passive(self, l, c, p):
        """ Cooldown. """
        if self.time_cooldown > 0:
            self.time_cooldown -= 1
            

class Boule_feu(Spell):
    def __init__(self):
        Spell.__init__(self, "Fireball", tc=100)

    def effet(self, l, c, p):
        l.dammage(25)
        c.dammage(125)

class Laser(Spell):
    def __init__(self):
        Spell.__init__(self, "Laser", d=200)

    def effet(self, l, c, p):
        c.dammage(1)

class Poison(Spell):
    def __init__(self):
        Spell.__init__(self, "Poison")
        self.duree_poison = 1000

    def effet(self, l, c, p):
        c.time_poison = self.duree_poison

    def passive(self, l, c, p):
        if self.time_cooldown > 0:
            self.time_cooldown -= 1
        if c.time_poison > 0:
            c.time_poison -= 1
        if c.time_poison % 100 == 1:
            c.dammage(25)

class VolDeVie(Spell):
    def __init__(self):
        Spell.__init__(self, "Life steal", d=50)

    def effet(self, l, c, p):
        c.dammage(1)
        l.heal(1)

class Soin(Spell):
    def __init__(self):
        Spell.__init__(self, "Heal")

    def effet(self, l, c, p):
        c.heal(100)
        c.time_poison = 0

class Vitesse(Spell):
    def __init__(self):
        Spell.__init__(self, "Speed")

    def effet(self, l, c, p):
        for s in c.s:
            s.time_cooldown = int(s.time_cooldown / 2)

class Interdiction(Spell):
    def __init__(self):
        Spell.__init__(self, "Interdiction", tc=0)
        
    def effet(self, l, c, p):
        if c.spell is not None:
            c.interdit = c.spell

class LienSpirituel(Spell):
    def __init__(self):
        Spell.__init__(self, "Spiritual link")

    def effet(self, l, c, p):
        l.linked.append([800, l, c])
        c.linked.append([800, l, c])

    def passive(self, l, c, p):
        for link in l.linked:
            if link[1] == l and link[2] == c:
                if link[0] > 0:
                    link[0] -= 1
                else:
                    l.linked.remove(link)
                    break
        for link in c.linked:
            if link[1] == l and link[2] == c:
                if link[0] > 0:
                    link[0] -= 1
                else:
                    c.linked.remove(link)
                    break

class Silence(Spell):
    def __init__(self):
        Spell.__init__(self, "Silence")

    def effet(self, l, c, p):
        c.time_silence = 400

    def passive(self, l, c, p):
        if self.time_cooldown > 0:
            self.time_cooldown -= 1
        if c.time_silence > 0:
            c.time_silence -= 1

class Renvoi(Spell):
    def __init__(self):
        Spell.__init__(self, "Counter", tc=50, tl=200)

    def effet(self, l, c, p):
        c.time_renvoi = 200

    def passive(self, l, c, p):
        if self.time_cooldown > 0:
            self.time_cooldown -= 1
        if c.time_renvoi > 0:
            c.time_renvoi -= 1

class Exodia(Spell):
    def __init__(self):
        Spell.__init__(self, "Exodia", c=4000)

    def effet(self, l, c, p):
        l.nbr_exodia += 1
        if l.nbr_exodia >= 5:
            for player in p:
                if player is not self:
                    player.pv = 0
            l.nbr_exodia = 0

class Multiplicateur(Spell):
    def __init__(self):
        Spell.__init__(self, "Multiplier")

    def effet(self, l, c, p):
        c.dammage(40*l.nbr_multiplicateur)
        l.nbr_multiplicateur += 1

class TicTac(Spell):
    def __init__(self):
        Spell.__init__(self, "TicTac")

    def effet(self, l, c, p):
        if l.tictac == "tic":
            c.dammage(int(c.pv*0.2))
        else:
            c.dammage(int((c.pv_max-c.pv)*0.25))

class Balance(Spell):
    def __init__(self):
        Spell.__init__(self, "Balance")

    def effet(self, l, c, p):
        l.dammage((l.pv - c.pv)/3)
        c.dammage((c.pv - l.pv)/3)

class Renforcement(Spell):
    def __init__(self):
        Spell.__init__(self, "Reinforcement")
    def effet(self, l, c, p):
        c.pv_max += 50
        c.heal(25)

class Specialisation(Spell):
    def __init__(self):
        Spell.__init__(self, "Specialisation")

    def effet(self, l, c, p):
        if l.last_spell is not None:
            l.last_spell.time_cooldown = int(l.last_spell.time_cooldown/3)
            l.spell_specialisation = l.last_spell

class Invincibilite(Spell):
    def __init__(self):
        Spell.__init__(self, "Invincibility", tc=0, d=250)

    def effet(self, l, c, p):
        c.time_invincibilite = 250

    def passive(self, l, c, p):
        if self.time_cooldown > 0:
            self.time_cooldown -= 1
        if c.time_invincibilite > 0:
            c.time_invincibilite -= 1

class Treve(Spell):
    def __init__(self):
        Spell.__init__(self, "Truce", tc=10)

    def effet(self, l, c, p):
        l.time_treve = 300

    def passive(self, l, c, p):
        if self.time_cooldown > 0:
            self.time_cooldown -= 1
        if l.time_treve > 0:
            l.time_treve -= 1

class Clone(Spell):
    def __init__(self):
        Spell.__init__(self, "Clone")

    def effet(self, l, c, p):
        c.time_clone = 600

    def passive(self, l, c, p):
        if self.time_cooldown > 0:
            self.time_cooldown -= 1
        if c.time_clone > 0:
            c.time_clone -= 1

class Retour(Spell):
    def __init__(self):
        Spell.__init__(self, "Timeback", tc=0, d=300)

    def start(self, l, c, p):
        if not self.started and self.time_cooldown == 0:
            c.busy = True
            self.time_charge += 1
            c.vie_retour = c.pv
        if self.time_charge >= self.tc:
            if not self.started:
                self.started = True

    def action(self, l, c, p):
        if self.started:
            self.duree += 1
            if self.duree > self.d:
                self.ended = True
                c.pv = c.vie_retour

class Flash(Spell):
    def __init__(self):
        Spell.__init__(self, "Flash", tc=0, d=1)

    def effet(self, l, c, p):
        c.dammage(20)

class Canon(Spell):
    def __init__(self):
        Spell.__init__(self, "Cannon", tc=400, d=1)
    
    def effet(self, l, c, p):
        c.dammage(200)

class Coagulation(Spell):
    def __init__(self):
        Spell.__init__(self, "Coagulation", d=150)

    def effet(self, l, c, p):
        c.heal(1)

class Regeneration(Spell):
    def __init__(self):
        Spell.__init__(self, "Regeneration")
        self.duree_regeneration = 500

    def effet(self, l, c, p):
        c.time_regeneration = self.duree_regeneration

    def passive(self, l, c, p):
        if self.time_cooldown > 0:
            self.time_cooldown -= 1
        if c.time_regeneration > 0:
            c.time_regeneration -= 1
        if c.time_regeneration % 100 == 1:
            c.heal(20)

class Annulation(Spell):
    def __init__(self):
        Spell.__init__(self, "Cancelation", tc=50)

    def effet(self, l, c, p):
        if c.spell is not None:
            c.spell.time_cooldown = c.spell.c
            c.spell.started = True
            c.spell.ended = True

class VolDeSort(Spell):
    def __init__(self):
        Spell.__init__(self, "Spell steal", tc=0)

    def effet(self, l, c, p):
        if c.spell is not None:
            for i in range(len(c.s)):
                if c.s[i] is c.spell:
                    c.s[i] = self
            for i in range(len(l.s)):
                if l.s[i] is self:
                    l.s[i] = c.spell.__class__()
        c.spell = None
        c.busy = False

class Earthquake(Spell):
    def __init__(self):
        Spell.__init__(self, "Earthquake")

    def effet(self, l, c, p):
        for player in p:
            player.dammage(50)

class Acceleration(Spell):
    """ Accélère les lancers (x2) et le lag (/2) du joueur ciblé ; annule Slow. """
    def __init__(self):
        Spell.__init__(self, "Speed up")
        self.duree_acceleration = 800

    def effet(self, l, c, p):
        c.time_acceleration = self.duree_acceleration
        c.time_slow = 0

    def passive(self, l, c, p):
        if self.time_cooldown > 0:
            self.time_cooldown -= 1
        if c.time_acceleration > 0:
            c.time_acceleration -= 1

class Ralentissement(Spell):
    """ Ralentit les lancers (/2) et augmente les cooldowns (x2) du joueur ciblé ; annule Acceleration. """
    def __init__(self):
        Spell.__init__(self, "Slow")
        self.duree_slow = 1000

    def effet(self, l, c, p):
        c.time_slow = self.duree_slow
        c.time_acceleration = 0

    def passive(self, l, c, p):
        if self.time_cooldown > 0:
            self.time_cooldown -= 1
        if c.time_slow > 0:
            c.time_slow -= 1

class VolDeTemps(Spell):
    """ Verrouille (plein cooldown) chaque sort actuellement disponible de la cible, et réduit d'autant le cooldown des sorts du lanceur. """
    def __init__(self):
        Spell.__init__(self, "Time steal")

    def effet(self, l, c, p):
        for spell_c in c.s:
            if spell_c.time_cooldown == 0:
                spell_c.time_cooldown = spell_c.c
                for spell_l in l.s:
                    spell_l.time_cooldown = max(0, spell_l.time_cooldown - 100)

class Reanimation(Spell):
    """ Si actif au moment où la cible devrait mourir, elle ressuscite avec pv_max/3 au lieu de mourir. """
    def __init__(self):
        Spell.__init__(self, "Reanimation")
        self.duree_reanimation = 600

    def effet(self, l, c, p):
        c.time_reanimation = self.duree_reanimation

    def passive(self, l, c, p):
        if self.time_cooldown > 0:
            self.time_cooldown -= 1
        if c.time_reanimation > 0:
            c.time_reanimation -= 1

class LagKick(Spell):
    """ Ne bloque pas le lanceur : les dégâts sont réglés en passif, 1000 ticks après le lancement. """
    def __init__(self):
        Spell.__init__(self, "Lag kick", tc=50)
        self.duree_lag_kick = 1000

    def effet(self, l, c, p):
        c.time_lag_kick = self.duree_lag_kick

    def passive(self, l, c, p):
        if self.time_cooldown > 0:
            self.time_cooldown -= 1
        if c.time_lag_kick > 0:
            c.time_lag_kick -= 1
            if c.time_lag_kick == 0:
                c.dammage(150)

class Deviation(Spell):
    """ Force la cible à lancer ses sorts sur le lanceur, tant que l'effet dure (voir loop()). """
    def __init__(self):
        Spell.__init__(self, "Deviation")
        self.duree_deviation = 600

    def effet(self, l, c, p):
        c.time_deviation = self.duree_deviation
        c.deviation_cible = l

    def passive(self, l, c, p):
        if self.time_cooldown > 0:
            self.time_cooldown -= 1
        if c.time_deviation > 0:
            c.time_deviation -= 1
            if c.time_deviation == 0:
                c.deviation_cible = None

class Baffe(Spell):
    def __init__(self):
        Spell.__init__(self, "Quick slap", c=int(cooldown_base/4), tc=20, tl=20)

    def effet(self, l, c, p):
        c.dammage(10)

class Bouclier(Spell):
    """ Absorbe jusqu'à 25 points de dégâts pendant sa durée, même partiellement consommé. """
    def __init__(self):
        Spell.__init__(self, "Shield")
        self.duree_shield = 500

    def effet(self, l, c, p):
        c.shield = 25
        c.time_shield = self.duree_shield

    def passive(self, l, c, p):
        if self.time_cooldown > 0:
            self.time_cooldown -= 1
        if c.time_shield > 0:
            c.time_shield -= 1
            if c.time_shield == 0:
                c.shield = 0

class ConcentrationMagique(Spell):
    """ Inflige 5 dégâts par sort de la cible actuellement disponible (hors cooldown). """
    def __init__(self):
        Spell.__init__(self, "Magic concentration")

    def effet(self, l, c, p):
        dispo = sum(1 for s in c.s if s.time_cooldown == 0)
        c.dammage(5 * dispo)

class PeineDeMort(Spell):
    """ Après un très long délai, tue la cible sauf si elle est invincible, si le sort a été relancé
    entre-temps (délai réinitialisé) ou si Nettoyage a purgé le passif (délai remis à 0). """
    def __init__(self):
        Spell.__init__(self, "Death penalty", tc=200)
        self.duree_death_penalty = 3000

    def effet(self, l, c, p):
        c.time_death_penalty = self.duree_death_penalty

    def passive(self, l, c, p):
        if self.time_cooldown > 0:
            self.time_cooldown -= 1
        if c.time_death_penalty > 0:
            c.time_death_penalty -= 1
            if c.time_death_penalty == 0 and c.time_invincibilite == 0:
                c.pv = 0

class Esprit(Spell):
    def __init__(self):
        Spell.__init__(self, "Spirit")

    def effet(self, l, c, p):
        morts = sum(1 for player in p if player.pv <= 0)
        c.dammage(200 * morts)

class Difference(Spell):
    """ Inflige la différence de points de vie entre la cible et son coéquipier. """
    def __init__(self):
        Spell.__init__(self, "Difference")

    def effet(self, l, c, p):
        ally = get_ally(c, p)
        if ally is not None:
            c.dammage(abs(c.pv - ally.pv))

class RayonDeSoleil(Spell):
    """ Premier lancer : charge (pas de dégâts). Lancer suivant : libère les dégâts. """
    def __init__(self):
        Spell.__init__(self, "Sun ray", tc=150)
        self.charge = False

    def effet(self, l, c, p):
        if not self.charge:
            self.charge = True
        else:
            c.dammage(300)
            self.charge = False

class ConcentrationSorts(Spell):
    """ Inflige 75 dégâts par sort actuellement en cours de lancement (start passé, pas encore terminé). """
    def __init__(self):
        Spell.__init__(self, "Magical concentration")

    def effet(self, l, c, p):
        en_cours = sum(1 for player in p if player.spell is not None and player.spell.started and not player.spell.ended)
        c.dammage(75 * en_cours)

class Repetition(Spell):
    """ Redéclenche l'effet du dernier sort du lanceur, sans se soucier de son cooldown. """
    def __init__(self):
        Spell.__init__(self, "Repeat")

    def effet(self, l, c, p):
        if l.last_spell is not None:
            l.last_spell.effet(l, c, p)

class Impatience(Spell):
    def __init__(self):
        Spell.__init__(self, "Impatience")

    def effet(self, l, c, p):
        total = sum(s.time_cooldown for s in c.s)
        c.dammage(int(total / 100))

class Nettoyage(Spell):
    """ Annule tous les effets passifs actuellement actifs sur la cible. """
    def __init__(self):
        Spell.__init__(self, "Clean", tc=50)

    def effet(self, l, c, p):
        c.time_poison = 0
        c.time_silence = 0
        c.time_renvoi = 0
        c.time_invincibilite = 0
        c.time_treve = 0
        c.time_clone = 0
        c.time_regeneration = 0
        c.time_acceleration = 0
        c.time_slow = 0
        c.time_reanimation = 0
        c.time_lag_kick = 0
        c.time_deviation = 0
        c.deviation_cible = None
        c.shield = 0
        c.time_shield = 0
        c.time_death_penalty = 0
        c.time_aveuglement = 0
        c.time_canalisation = 0
        c.time_inversion = 0
        c.time_marque = 0
        c.interdit = None
        c.linked = []

class Inversion(Spell):
    """ Pendant sa durée, les dégâts subis par la cible deviennent des soins et inversement. """
    def __init__(self):
        Spell.__init__(self, "Inversion", tc=100)
        self.duree_inversion = 300

    def effet(self, l, c, p):
        c.time_inversion = self.duree_inversion

    def passive(self, l, c, p):
        if self.time_cooldown > 0:
            self.time_cooldown -= 1
        if c.time_inversion > 0:
            c.time_inversion -= 1

class ProjectileMagique(Spell):
    """ Inflige 50 dégâts à la cible et à son coéquipier. """
    def __init__(self):
        Spell.__init__(self, "Magic projectile")

    def effet(self, l, c, p):
        c.dammage(50)
        ally = get_ally(c, p)
        if ally is not None:
            ally.dammage(50)

class Canalisation(Spell):
    """ Pendant sa durée, soigne la cible à chaque fois qu'un joueur (n'importe lequel) lance un sort. """
    def __init__(self):
        Spell.__init__(self, "Channeling")
        self.duree_canalisation = 800

    def effet(self, l, c, p):
        c.time_canalisation = self.duree_canalisation

    def passive(self, l, c, p):
        if self.time_cooldown > 0:
            self.time_cooldown -= 1
        if c.time_canalisation > 0:
            c.time_canalisation -= 1
            for player in p:
                if player.spell is not None and player.spell.started and player.spell.duree == 1:
                    c.heal(15)

class Aveuglement(Spell):
    """ Pendant sa durée, la cible ne peut viser qu'elle-même (voir loop()). """
    def __init__(self):
        Spell.__init__(self, "Blindness")
        self.duree_aveuglement = 800

    def effet(self, l, c, p):
        c.time_aveuglement = self.duree_aveuglement

    def passive(self, l, c, p):
        if self.time_cooldown > 0:
            self.time_cooldown -= 1
        if c.time_aveuglement > 0:
            c.time_aveuglement -= 1

class Troc(Spell):
    """ Plus ce sort est utilisé par l'ensemble des joueurs, plus il perd en puissance (compteur partagé). """
    utilisation_totale = 0

    def __init__(self):
        Spell.__init__(self, "Trade")

    def effet(self, l, c, p):
        Troc.utilisation_totale += 1
        degats = max(10, 200 - 10 * Troc.utilisation_totale)
        c.dammage(degats)

class Tempo(Spell):
    """ Diminue de 1000 le cooldown max de chaque sort de la cible (plancher à 200). """
    def __init__(self):
        Spell.__init__(self, "Tempo")

    def effet(self, l, c, p):
        for s in c.s:
            s.c = max(200, s.c - 1000)

class Marque(Spell):
    """ Rend la cible vulnérable : les dégâts qu'elle subit sont augmentés de 20% pendant sa durée. """
    def __init__(self):
        Spell.__init__(self, "Mark")
        self.duree_marque = 800
        self.multiplicateur_marque = 1.2

    def effet(self, l, c, p):
        c.time_marque = self.duree_marque

    def passive(self, l, c, p):
        if self.time_cooldown > 0:
            self.time_cooldown -= 1
        if c.time_marque > 0:
            c.time_marque -= 1

class Prolongation(Spell):
    """ Prolonge de 500 la durée restante de chaque passif actuellement actif sur la cible. """
    attributs_prolongeables = [
        "time_poison", "time_silence", "time_renvoi", "time_invincibilite",
        "time_treve", "time_clone", "time_regeneration", "time_acceleration",
        "time_slow", "time_reanimation", "time_lag_kick", "time_deviation",
        "time_shield", "time_death_penalty", "time_aveuglement", "time_canalisation",
        "time_inversion", "time_marque",
    ]

    def __init__(self):
        Spell.__init__(self, "Prolongation")
        self.bonus_prolongation = 500

    def effet(self, l, c, p):
        for attr in Prolongation.attributs_prolongeables:
            if getattr(c, attr) > 0:
                setattr(c, attr, getattr(c, attr) + self.bonus_prolongation)

spells = [Boule_feu, Laser, Poison, VolDeVie, Soin, Vitesse, Interdiction, LienSpirituel, Silence, Renvoi,
          Exodia, Multiplicateur, TicTac, Balance, Renforcement, Specialisation, Invincibilite, Treve, Clone, Retour,
          Flash, Canon, Coagulation, Regeneration, Annulation, VolDeSort, Earthquake,
          Acceleration, Ralentissement, VolDeTemps, Reanimation, LagKick, Deviation, Baffe, Bouclier,
          ConcentrationMagique, PeineDeMort, Esprit, Difference, RayonDeSoleil, ConcentrationSorts,
          Repetition, Impatience, Nettoyage, Inversion, ProjectileMagique, Canalisation, Aveuglement, Troc,
          Tempo, Prolongation, Marque]

class Sorcer:
    def __init__(self, spells):
        self.s = [s() for s in spells] # spells.
        self.pv_max = 1000
        self.pv = self.pv_max
        self.spell = None
        self.last_spell = None
        self.busy = False
        self.next_spell = None # Not used yet.
        self.cible = self # Not used yet.

        self.time_poison = 0
        self.interdit = None
        self.linked = []
        self.time_silence = 0
        self.time_renvoi = 0
        self.nbr_multiplicateur = 1
        self.tictac = "tic"
        self.nbr_exodia = 0
        self.spell_specialisation = None
        self.time_invincibilite = 0
        self.time_treve = 0
        self.time_clone = 0
        self.vie_retour = 0
        self.time_regeneration = 0

        self.time_acceleration = 0
        self.time_slow = 0
        self.time_reanimation = 0
        self.time_lag_kick = 0
        self.time_deviation = 0
        self.deviation_cible = None
        self.shield = 0
        self.time_shield = 0
        self.time_death_penalty = 0
        self.time_inversion = 0
        self.time_canalisation = 0
        self.time_aveuglement = 0
        self.time_marque = 0

    def dammage(self, d):
        if self.time_inversion > 0:
            self._heal_raw(d)
            return
        self._dammage_raw(d)

    def _dammage_raw(self, d):
        if self.time_invincibilite == 0:
            if self.pv > 0:
                if d > 0 and self.time_marque > 0:
                    d *= 1.2
                if d > 0 and self.shield > 0:
                    absorbe = min(self.shield, d)
                    self.shield -= absorbe
                    d -= absorbe
                self.pv -= d
                self.pv = int(self.pv)
                if self.pv <= 0 and d > 0 and self.time_reanimation > 0:
                    self.pv = int(self.pv_max/3)
                    self.time_reanimation = 0
                else:
                    self.pv = 0 if self.pv < 0 else self.pv
                for link in self.linked:
                    if link[1] is not self:
                        if link[1].pv > 0:
                            link[1].pv -= d
                            link[1].pv = int(link[1].pv)
                            link[1].pv = 0 if link[1].pv < 0 else link[1].pv
                    if link[2] is not self:
                        if link[2].pv > 0:
                            link[2].pv -= d
                            link[2].pv = int(link[2].pv)
                            link[2].pv = 0 if link[2].pv < 0 else link[2].pv

    def heal(self, d):
        if self.time_inversion > 0:
            self._dammage_raw(d)
            return
        self._heal_raw(d)

    def _heal_raw(self, d):
        if self.pv > 0:
            self.pv += d
            self.pv = int(self.pv)
            self.pv = self.pv_max if self.pv > self.pv_max else self.pv
            for link in self.linked:
                if link[1] is not self:
                    if link[1].pv > 0:
                        link[1].pv += d
                        link[1].pv = int(link[1].pv)
                        link[1].pv = link[1].pv_max if link[1].pv > link[1].pv_max else link[1].pv
                if link[2] is not self:
                    if link[2].pv > 0:
                        link[2].pv += d
                        link[2].pv = int(link[2].pv)
                        link[2].pv = link[2].pv_max if link[2].pv > link[2].pv_max else link[2].pv


difficulte  = 3
def start():
    global p1, p2, p3, p4, players, team_a, team_b, spells, difficulte

    s = list(spells)
    cooldown_base = 2000
    cooldown_base = 2000 * difficulte
    if difficulte == 1:
        s = spells[:10]
    elif difficulte == 2:
        s = spells[:20]
    p1 = Sorcer(s)
    p2 = Sorcer(s)
    p3 = Sorcer(s)
    p4 = Sorcer(s)

    players = [p1, p2, p3, p4]
    team_a = [p1, p2] # Not used.
    team_b = [p3, p4] # Not used.
    for p in players:
        for s in p.s:
            s.c = cooldown_base

    Troc.utilisation_totale = 0

    print("New fight")

def loop(commands):
    for i, c in enumerate(commands):
        n, cible = c.split(";")
        cible = int(cible)

        p = players[i]
        if p is p1:
            p.cible = [p1, p2, p3, p4][cible]
        elif p is p2:
            p.cible = [p2, p1, p4, p3][cible]
        elif p is p3:
            p.cible = [p3, p4, p1, p2][cible]
        elif p is p4:
            p.cible = [p4, p3, p2, p1][cible]

        if p.time_deviation > 0 and p.deviation_cible is not None:
            p.cible = p.deviation_cible
        if p.time_aveuglement > 0:
            p.cible = p

        if n != "":
            n = int(n)
            if p.spell is None:
                p.spell = p.s[n]
                p.spell = None if p.spell.time_cooldown > 0 else p.spell
                p.spell = None if p.spell is p.interdit else p.spell
                p.spell = None if p.time_silence > 0 else p.spell
                p.spell = None if p.pv <= 0 else p.spell
                for player in players:
                    if player.time_treve > 0:
                        p.spell = None
                if p.spell is not None:
                    print(f"Spell p{i+1} :", p.spell, "; Target :", cible)

    for p in players:
        s = p.spell
        if s is not None:
            s.start(p, p.cible, players)
            if p.cible.time_renvoi > 0:
                s.action(p, p, players)
            else:
                s.action(p, p.cible, players)
            s.end(p, p.cible, players)
        for s in p.s:
            s.passive(p, p.cible, players)

    for p in players:
        if p.time_clone > 0:
            if p.spell is not None:
                s_clone = copy.copy(p.spell)
                if s_clone is not None:
                    s_clone.start(p, p.cible, players)
                    if p.cible.time_renvoi > 0:
                        s_clone.action(p, p, players)
                    else:
                        s_clone.action(p, p.cible, players)
                    s_clone.end(p, p.cible, players)

    return p1, p2, p3, p4
