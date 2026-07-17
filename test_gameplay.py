import pytest

import Gameplay as gp
from Gameplay import (
    Sorcer, Spell,
    Boule_feu, Laser, Poison, VolDeVie, Soin, Vitesse, Interdiction,
    LienSpirituel, Silence, Renvoi, Exodia, Multiplicateur, TicTac, Balance,
    Renforcement, Specialisation, Invincibilite, Treve, Clone, Retour,
    Flash, Canon, Coagulation, Regeneration, Annulation, VolDeSort, Earthquake,
    Acceleration, Ralentissement, VolDeTemps, Reanimation, LagKick, Deviation,
    Baffe, Bouclier, ConcentrationMagique, PeineDeMort, Esprit,
    Difference, RayonDeSoleil, ConcentrationSorts, Repetition, Impatience,
    Nettoyage, Inversion, ProjectileMagique, Canalisation, Aveuglement, Troc,
    Tempo, Prolongation, Marque,
)


def make_sorcer():
    """Sorcer sans sorts, pratique pour tester dammage/heal isolément."""
    return Sorcer([])


@pytest.fixture
def caster():
    return make_sorcer()


@pytest.fixture
def target():
    return make_sorcer()


@pytest.fixture
def players(caster, target):
    return [caster, target]


# ---------------------------------------------------------------------------
# Mécaniques de base de Sorcer (dammage / heal)
# ---------------------------------------------------------------------------

class TestSorcerDammageHeal:
    def test_dammage_reduces_pv(self, caster):
        caster.dammage(100)
        assert caster.pv == caster.pv_max - 100

    def test_dammage_floors_at_zero(self, caster):
        caster.dammage(caster.pv_max + 500)
        assert caster.pv == 0

    def test_dammage_does_nothing_once_dead(self, caster):
        caster.pv = 0
        caster.dammage(50)
        assert caster.pv == 0

    def test_dammage_blocked_by_invincibility(self, caster):
        caster.time_invincibilite = 10
        caster.dammage(100)
        assert caster.pv == caster.pv_max

    def test_heal_increases_pv(self, caster):
        caster.pv = 100
        caster.heal(50)
        assert caster.pv == 150

    def test_heal_caps_at_pv_max(self, caster):
        caster.pv = caster.pv_max - 10
        caster.heal(50)
        assert caster.pv == caster.pv_max

    def test_heal_does_nothing_once_dead(self, caster):
        caster.pv = 0
        caster.heal(50)
        assert caster.pv == 0

    def test_dammage_propagates_through_link(self, caster, target):
        caster.linked.append([800, caster, target])
        target.linked.append([800, caster, target])
        caster.dammage(30)
        assert caster.pv == caster.pv_max - 30
        assert target.pv == target.pv_max - 30

    def test_heal_propagates_through_link(self, caster, target):
        caster.pv = 100
        target.pv = 100
        caster.linked.append([800, caster, target])
        target.linked.append([800, caster, target])
        caster.heal(20)
        assert caster.pv == 120
        assert target.pv == 120


# ---------------------------------------------------------------------------
# Cycle de vie générique d'un sort (start -> action -> end)
# ---------------------------------------------------------------------------

class TestSpellLifecycle:
    def test_full_cycle_applies_effect_and_sets_cooldown(self, caster, target, players):
        spell = Boule_feu()
        caster.spell = spell

        for _ in range(spell.tc):
            spell.start(caster, target, players)
        assert spell.started

        for _ in range(spell.d + 1):
            spell.action(caster, target, players)
        assert spell.ended
        assert target.pv == target.pv_max - 125
        assert caster.pv == caster.pv_max - 25

        for _ in range(spell.tl):
            spell.end(caster, target, players)

        assert spell.time_cooldown == spell.c
        assert caster.spell is None
        assert caster.busy is False
        assert caster.last_spell is spell

    def test_specialisation_cuts_cooldown_to_a_third(self, caster, target, players):
        spell = Boule_feu()
        caster.spell_specialisation = spell
        spell.started = True
        spell.ended = True
        spell.time_lag = spell.tl - 1

        spell.end(caster, target, players)

        assert spell.time_cooldown == int(spell.c / 3)

    def test_passive_decrements_cooldown(self, caster, target, players):
        spell = Boule_feu()
        spell.time_cooldown = 5
        spell.passive(caster, target, players)
        assert spell.time_cooldown == 4

    def test_passive_does_not_go_negative(self, caster, target, players):
        spell = Boule_feu()
        spell.time_cooldown = 0
        spell.passive(caster, target, players)
        assert spell.time_cooldown == 0


