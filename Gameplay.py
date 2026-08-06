import copy

difficulte  = 3
cooldown_base = int(15000/26) * difficulte

team_scores = [0, 0]
team_winner = None


def get_spell_preview_text(spell):
    """Retourne le texte de prévisualisation d'un sort pour l'interface."""
    if spell is None:
        return ""
    description = getattr(spell, "description", "") or ""
    if description:
        return f"{spell.n} : {description}"
    return spell.n


def get_ally(player, p):
    """ Coéquipier de player dans p, en supposant des paires (p[0],p[1]), (p[2],p[3])... comme team_a/team_b. """
    if player not in p:
        return None
    i = p.index(player)
    j = i - 1 if i % 2 == 1 else i + 1
    return p[j] if 0 <= j < len(p) else None


class Spell:
    """Classe de base pour les sorts avec cooldown, temps de charge, durée et lag."""
    def __init__(self, n, c=cooldown_base, tc=200, d=1, tl=100):
        self.n = n  # Nom
        self.c = c  # Cooldown
        self.tc = tc  # Temps de charge
        self.d = d  # Durée
        self.tl = tl  # Temps de lag
        self.description = self._build_description()

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
        self._last_spell_registered = False

    def _build_description(self):
        doc = self.__class__.__doc__
        if doc:
            return " ".join(line.strip() for line in doc.strip().splitlines() if line.strip())
        return self.n
    
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
            self.effect_target = c
            if self.duree <= self.d:
                if not getattr(self, "_last_spell_registered", False):
                    if not isinstance(self, (Repetition, Specialisation)):
                        l.last_spell = self
                    self._last_spell_registered = True
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

    def passive(self, l, c, p):
        """ Cooldown. """
        if self.time_cooldown > 0:
            self.time_cooldown -= 1

    def _tick_target_timers(self, l, c):
        target = c if c is not None else l
        if target is None:
            return
        if getattr(target, "_duration_tick_done", False):
            return
        target.tick_duration_counters()

class Boule_feu(Spell):
    """ Inflige 25 points de dégâts au lanceur et 125 points de dégâts à la cible. """
    def __init__(self):
        Spell.__init__(self, "Fireball", tc=100)

    def effet(self, l, c, p):
        l.dammage(25)
        c.dammage(125)

class Laser(Spell):
    """ Inflige 1 point de dégâts par tick à la cible pendant 200 ticks. """
    def __init__(self):
        Spell.__init__(self, "Laser", d=200)

    def effet(self, l, c, p):
        c.dammage(1)

class Poison(Spell):
    """ Applique un poison qui inflige 25 dégâts toutes les 100 unités de temps pendant 1000 ticks. """
    def __init__(self):
        Spell.__init__(self, "Poison")
        self.duree_poison = 1000

    def effet(self, l, c, p):
        c.time_poison = self.duree_poison

    def passive(self, l, c, p):
        if self.time_cooldown > 0:
            self.time_cooldown -= 1
        if c is None:
            return
        self._tick_target_timers(l, c)
        if c.time_poison % 100 == 1:
            c.dammage(25)

class VolDeVie(Spell):
    """ Vole de la vie à la cible en infligeant 1 dégât et en soignant 1 point par tick pendant 50 ticks. """
    def __init__(self):
        Spell.__init__(self, "Life steal", d=50)

    def effet(self, l, c, p):
        c.dammage(1)
        l.heal(1)

class Soin(Spell):
    """ Soigne la cible de 100 points et supprime l'effet poison. """
    def __init__(self):
        Spell.__init__(self, "Heal")

    def effet(self, l, c, p):
        c.heal(100)
        c.time_poison = 0

class Vitesse(Spell):
    """ Réduit de moitié le cooldown de tous les sorts de la cible. """
    def __init__(self):
        Spell.__init__(self, "Speed")

    def effet(self, l, c, p):
        for s in c.s:
            s.time_cooldown = int(s.time_cooldown / 2)

class Interdiction(Spell):
    """ Empêche indéfiniment la cible d'utiliser le sort qu'elle est en train de lancer ou jusqu'à une nouvelle interdiction. """
    def __init__(self):
        Spell.__init__(self, "Interdiction", tc=0)
        
    def effet(self, l, c, p):
        if c.spell is not None:
            c.interdit = c.spell

class LienSpirituel(Spell):
    """ Crée un lien spirituel entre le lanceur et la cible pendant 800 ticks. """
    def __init__(self):
        Spell.__init__(self, "Spiritual link")

    def effet(self, l, c, p):
        l.linked.append([800, l, c])
        c.linked.append([800, l, c])

    def passive(self, l, c, p):
        if self.time_cooldown > 0:
            self.time_cooldown -= 1
        if c is None:
            return
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
    """ Silence la cible pendant 400 ticks. """
    def __init__(self):
        Spell.__init__(self, "Silence")

    def effet(self, l, c, p):
        c.time_silence = 400

    def passive(self, l, c, p):
        if self.time_cooldown > 0:
            self.time_cooldown -= 1
        if c is None:
            return
        self._tick_target_timers(l, c)

class Renvoi(Spell):
    """ Active un renvoi pendant 200 ticks pour renvoyer des sorts ciblant la cible. """
    def __init__(self):
        Spell.__init__(self, "Counter", tc=50, tl=200)
        self.effect_target = None

    def effet(self, l, c, p):
        self.effect_target = c
        c.time_renvoi = 200

    def passive(self, l, c, p):
        if self.time_cooldown > 0:
            self.time_cooldown -= 1
        if c is None and getattr(self, "effect_target", None) is None:
            return
        if getattr(self, "effect_target", None) is None:
            if not getattr(self, "started", False):
                return
            target = c
        else:
            target = self.effect_target

        if target is None:
            return

        if getattr(target, "time_renvoi", 0) > 0 and not getattr(target, "_duration_tick_done", False):
            target.time_renvoi -= 1

class Exodia(Spell):
    """ Incrémente le compteur Exodia et élimine tous les adversaires quand il atteint 5. """
    def __init__(self):
        Spell.__init__(self, "Exodia")

    def effet(self, l, c, p):
        l.nbr_exodia += 1
        if l.nbr_exodia >= 5:
            ally = get_ally(l, p)
            for player in p:
                if player is l or player is ally:
                    continue
                if getattr(player, "pv", 0) > 0:
                    player.pv = 0
            l.nbr_exodia = 0

class Multiplicateur(Spell):
    """ Inflige 40 dégats multiplié par le compteur multiplicateur du lanceur. """
    def __init__(self):
        Spell.__init__(self, "Multiplier")

    def effet(self, l, c, p):
        c.dammage(40*l.nbr_multiplicateur)
        l.nbr_multiplicateur += 1

class TicTac(Spell):
    """ Alterne entre deux dégâts : 20% sur les PV actuels ou 25% sur les PV manquants de la cible. """
    def __init__(self):
        Spell.__init__(self, "TicTac")

    def effet(self, l, c, p):
        if l.tictac == "tic":
            c.dammage(int(c.pv*0.2))
            l.tictac = "tac"
        else:
            c.dammage(int((c.pv_max-c.pv)*0.25))
            l.tictac = "tic"

class Balance(Spell):
    """ Équilibre les PV du lanceur et de la cible en infligeant un tiers de la différence. """
    def __init__(self):
        Spell.__init__(self, "Balance")

    def effet(self, l, c, p):
        l.dammage((l.pv - c.pv)/3)
        c.dammage((c.pv - l.pv)/3)

class Renforcement(Spell):
    """ Augmente les PV maximales de la cible de 75 et la soigne de 25 points. """
    def __init__(self):
        Spell.__init__(self, "Reinforcement")
    def effet(self, l, c, p):
        c.pv_max += 75
        c.heal(25)