# ---------------------------------------------------------------------------
# Sorts individuels : effet() / passive() / start()+action() spécifiques
# ---------------------------------------------------------------------------

class TestBouleFeu:
    def test_effet(self, caster, target, players):
        Boule_feu().effet(caster, target, players)
        assert caster.pv == caster.pv_max - 25
        assert target.pv == target.pv_max - 125


class TestLaser:
    def test_effet(self, caster, target, players):
        Laser().effet(caster, target, players)
        assert target.pv == target.pv_max - 1
        assert caster.pv == caster.pv_max


class TestPoison:
    def test_effet_sets_poison_duration(self, caster, target, players):
        spell = Poison()
        spell.effet(caster, target, players)
        assert target.time_poison == spell.duree_poison

    def test_passive_ticks_down_and_damages_on_multiple_of_hundred(self, caster, target, players):
        spell = Poison()
        target.time_poison = 101  # devient 100, condition (%100==1) donc pas ce tour
        spell.passive(caster, target, players)
        assert target.time_poison == 100
        assert target.pv == target.pv_max

        target.time_poison = 2  # devient 1 -> déclenche les dégâts
        spell.passive(caster, target, players)
        assert target.time_poison == 1
        assert target.pv == target.pv_max - 25

    def test_passive_decrements_spell_cooldown(self, caster, target, players):
        spell = Poison()
        spell.time_cooldown = 3
        spell.passive(caster, target, players)
        assert spell.time_cooldown == 2


class TestVolDeVie:
    def test_effet(self, caster, target, players):
        caster.pv = 100
        VolDeVie().effet(caster, target, players)
        assert target.pv == target.pv_max - 1
        assert caster.pv == 101


class TestSoin:
    def test_effet_heals_and_clears_poison(self, caster, target, players):
        target.pv = 100
        target.time_poison = 500
        Soin().effet(caster, target, players)
        assert target.pv == 200
        assert target.time_poison == 0


class TestVitesse:
    def test_effet_halves_all_target_spell_cooldowns(self, caster, target, players):
        target.s = [Boule_feu(), Laser()]
        target.s[0].time_cooldown = 100
        target.s[1].time_cooldown = 7
        Vitesse().effet(caster, target, players)
        assert target.s[0].time_cooldown == 50
        assert target.s[1].time_cooldown == 3


class TestInterdiction:
    def test_effet_forbids_current_spell(self, caster, target, players):
        forbidden = Laser()
        target.spell = forbidden
        Interdiction().effet(caster, target, players)
        assert target.interdit is forbidden

    def test_effet_does_nothing_if_no_current_spell(self, caster, target, players):
        target.spell = None
        Interdiction().effet(caster, target, players)
        assert target.interdit is None


class TestLienSpirituel:
    def test_effet_creates_link_on_both_sides(self, caster, target, players):
        LienSpirituel().effet(caster, target, players)
        assert len(caster.linked) == 1
        assert len(target.linked) == 1
        assert caster.linked[0] == [800, caster, target]

    def test_passive_counts_down_and_expires(self, caster, target, players):
        spell = LienSpirituel()
        caster.linked.append([1, caster, target])
        target.linked.append([1, caster, target])
        spell.passive(caster, target, players)
        assert caster.linked == [[0, caster, target]]
        spell.passive(caster, target, players)
        assert caster.linked == []
        assert target.linked == []


class TestSilence:
    def test_effet(self, caster, target, players):
        Silence().effet(caster, target, players)
        assert target.time_silence == 400

    def test_passive_decrements_silence_and_cooldown(self, caster, target, players):
        spell = Silence()
        spell.time_cooldown = 2
        target.time_silence = 2
        spell.passive(caster, target, players)
        assert spell.time_cooldown == 1
        assert target.time_silence == 1