class Specialisation(Spell):
    """ Marque le dernier sort lancé comme spécialisation, divisant sont cooldown par 4. """
    def __init__(self):
        Spell.__init__(self, "Specialisation")

    def effet(self, l, c, p):
        if l.last_spell is not None:
            l.last_spell.time_cooldown = int(l.last_spell.time_cooldown/3)
            l.spell_specialisation = l.last_spell

class Invincibilite(Spell):
    """ Rend la cible invincible pendant 250 ticks. """
    def __init__(self):
        Spell.__init__(self, "Invincibility", tc=0, d=250)

    def effet(self, l, c, p):
        self.effect_target = c
        c.time_invincibilite = 250

    def passive(self, l, c, p):
        if self.time_cooldown > 0:
            self.time_cooldown -= 1

class Treve(Spell):
    """ Accorde une trêve de 300 ticks au lanceur, empêchant le lancement de sorts pendant sa durée. """
    def __init__(self):
        Spell.__init__(self, "Truce", tc=10)

    def effet(self, l, c, p):
        self.effect_target = l
        l.time_treve = 300

    def passive(self, l, c, p):
        if self.time_cooldown > 0:
            self.time_cooldown -= 1

class Clone(Spell):
    """ Applique un clone à la cible pendant 600 ticks. """
    def __init__(self):
        Spell.__init__(self, "Clone")

    def effet(self, l, c, p):
        c.time_clone = 600

    def passive(self, l, c, p):
        if self.time_cooldown > 0:
            self.time_cooldown -= 1

class Retour(Spell):
    """ Enregistre la vie actuelle de la cible et la restaure à la fin de la durée de 300 ticks. """
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
    """ Inflige instantanément 20 dégâts à la cible. Achève la cible si celle-ci possède moins de 10% de ses points de vie max. """
    def __init__(self):
        Spell.__init__(self, "Flash", tc=0, d=1)

    def effet(self, l, c, p):
        c.dammage(20)
        if c.pv > 0 and c.pv <= int(c.pv_max * 0.1):
            c.pv = 0

class Canon(Spell):
    """ Charge pendant 400 ticks puis frappe la cible pour 200 dégâts. """
    def __init__(self):
        Spell.__init__(self, "Cannon", tc=400, d=1)
    
    def effet(self, l, c, p):
        c.dammage(200)

class Coagulation(Spell):
    """ Soigne la cible de 1 point à chaque tick pendant 150 ticks. """
    def __init__(self):
        Spell.__init__(self, "Coagulation", d=150)

    def effet(self, l, c, p):
        c.heal(1)

class Regeneration(Spell):
    """ Applique une régénération de 20 points de vie à la cible tous les 100 ticks pendant 500 ticks. """
    def __init__(self):
        Spell.__init__(self, "Regeneration")
        self.duree_regeneration = 500

    def effet(self, l, c, p):
        c.time_regeneration = self.duree_regeneration

    def passive(self, l, c, p):
        if self.time_cooldown > 0:
            self.time_cooldown -= 1
        if c.time_regeneration % 100 == 1:
            c.heal(20)

class Annulation(Spell):
    """ Force le sort cible à s'achever immédiatement et met son cooldown à son maximum. """
    def __init__(self):
        Spell.__init__(self, "Cancelation", tc=50)

    def effet(self, l, c, p):
        if c.spell is not None:
            c.spell.time_cooldown = c.spell.c
            c.spell.started = True
            c.spell.ended = True

class VolDeSort(Spell):
    """ Vole le sort actuellement lancé par la cible et échange ce sort avec le lanceur. """
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
    """ Inflige 150 dégâts à tous les joueurs. """
    def __init__(self):
        Spell.__init__(self, "Earthquake")

    def effet(self, l, c, p):
        for player in p:
            player.dammage(150)