class TestRenvoi:
    def test_effet(self, caster, target, players):
        Renvoi().effet(caster, target, players)
        assert target.time_renvoi == 200

    def test_passive_decrements_renvoi_and_cooldown(self, caster, target, players):
        spell = Renvoi()
        spell.time_cooldown = 2
        target.time_renvoi = 2
        spell.passive(caster, target, players)
        assert spell.time_cooldown == 1
        assert target.time_renvoi == 1


class TestExodia:
    def test_effet_increments_counter_below_threshold(self, caster, target, players):
        spell = Exodia()
        spell.effet(caster, target, players)
        assert caster.nbr_exodia == 1
        assert target.pv == target.pv_max

    def test_effet_wipes_all_players_at_five_stacks(self, caster, target, players):
        # NB : effet() compare `player is not self` (self = l'objet Spell), qui est
        # toujours vrai pour un Sorcer -> tous les joueurs de `p` sont mis à 0 pv,
        # y compris le lanceur. Ce test documente le comportement actuel du code.
        ally = make_sorcer()
        enemy2 = make_sorcer()
        all_players = [caster, target, ally, enemy2]

        spell = Exodia()
        caster.nbr_exodia = 4
        spell.effet(caster, target, all_players)

        assert caster.nbr_exodia == 0
        assert target.pv == 0
        assert enemy2.pv == 0
        assert ally.pv == 0
        assert caster.pv == 0


class TestMultiplicateur:
    def test_effet_scales_damage_and_increments(self, caster, target, players):
        spell = Multiplicateur()
        assert caster.nbr_multiplicateur == 1
        spell.effet(caster, target, players)
        assert target.pv == target.pv_max - 40
        assert caster.nbr_multiplicateur == 2

        spell.effet(caster, target, players)
        assert target.pv == target.pv_max - 40 - 80
        assert caster.nbr_multiplicateur == 3


class TestTicTac:
    def test_effet_tic_deals_percentage_of_current_pv(self, caster, target, players):
        caster.tictac = "tic"
        target.pv = 300
        TicTac().effet(caster, target, players)
        assert target.pv == 300 - int(300 * 0.2)

    def test_effet_tac_deals_percentage_of_missing_pv(self, caster, target, players):
        caster.tictac = "tac"
        target.pv = 300
        target.pv_max = 800
        TicTac().effet(caster, target, players)
        assert target.pv == 300 - int((800 - 300) * 0.25)


class TestBalance:
    def test_effet_equalizes_toward_each_other(self, caster, target, players):
        caster.pv = 800
        target.pv = 200
        Balance().effet(caster, target, players)
        # l.dammage((l.pv - c.pv)/3) puis c.dammage((c.pv - l.pv)/3) avec c.pv déjà modifié entre-temps
        assert caster.pv == 800 - int((800 - 200) / 3)
        assert target.pv == 200 - int((200 - caster.pv) / 3)


class TestRenforcement:
    def test_effet_increases_max_pv_and_heals(self, caster, target, players):
        target.pv = 100
        target.pv_max = 800
        Renforcement().effet(caster, target, players)
        assert target.pv_max == 850
        assert target.pv == 125


class TestSpecialisation:
    def test_effet_marks_last_spell_and_cuts_its_cooldown(self, caster, target, players):
        last = Boule_feu()
        last.time_cooldown = 300
        caster.last_spell = last
        Specialisation().effet(caster, target, players)
        assert caster.spell_specialisation is last
        assert last.time_cooldown == 100

    def test_effet_does_nothing_without_last_spell(self, caster, target, players):
        caster.last_spell = None
        Specialisation().effet(caster, target, players)
        assert caster.spell_specialisation is None


class TestInvincibilite:
    def test_effet(self, caster, target, players):
        Invincibilite().effet(caster, target, players)
        assert target.time_invincibilite == 250

    def test_passive_decrements_and_blocks_damage(self, caster, target, players):
        spell = Invincibilite()
        target.time_invincibilite = 2
        spell.passive(caster, target, players)
        assert target.time_invincibilite == 1
        target.dammage(999)
        assert target.pv == target.pv_max


class TestTreve:
    def test_effet_affects_caster_not_target(self, caster, target, players):
        Treve().effet(caster, target, players)
        assert caster.time_treve == 300
        assert target.time_treve == 0

    def test_passive_decrements(self, caster, target, players):
        spell = Treve()
        caster.time_treve = 2
        spell.time_cooldown = 5
        spell.passive(caster, target, players)
        assert caster.time_treve == 1
        assert spell.time_cooldown == 4


class TestClone:
    def test_effet(self, caster, target, players):
        Clone().effet(caster, target, players)
        assert target.time_clone == 600

    def test_passive_decrements(self, caster, target, players):
        spell = Clone()
        target.time_clone = 2
        spell.passive(caster, target, players)
        assert target.time_clone == 1


class TestRetour:
    def test_full_cycle_restores_target_pv_after_delay(self, caster, target, players):
        spell = Retour()
        target.pv = 500  # PV au moment du lancement, doit être restauré

        for _ in range(max(spell.tc, 1)):
            spell.start(caster, target, players)
        assert spell.started
        assert target.vie_retour == 500

        target.dammage(400)
        assert target.pv == 100

        for _ in range(spell.d + 1):
            spell.action(caster, target, players)

        assert spell.ended
        assert target.pv == 500


class TestFlash:
    def test_effet(self, caster, target, players):
        Flash().effet(caster, target, players)
        assert target.pv == target.pv_max - 20


class TestCanon:
    def test_effet(self, caster, target, players):
        Canon().effet(caster, target, players)
        assert target.pv == target.pv_max - 200


class TestCoagulation:
    def test_effet(self, caster, target, players):
        target.pv = 100
        Coagulation().effet(caster, target, players)
        assert target.pv == 101


class TestRegeneration:
    def test_effet_sets_duration(self, caster, target, players):
        spell = Regeneration()
        spell.effet(caster, target, players)
        assert target.time_regeneration == spell.duree_regeneration

    def test_passive_heals_on_multiple_of_hundred(self, caster, target, players):
        spell = Regeneration()
        target.pv = 100
        target.time_regeneration = 2  # devient 1 -> soin
        spell.passive(caster, target, players)
        assert target.time_regeneration == 1
        assert target.pv == 120

    def test_passive_decrements_cooldown(self, caster, target, players):
        spell = Regeneration()
        spell.time_cooldown = 3
        spell.passive(caster, target, players)
        assert spell.time_cooldown == 2


class TestAnnulation:
    def test_effet_cancels_target_current_spell(self, caster, target, players):
        current = Laser()
        current.c = 999
        target.spell = current
        Annulation().effet(caster, target, players)
        assert current.time_cooldown == 999
        assert current.started is True
        assert current.ended is True

    def test_effet_does_nothing_without_current_spell(self, caster, target, players):
        target.spell = None
        Annulation().effet(caster, target, players)  # ne doit pas lever d'exception


class TestVolDeSort:
    def test_effet_swaps_spell_with_target(self, caster, target, players):
        stolen = Laser()
        target.spell = stolen
        target.s = [stolen]

        vol_de_sort = VolDeSort()
        caster.s = [vol_de_sort]

        vol_de_sort.effet(caster, target, players)

        assert target.s[0] is vol_de_sort
        assert isinstance(caster.s[0], Laser)
        assert target.spell is None
        assert target.busy is False

    def test_effet_does_nothing_without_target_spell(self, caster, target, players):
        target.spell = None
        vol_de_sort = VolDeSort()
        caster.s = [vol_de_sort]
        vol_de_sort.effet(caster, target, players)
        assert target.spell is None
        assert target.busy is False
        assert caster.s[0] is vol_de_sort


@pytest.fixture
def four_players():
    return [make_sorcer(), make_sorcer(), make_sorcer(), make_sorcer()]


class TestGetAlly:
    def test_pairs_consecutive_players(self, four_players):
        p1, p2, p3, p4 = four_players
        assert gp.get_ally(p1, four_players) is p2
        assert gp.get_ally(p2, four_players) is p1
        assert gp.get_ally(p3, four_players) is p4
        assert gp.get_ally(p4, four_players) is p3

    def test_returns_none_if_player_not_in_list(self, four_players):
        assert gp.get_ally(make_sorcer(), four_players) is None