class Acceleration(Spell):
    """ Accélère les lancers (x2) et le lag (/2) du joueur ciblé ; annule Slow. Dure 2500 ticks. """
    def __init__(self):
        Spell.__init__(self, "Speed up")
        self.duree_acceleration = 2500

    def effet(self, l, c, p):
        c.time_acceleration = self.duree_acceleration
        c.time_slow = 0

    def passive(self, l, c, p):
        if self.time_cooldown > 0:
            self.time_cooldown -= 1

class Ralentissement(Spell):
    """ Ralentit les lancers (/2) et augmente les cooldowns (x2) du joueur ciblé ; annule Acceleration. Dure 2500 ticks. """
    def __init__(self):
        Spell.__init__(self, "Slow")
        self.duree_slow = 2500

    def effet(self, l, c, p):
        c.time_slow = self.duree_slow
        c.time_acceleration = 0

    def passive(self, l, c, p):
        if self.time_cooldown > 0:
            self.time_cooldown -= 1

class VolDeTemps(Spell):
    """ Réduit le cooldown de tous les sorts du lanceur au cooldown actuel des sorts de la cible. """
    def __init__(self):
        Spell.__init__(self, "Time steal")

    def effet(self, l, c, p):
        for spell_c in c.s:
            if spell_c.time_cooldown == 0:
                for spell_l in l.s:
                    spell_l.time_cooldown = min(spell_c.time_cooldown, spell_l.time_cooldown)

class Reanimation(Spell):
    """ Si actif au moment où la cible devrait mourir, elle ressuscite avec point de vie max divisé par 3 au lieu de mourir. 600 ticks. """
    def __init__(self):
        Spell.__init__(self, "Reanimation")
        self.duree_reanimation = 600

    def effet(self, l, c, p):
        c.time_reanimation = self.duree_reanimation

    def passive(self, l, c, p):
        if self.time_cooldown > 0:
            self.time_cooldown -= 1

class Puissance(Spell):
    """ Cumule 1 dégat pour chaque 15 ticks durant lequel le lanceur n'a pas subit de dégats.
        Lorsque le sort est lancé, inflige tous les dégats cumulés à la cible.
        Le cumule est remis à 0 dès que le lanceur subit un dégât. """
    def __init__(self):
        Spell.__init__(self, "Puissance", tc=50)

    def effet(self, l, c, p):
        self.effect_target = l
        if l.time_puissance > 0:
            c.dammage(l.time_puissance)
        l.time_puissance = 0
        l.puissance_ticks_since_damage = 0

    def passive(self, l, c, p):
        if self.time_cooldown > 0:
            self.time_cooldown -= 1
        if l.pv > 0:
            l.puissance_ticks_since_damage += 1
            while l.puissance_ticks_since_damage >= 15:
                l.time_puissance += 1
                l.puissance_ticks_since_damage -= 15


class Deviation(Spell):
    """ Force tous les joueurs à lancer ses sorts sur la cible pendant 600 ticks. """
    def __init__(self):
        Spell.__init__(self, "Deviation")
        self.duree_deviation = 600

    def effet(self, l, c, p):
        c.time_deviation = self.duree_deviation
        c.deviation_cible = c

    def passive(self, l, c, p):
        if self.time_cooldown > 0:
            self.time_cooldown -= 1

class Baffe(Spell):
    """Un coup rapide qui inflige 15 dégâts avec un cooldown court."""
    def __init__(self):
        Spell.__init__(self, "Quick slap", c=int(cooldown_base/10), tc=20, tl=20)

    def effet(self, l, c, p):
        c.dammage(15)

class Bouclier(Spell):
    """ Réduit chaque source de dégâts de 25 et absorbe les dégâts supérieur à 150 pendant 3000 ticks. """
    def __init__(self):
        Spell.__init__(self, "Shield")
        self.duree_shield = 3000

    def effet(self, l, c, p):
        c.shield = 25
        c.shield_max = 150
        c.time_shield = self.duree_shield

    def passive(self, l, c, p):
        if self.time_cooldown > 0:
            self.time_cooldown -= 1