class TestEarthquake:
    def test_effet_damages_every_player_including_caster(self, four_players):
        p1, p2, p3, p4 = four_players
        Earthquake().effet(p1, p2, four_players)
        for player in four_players:
            assert player.pv == player.pv_max - 50


class TestAcceleration:
    def test_effet_sets_flag_and_cancels_slow(self, caster, target, players):
        target.time_slow = 100
        spell = Acceleration()
        spell.effet(caster, target, players)
        assert target.time_acceleration == spell.duree_acceleration
        assert target.time_slow == 0

    def test_passive_decrements(self, caster, target, players):
        spell = Acceleration()
        target.time_acceleration = 2
        spell.passive(caster, target, players)
        assert target.time_acceleration == 1

    def test_doubles_cast_speed_and_halves_lag(self, caster, target, players):
        caster.time_acceleration = 100
        spell = Boule_feu()  # tc=100, d=1, tl=100

        for _ in range(int(spell.tc / 2)):
            spell.start(caster, target, players)
        assert spell.started

        for _ in range(spell.d + 1):
            spell.action(caster, target, players)
        assert spell.ended

        for _ in range(int(spell.tl / 2)):
            spell.end(caster, target, players)
        assert spell.time_cooldown == spell.c


class TestRalentissement:
    def test_effet_sets_flag_and_cancels_acceleration(self, caster, target, players):
        target.time_acceleration = 100
        spell = Ralentissement()
        spell.effet(caster, target, players)
        assert target.time_slow == spell.duree_slow
        assert target.time_acceleration == 0

    def test_passive_decrements(self, caster, target, players):
        spell = Ralentissement()
        target.time_slow = 2
        spell.passive(caster, target, players)
        assert target.time_slow == 1

    def test_halves_cast_speed(self, caster, target, players):
        caster.time_slow = 100
        spell = Boule_feu()  # tc=100

        for _ in range(199):
            spell.start(caster, target, players)
        assert not spell.started

        spell.start(caster, target, players)
        assert spell.started

    def test_doubles_cooldown_on_end(self, caster, target, players):
        caster.time_slow = 100
        spell = Flash()
        spell.started = True
        spell.ended = True
        spell.time_lag = spell.tl - 1

        spell.end(caster, target, players)

        assert spell.time_cooldown == spell.c * 2


class TestVolDeTemps:
    def test_effet_locks_unused_spells_and_refunds_caster(self, caster, target, players):
        ready = Laser()
        ready.time_cooldown = 0
        busy = Boule_feu()
        busy.time_cooldown = 50
        target.s = [ready, busy]

        own_spell = Flash()
        own_spell.time_cooldown = 150
        caster.s = [own_spell]

        VolDeTemps().effet(caster, target, players)

        assert ready.time_cooldown == ready.c
        assert busy.time_cooldown == 50
        assert own_spell.time_cooldown == 50


class TestReanimation:
    def test_effet_and_passive(self, caster, target, players):
        spell = Reanimation()
        spell.effet(caster, target, players)
        assert target.time_reanimation == spell.duree_reanimation

        target.time_reanimation = 2
        spell.passive(caster, target, players)
        assert target.time_reanimation == 1

    def test_revives_instead_of_dying_when_active(self, target):
        target.pv = 30
        target.time_reanimation = 100
        target.dammage(200)
        assert target.pv == int(target.pv_max / 3)
        assert target.time_reanimation == 0

    def test_dies_normally_without_reanimation(self, target):
        target.pv = 30
        target.dammage(200)
        assert target.pv == 0


class TestLagKick:
    def test_effet(self, caster, target, players):
        spell = LagKick()
        spell.effet(caster, target, players)
        assert target.time_lag_kick == spell.duree_lag_kick

    def test_passive_deals_damage_only_when_timer_reaches_zero(self, caster, target, players):
        spell = LagKick()
        target.time_lag_kick = 3

        spell.passive(caster, target, players)
        assert target.pv == target.pv_max
        spell.passive(caster, target, players)
        assert target.pv == target.pv_max
        spell.passive(caster, target, players)
        assert target.pv == target.pv_max - 150


class TestDeviation:
    def test_effet_and_passive(self, caster, target, players):
        spell = Deviation()
        spell.effet(caster, target, players)
        assert target.time_deviation == spell.duree_deviation
        assert target.deviation_cible is caster

        target.time_deviation = 1
        spell.passive(caster, target, players)
        assert target.time_deviation == 0
        assert target.deviation_cible is None

    def test_forces_target_via_loop(self):
        gp.start()
        gp.p2.time_deviation = 50
        gp.p2.deviation_cible = gp.p3
        gp.loop([";0", ";0", ";0", ";0"])
        assert gp.p2.cible is gp.p3


class TestBaffe:
    def test_effet(self, caster, target, players):
        Baffe().effet(caster, target, players)
        assert target.pv == target.pv_max - 10

    def test_has_a_low_cooldown_by_design(self):
        spell = Baffe()
        assert spell.c == int(gp.cooldown_base / 4)


class TestBouclier:
    def test_effet(self, caster, target, players):
        Bouclier().effet(caster, target, players)
        assert target.shield == 25
        assert target.time_shield == 300

    def test_shield_fully_absorbs_small_hit(self, target):
        target.shield = 25
        target.dammage(10)
        assert target.shield == 15
        assert target.pv == target.pv_max

    def test_shield_overflow_passes_through(self, target):
        target.shield = 25
        target.dammage(40)
        assert target.shield == 0
        assert target.pv == target.pv_max - 15

    def test_passive_expiry_clears_remaining_shield(self, target):
        spell = Bouclier()
        target.shield = 25
        target.time_shield = 1
        spell.passive(None, target, None)
        assert target.time_shield == 0
        assert target.shield == 0


class TestConcentrationMagique:
    def test_effet_damages_per_available_spell(self, caster, target, players):
        ready1 = Laser(); ready1.time_cooldown = 0
        ready2 = Flash(); ready2.time_cooldown = 0
        busy = Boule_feu(); busy.time_cooldown = 10
        target.s = [ready1, ready2, busy]

        ConcentrationMagique().effet(caster, target, players)

        assert target.pv == target.pv_max - 20


class TestPeineDeMort:
    def test_effet_sets_timer(self, caster, target, players):
        spell = PeineDeMort()
        spell.effet(caster, target, players)
        assert target.time_death_penalty == spell.duree_death_penalty

    def test_death_at_zero_when_undefended(self, caster, target, players):
        spell = PeineDeMort()
        target.time_death_penalty = 1
        spell.passive(caster, target, players)
        assert target.time_death_penalty == 0
        assert target.pv == 0

    def test_invincibility_prevents_death(self, caster, target, players):
        spell = PeineDeMort()
        target.time_death_penalty = 1
        target.time_invincibilite = 10
        spell.passive(caster, target, players)
        assert target.pv == target.pv_max

    def test_recast_resets_timer_and_prevents_scheduled_death(self, caster, target, players):
        spell = PeineDeMort()
        target.time_death_penalty = 1
        spell.effet(caster, target, players)  # relancé avant l'échéance -> réinitialise le délai
        spell.passive(caster, target, players)
        assert target.time_death_penalty == spell.duree_death_penalty - 1
        assert target.pv == target.pv_max

    def test_clean_removes_the_curse_entirely(self, caster, target, players):
        spell = PeineDeMort()
        target.time_death_penalty = 1
        Nettoyage().effet(caster, target, players)
        spell.passive(caster, target, players)
        assert target.pv == target.pv_max


class TestEsprit:
    def test_effet_scales_with_dead_players(self, four_players):
        p1, p2, p3, p4 = four_players
        p2.pv = 0
        p3.pv = 0
        Esprit().effet(p1, p4, four_players)
        assert p4.pv == p4.pv_max - 400


class TestDifference:
    def test_effet_damages_by_hp_gap_with_ally(self, four_players):
        p1, p2, p3, p4 = four_players
        p3.pv = 700
        p4.pv = 650
        Difference().effet(p1, p4, four_players)
        assert p4.pv == 600