class ConcentrationMagique(Spell):
    """ Soigne 5 dégâts par sort de la cible actuellement disponible (hors cooldown). """
    def __init__(self):
        Spell.__init__(self, "Magic concentration")

    def effet(self, l, c, p):
        dispo = sum(1 for s in c.s if s.time_cooldown == 0)
        c.heal(5 * dispo)

class PeineDeMort(Spell):
    """ Après 3000 ticks, tue la cible sauf si elle est invincible, si le sort a été relancé
    entre-temps (délai réinitialisé) ou si Nettoyage a purgé le passif (délai remis à 0). """
    def __init__(self):
        Spell.__init__(self, "Death penalty", tc=200)
        self.duree_death_penalty = 3000

    def effet(self, l, c, p):
        c.time_death_penalty = self.duree_death_penalty
        c.death_penalty_armed = True

    def passive(self, l, c, p):
        if self.time_cooldown > 0:
            self.time_cooldown -= 1
        before = getattr(c, "time_death_penalty", 0)
        self._tick_target_timers(l, c)
        expired_now = before > 0 and c.time_death_penalty == 0
        if (getattr(c, "death_penalty_armed", False) or expired_now) and c.time_death_penalty == 0:
            if c.time_invincibilite == 0:
                c.force_death()
            c.death_penalty_armed = False

class Esprit(Spell):
    """ Inflige 200 dégâts à la cible pour chaque joueur mort dans la partie. """
    def __init__(self):
        Spell.__init__(self, "Spirit")

    def effet(self, l, c, p):
        morts = sum(1 for player in p if player.pv <= 0)
        c.dammage(200 * morts)