class TestRayonDeSoleil:
    def test_first_cast_only_charges(self, caster, target, players):
        spell = RayonDeSoleil()
        spell.effet(caster, target, players)
        assert spell.charge is True
        assert target.pv == target.pv_max

    def test_second_cast_releases_the_damage(self, caster, target, players):
        spell = RayonDeSoleil()
        spell.effet(caster, target, players)
        spell.effet(caster, target, players)
        assert spell.charge is False
        assert target.pv == target.pv_max - 300


class TestConcentrationSorts:
    def test_effet_damages_per_spell_currently_being_cast(self, four_players):
        p1, p2, p3, p4 = four_players
        s1 = Laser(); s1.started = True; s1.ended = False
        p2.spell = s1
        s2 = Boule_feu(); s2.started = True; s2.ended = False
        p3.spell = s2

        ConcentrationSorts().effet(p1, p4, four_players)

        assert p4.pv == p4.pv_max - 200


class TestRepetition:
    def test_effet_retriggers_last_spell_effect(self, caster, target, players):
        caster.last_spell = Boule_feu()
        Repetition().effet(caster, target, players)
        assert caster.pv == caster.pv_max - 25
        assert target.pv == target.pv_max - 125

    def test_effet_does_nothing_without_last_spell(self, caster, target, players):
        caster.last_spell = None
        Repetition().effet(caster, target, players)
        assert caster.pv == caster.pv_max
        assert target.pv == target.pv_max


class TestImpatience:
    def test_effet(self, caster, target, players):
        s1 = Laser(); s1.time_cooldown = 150
        s2 = Boule_feu(); s2.time_cooldown = 250
        target.s = [s1, s2]

        Impatience().effet(caster, target, players)

        assert target.pv == target.pv_max - int(400 / 100)


class TestNettoyage:
    def test_effet_clears_status_effects(self, caster, target, players):
        target.time_poison = 10
        target.time_silence = 10
        target.shield = 25
        target.time_shield = 50
        target.time_death_penalty = 500
        target.interdit = Laser()
        target.linked = [[10, caster, target]]

        Nettoyage().effet(caster, target, players)

        assert target.time_poison == 0
        assert target.time_silence == 0
        assert target.shield == 0
        assert target.time_shield == 0
        assert target.time_death_penalty == 0
        assert target.interdit is None
        assert target.linked == []


class TestInversion:
    def test_effet_sets_duration(self, caster, target, players):
        spell = Inversion()
        spell.effet(caster, target, players)
        assert target.time_inversion == spell.duree_inversion

    def test_dammage_heals_while_inverted(self, target):
        target.pv = 500
        target.time_inversion = 10
        target.dammage(50)
        assert target.pv == 550

    def test_heal_damages_while_inverted(self, target):
        target.pv = 500
        target.time_inversion = 10
        target.heal(50)
        assert target.pv == 450


class TestProjectileMagique:
    def test_effet_damages_target_and_its_ally_only(self, four_players):
        p1, p2, p3, p4 = four_players
        ProjectileMagique().effet(p1, p4, four_players)
        assert p4.pv == p4.pv_max - 50
        assert p3.pv == p3.pv_max - 50
        assert p1.pv == p1.pv_max
        assert p2.pv == p2.pv_max


class TestCanalisation:
    def test_effet(self, caster, target, players):
        spell = Canalisation()
        spell.effet(caster, target, players)
        assert target.time_canalisation == spell.duree_canalisation

    def test_passive_heals_target_when_a_player_just_cast_a_spell(self, caster, target):
        spell = Canalisation()
        target.pv = 100
        target.time_canalisation = 10

        other = make_sorcer()
        casting = Laser()
        casting.started = True
        casting.duree = 1
        other.spell = casting

        spell.passive(caster, target, [caster, target, other])

        assert target.pv == 115
        assert target.time_canalisation == 9