class Difference(Spell):
    """ Inflige la différence de points de vie entre la cible et son coéquipier divisé par 2. """
    def __init__(self):
        Spell.__init__(self, "Difference")

    def effet(self, l, c, p):
        ally = get_ally(c, p)
        if ally is not None:
            c.dammage(abs(c.pv - ally.pv) // 2)

class RayonDeSoleil(Spell):
    """ Premier lancer : charge (pas de dégâts). Lancer suivant : inflige 300 points de dégâts. """
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
    """ Inflige 75 dégâts par sort actuellement en cours de lancement. """
    def __init__(self):
        Spell.__init__(self, "Spell concentration")

    def effet(self, l, c, p):
        en_cours = sum(1 for player in p if player.spell is not None and player.spell.started and not player.spell.ended)
        c.dammage(75 * en_cours)

class Repetition(Spell):
    """Redéclenche immédiatement l'effet du dernier sort lancé par le lanceur. """
    def __init__(self):
        Spell.__init__(self, "Repeat")

    def effet(self, l, c, p):
        if l.last_spell is not None:
            l.last_spell.effet(l, c, p)

class Impatience(Spell):
    """Inflige en dégâts la somme des cooldown des sorts de la cible divisé par 1000. """
    def __init__(self):
        Spell.__init__(self, "Impatience")

    def effet(self, l, c, p):
        total = sum(s.time_cooldown for s in c.s)
        c.dammage(int(total / 1000))

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
        c.time_puissance = 0
        c.puissance_ticks_since_damage = 0
        c.time_deviation = 0
        c.deviation_cible = None
        c.shield = 0
        c.time_shield = 0
        c.time_death_penalty = 0
        c.death_penalty_armed = False
        c.time_aveuglement = 0
        c.time_canalisation = 0
        c.time_inversion = 0
        c.time_marque = 0
        c.interdit = None
        c.linked = []

class Inversion(Spell):
    """ Pendant une durée de 1000 ticks, les dégâts subis par la cible deviennent des soins et inversement. """
    def __init__(self):
        Spell.__init__(self, "Inversion", tc=100)
        self.duree_inversion = 1000

    def effet(self, l, c, p):
        c.time_inversion = self.duree_inversion

    def passive(self, l, c, p):
        if self.time_cooldown > 0:
            self.time_cooldown -= 1

class ProjectileMagique(Spell):
    """ Inflige 75 dégâts à la cible et à son coéquipier. """
    def __init__(self):
        Spell.__init__(self, "Magic projectile")

    def effet(self, l, c, p):
        c.dammage(75)
        ally = get_ally(c, p)
        if ally is not None:
            ally.dammage(75)

class Canalisation(Spell):
    """ Pendant une durée de 800 ticks, soigne la cible à chaque fois qu'un joueur (n'importe lequel) lance un sort. """
    def __init__(self):
        Spell.__init__(self, "Channeling")
        self.duree_canalisation = 800

    def effet(self, l, c, p):
        c.time_canalisation = self.duree_canalisation

    def passive(self, l, c, p):
        if self.time_cooldown > 0:
            self.time_cooldown -= 1
        if c.time_canalisation > 0:
            for player in p:
                if player.spell is not None and player.spell.started and player.spell.duree == 1:
                    c.heal(15)

class Aveuglement(Spell):
    """ Pendant une durée de 800 ticks, la cible ne peut viser qu'elle-même. """
    def __init__(self):
        Spell.__init__(self, "Blindness")
        self.duree_aveuglement = 800

    def effet(self, l, c, p):
        c.time_aveuglement = self.duree_aveuglement

    def passive(self, l, c, p):
        if self.time_cooldown > 0:
            self.time_cooldown -= 1

class Troc(Spell):
    """ La puissance de ce sort commence à 0, augmente de 1 tous les 100 ticks, puis est réinitialisée à 0 lorsqu'il est utilisé par un joueur. """
    utilisation_totale = 0
    puissance = 0

    def __init__(self):
        Spell.__init__(self, "Trade")

    def effet(self, l, c, p):
        Troc.utilisation_totale += 1
        degats = max(0, int(Troc.puissance/100))
        c.dammage(degats)
        Troc.puissance = 0

    def passive(self, l, c, p):
        super().passive(l, c, p)
        Troc.puissance += 1

class Tempo(Spell):
    """ Diminue de 3000 le cooldown max de chaque sort de la cible (plancher à 200). """
    def __init__(self):
        Spell.__init__(self, "Tempo")

    def effet(self, l, c, p):
        for s in c.s:
            s.c = max(200, s.c - 3000)

class Marque(Spell):
    """ Rend la cible vulnérable : les dégâts qu'elle subit sont augmentés de 100% pendant sa durée pendant 800 ticks. """
    def __init__(self):
        Spell.__init__(self, "Mark")
        self.duree_marque = 800
        self.multiplicateur_marque = 2.0

    def effet(self, l, c, p):
        c.time_marque = self.duree_marque

    def passive(self, l, c, p):
        if self.time_cooldown > 0:
            self.time_cooldown -= 1

class Prolongation(Spell):
    """ Prolonge de 1000 la durée restante de chaque passif actuellement actif sur la cible. """
    attributs_prolongeables = [
        "time_poison", "time_silence", "time_renvoi", "time_invincibilite",
        "time_treve", "time_clone", "time_regeneration", "time_acceleration",
        "time_slow", "time_reanimation", "time_deviation",
        "time_shield", "time_death_penalty", "time_aveuglement", "time_canalisation",
        "time_inversion", "time_marque",
    ]

    def __init__(self):
        Spell.__init__(self, "Prolongation")
        self.bonus_prolongation = 1000

    def effet(self, l, c, p):
        for attr in Prolongation.attributs_prolongeables:
            if getattr(c, attr) > 0:
                setattr(c, attr, getattr(c, attr) + self.bonus_prolongation)

spells = [Boule_feu, Laser, Poison, VolDeVie, Soin, Vitesse, Interdiction, LienSpirituel, Silence, Renvoi,
          Exodia, Multiplicateur, TicTac, Balance, Renforcement, Specialisation, Invincibilite, Treve, Clone, Retour,
          Flash, Canon, Coagulation, Regeneration, Annulation, VolDeSort, Earthquake,
          Acceleration, Ralentissement, VolDeTemps, Reanimation, Puissance, Deviation, Baffe, Bouclier,
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
        self.time_puissance = 0
        self.puissance_ticks_since_damage = 0
        self.time_deviation = 0
        self.deviation_cible = None
        self.shield = 0
        self.time_shield = 0
        self.time_death_penalty = 0
        self.death_penalty_armed = False
        self.time_inversion = 0
        self.time_canalisation = 0
        self.time_aveuglement = 0
        self.time_marque = 0
        self._duration_tick_done = False

    def dammage(self, d):
        if self.time_inversion > 0:
            self._heal_raw(d)
            return
        self._dammage_raw(int(d))

    def force_death(self):
        if self.pv <= 0:
            return
        if self.time_reanimation > 0:
            self.pv = int(self.pv_max/3)
            self.time_reanimation = 0
            return
        self.pv = 0

    def tick_duration_counters(self):
        duration_attributes = [
            "time_poison", "time_silence", "time_renvoi", "time_invincibilite",
            "time_treve", "time_clone", "time_regeneration", "time_acceleration",
            "time_slow", "time_reanimation", "time_deviation", "time_shield",
            "time_death_penalty", "time_inversion", "time_canalisation",
            "time_aveuglement", "time_marque",
        ]
        for attr in duration_attributes:
            current = getattr(self, attr, 0)
            if current > 0:
                setattr(self, attr, current - 1)
        if self.time_shield <= 0:
            self.shield = 0
        if self.time_deviation <= 0:
            self.deviation_cible = None
        self._duration_tick_done = True

    def _dammage_raw(self, d):
        if self.time_invincibilite == 0:
            if self.pv > 0:
                if d > 0 and self.time_marque > 0:
                    d *= 1.2
                if d > 0 and self.time_shield > 0 and self.shield > 0:
                    d = min(self.shield_max, max(0, d - self.shield)) if d > self.shield_max else max(0, d - self.shield)
                self.pv -= d
                self.pv = int(self.pv)
                if self.pv <= 0 and d > 0 and self.time_reanimation > 0:
                    self.pv = int(self.pv_max/3)
                    self.time_reanimation = 0
                if d > 0:
                    self.puissance_ticks_since_damage = 0
                    self.time_puissance = 0
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


def reset_team_scores():
    global team_scores, team_winner
    team_scores = [0, 0]
    team_winner = None


def get_team_scores(players_list=None):
    return list(team_scores)


def update_team_scores(players_list=None):
    global team_scores, team_winner

    if players_list is None:
        players_list = globals().get("players")
    if players_list is None:
        players_list = [globals().get("p1"), globals().get("p2"), globals().get("p3"), globals().get("p4")]

    team_a_players = globals().get("team_a")
    if team_a_players is None or len(team_a_players) < 2:
        team_a_players = players_list[:2]
    team_b_players = globals().get("team_b")
    if team_b_players is None or len(team_b_players) < 2:
        team_b_players = players_list[2:4]

    team_a_alive = any(getattr(player, "pv", 0) > 0 for player in team_a_players)
    team_b_alive = any(getattr(player, "pv", 0) > 0 for player in team_b_players)

    if team_a_alive and not team_b_alive:
        winner = 0
    elif team_b_alive and not team_a_alive:
        winner = 1
    else:
        winner = None

    if winner is not None and team_winner != winner:
        team_scores[winner] += 1
        team_winner = winner
    elif winner is None:
        team_winner = None

    return list(team_scores)


def start(reset_scores=True):
    global p1, p2, p3, p4, players, team_a, team_b, spells, difficulte, cooldown_base
    difficulte += 1
    difficulte = min(difficulte, 26)
    difficulte = max(difficulte, 1)

    s = list(spells)
    s = spells[:min(difficulte*2, len(spells))]
    p1 = Sorcer(s)
    p2 = Sorcer(s)
    p3 = Sorcer(s)
    p4 = Sorcer(s)

    players = [p1, p2, p3, p4]
    team_a = [p1, p2] # Not used.
    team_b = [p3, p4] # Not used.
    if reset_scores:
        reset_team_scores()

    Troc.utilisation_totale = 0

    print("New fight")

def loop(commands):
    forced_deviation_target = next(
        (
            player.deviation_cible
            for player in players
            if player.time_deviation > 0 and player.deviation_cible is not None
        ),
        None,
    )

    for i, c in enumerate(commands):
        p = players[i]
        n = ""
        cible = None
        if isinstance(c, str) and ";" in c:
            n, cible_str = c.split(";", 1)
            try:
                cible = int(cible_str)
            except ValueError:
                cible = None

        # Ne pas laisser les commandes réseau re-cibler un sort déjà en cours.
        # Cela évite le clignotement des flèches et les retargets en plein cast.
        if cible is not None and p.spell is None:
            try:
                if p is p1:
                    p.cible = [p1, p2, p3, p4][cible]
                elif p is p2:
                    p.cible = [p2, p1, p4, p3][cible]
                elif p is p3:
                    p.cible = [p3, p4, p1, p2][cible]
                elif p is p4:
                    p.cible = [p4, p3, p2, p1][cible]
            except IndexError:
                pass

        if p.time_aveuglement > 0:
            p.cible = p
        if forced_deviation_target is not None:
            p.cible = forced_deviation_target

        if p.cible is not None and getattr(p.cible, "pv", 0) <= 0:
            p.cible = None

        if n != "":
            try:
                n = int(n)
            except ValueError:
                n = ""
        if n != "":
            if p.spell is None:
                valid_target = p.cible is not None and getattr(p.cible, "pv", 0) > 0
                if not valid_target:
                    p.spell = None
                else:
                    try:
                        p.spell = p.s[n]
                        p.spell = None if p.spell.time_cooldown > 0 else p.spell
                        p.spell = None if p.spell is p.interdit else p.spell
                        p.spell = None if p.time_silence > 0 else p.spell
                        p.spell = None if p.pv <= 0 else p.spell
                    except IndexError:
                        p.spell = None
                    for player in players:
                        if player.time_treve > 0:
                            p.spell = None
                    if p.spell is not None:
                        print(f"Spell p{i+1} :", p.spell, "; Target :", cible)

    for p in players:
        p._duration_tick_done = False

    for p in players:
        p.tick_duration_counters()

    for p in players:
        s = p.spell
        if s is not None:
            if p.pv > 0:
                target = p.cible
                if target is None or getattr(target, "pv", 0) <= 0:
                    p.spell = None
                    p.busy = False
                    continue
                s.start(p, target, players)
                if getattr(target, "time_renvoi", 0) > 0:
                    s.action(p, p, players)
                else:
                    s.action(p, target, players)
                s.end(p, target, players)
            else:
                p.spell = None
                p.busy = False
        for s in p.s:
            passive_target = getattr(s, "effect_target", None)
            if passive_target is None:
                passive_target = p.cible
            s.passive(p, passive_target, players)

    for p in players:
        if p.time_clone > 0:
            if p.spell is not None:
                target = p.cible
                if target is None or getattr(target, "pv", 0) <= 0:
                    continue
                s_clone = copy.copy(p.spell)
                if s_clone is not None:
                    s_clone.start(p, target, players)
                    if getattr(target, "time_renvoi", 0) > 0:
                        s_clone.action(p, p, players)
                    else:
                        s_clone.action(p, target, players)
                    s_clone.end(p, target, players)

    update_team_scores(players)

    return p1, p2, p3, p4