class TestAveuglement:
    def test_effet_and_passive(self, caster, target, players):
        spell = Aveuglement()
        spell.effet(caster, target, players)
        assert target.time_aveuglement == spell.duree_aveuglement

        target.time_aveuglement = 2
        spell.passive(caster, target, players)
        assert target.time_aveuglement == 1

    def test_forces_self_targeting_via_loop(self):
        gp.start()
        gp.p2.time_aveuglement = 50
        gp.loop([";0", ";2", ";0", ";0"])
        assert gp.p2.cible is gp.p2


class TestTroc:
    def test_effet_gets_weaker_as_it_is_used_more(self, caster, target, players):
        Troc.utilisation_totale = 0
        spell = Troc()

        spell.effet(caster, target, players)
        assert Troc.utilisation_totale == 1
        assert target.pv == target.pv_max - 190

        spell.effet(caster, target, players)
        assert Troc.utilisation_totale == 2
        assert target.pv == target.pv_max - 190 - 180


class TestTempo:
    def test_effet_reduces_max_cooldown_with_a_floor(self, caster, target, players):
        high = Canon(); high.c = 2000
        low = Flash(); low.c = 500
        target.s = [high, low]

        Tempo().effet(caster, target, players)

        assert high.c == 1000
        assert low.c == 200


class TestProlongation:
    def test_effet_extends_only_currently_active_passives(self, caster, target, players):
        target.time_poison = 50
        target.time_silence = 0

        spell = Prolongation()
        spell.effet(caster, target, players)

        assert target.time_poison == 50 + spell.bonus_prolongation
        assert target.time_silence == 0


class TestMarque:
    def test_effet_and_passive(self, caster, target, players):
        spell = Marque()
        spell.effet(caster, target, players)
        assert target.time_marque == spell.duree_marque

        target.time_marque = 2
        spell.passive(caster, target, players)
        assert target.time_marque == 1

    def test_dammage_increased_by_20_percent_while_marked(self, target):
        target.pv = 500
        target.time_marque = 10
        target.dammage(100)
        assert target.pv == 500 - 120

    def test_dammage_unaffected_once_mark_expired(self, target):
        target.pv = 500
        target.time_marque = 0
        target.dammage(100)
        assert target.pv == 400

    def test_shield_absorbs_from_the_amplified_damage(self, target):
        target.pv = target.pv_max
        target.time_marque = 10
        target.shield = 25
        target.dammage(100)
        # 100 * 1.2 = 120 dégâts bruts, 25 absorbés par le bouclier -> 95 passent
        assert target.shield == 0
        assert target.pv == target.pv_max - 95

    def test_inversion_bypasses_the_mark_multiplier(self, target):
        target.pv = 500
        target.time_marque = 10
        target.time_inversion = 10
        target.dammage(100)
        assert target.pv == 600

    def test_prolongation_extends_active_mark(self, caster, target, players):
        target.time_marque = 50
        spell = Prolongation()
        spell.effet(caster, target, players)
        assert target.time_marque == 50 + spell.bonus_prolongation

    def test_nettoyage_clears_active_mark(self, caster, target, players):
        target.time_marque = 50
        Nettoyage().effet(caster, target, players)
        assert target.time_marque == 0


# ---------------------------------------------------------------------------
# Sanity check : tous les sorts déclarés dans gp.spells sont bien couverts
# ---------------------------------------------------------------------------

def test_all_spells_are_covered_by_a_test_class():
    tested = {
        Boule_feu, Laser, Poison, VolDeVie, Soin, Vitesse, Interdiction,
        LienSpirituel, Silence, Renvoi, Exodia, Multiplicateur, TicTac,
        Balance, Renforcement, Specialisation, Invincibilite, Treve, Clone,
        Retour, Flash, Canon, Coagulation, Regeneration, Annulation,
        VolDeSort, Earthquake,
        Acceleration, Ralentissement, VolDeTemps, Reanimation, LagKick, Deviation,
        Baffe, Bouclier, ConcentrationMagique, PeineDeMort, Esprit,
        Difference, RayonDeSoleil, ConcentrationSorts, Repetition, Impatience,
        Nettoyage, Inversion, ProjectileMagique, Canalisation, Aveuglement, Troc,
        Tempo, Prolongation, Marque,
    }
    assert set(gp.spells) == tested
