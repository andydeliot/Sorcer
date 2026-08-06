from Gameplay import Sorcer, spells
import socket
import pickle
import struct
import threading
import argparse
import time
from typing import Dict, List, Optional, Tuple


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sorcer smart bot")
    parser.add_argument("--host", default="127.0.0.1", help="Server host")
    parser.add_argument("--port", type=int, default=5000, help="Server port")
    parser.add_argument("--tick", type=float, default=0.08, help="Decision tick in seconds")
    return parser.parse_args()


args = parse_args()
HOST = args.host
PORT = args.port
TICK_SECONDS = max(0.03, float(args.tick))

client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client.connect((HOST, PORT))

state_lock = threading.Lock()
players_state = [Sorcer(spells), Sorcer(spells), Sorcer(spells), Sorcer(spells)]
last_state_ts = 0.0


def send_obj(obj: str) -> None:
    data = pickle.dumps(obj)
    size = struct.pack("!I", len(data))
    client.sendto(size + data, (HOST, PORT))


def recv_loop() -> None:
    global players_state, last_state_ts
    while True:
        try:
            data, _ = client.recvfrom(65536)
            size = struct.unpack("!I", data[:4])[0]
            payload = pickle.loads(data[4:4 + size])
            new_players = None
            if isinstance(payload, dict):
                maybe_players = payload.get("players")
                if isinstance(maybe_players, list) and len(maybe_players) == 4:
                    new_players = maybe_players
            elif isinstance(payload, list) and len(payload) == 4:
                new_players = payload

            if new_players is not None:
                with state_lock:
                    players_state = new_players
                    last_state_ts = time.time()
        except Exception:
            # Keep bot alive even if one packet is malformed.
            continue


threading.Thread(target=recv_loop, daemon=True).start()


def spell_map(player) -> Dict[str, Tuple[int, object]]:
    mapping: Dict[str, Tuple[int, object]] = {}
    for idx, spell in enumerate(player.s):
        mapping[spell.n] = (idx, spell)
    return mapping


def choose_lowest_hp(players: List[object], indexes: List[int]) -> Optional[int]:
    alive = [i for i in indexes if players[i].pv > 0]
    if not alive:
        return None
    return min(alive, key=lambda i: players[i].pv)


def choose_highest_threat_enemy(players: List[object], indexes: List[int]) -> Optional[int]:
    alive = [i for i in indexes if players[i].pv > 0]
    if not alive:
        return None

    def threat_score(i: int) -> Tuple[int, int, int]:
        enemy = players[i]
        has_spell = 1 if enemy.spell is not None else 0
        started = 1 if (enemy.spell is not None and getattr(enemy.spell, "started", False)) else 0
        near_release = 0
        if enemy.spell is not None:
            tc = max(1, int(getattr(enemy.spell, "tc", 1)))
            charge = int(getattr(enemy.spell, "time_charge", 0))
            near_release = 1 if charge >= int(tc * 0.6) else 0
        return (has_spell, started + near_release, enemy.pv_max - enemy.pv)

    return max(alive, key=threat_score)


def target_not_countered(players: List[object], preferred: int) -> Optional[int]:
    if players[preferred].pv <= 0:
        return None
    if getattr(players[preferred], "time_renvoi", 0) <= 0:
        return preferred

    enemies = [2, 3]
    alternatives = [i for i in enemies if players[i].pv > 0 and getattr(players[i], "time_renvoi", 0) <= 0]
    if alternatives:
        return min(alternatives, key=lambda i: players[i].pv)
    return preferred


def choose_command(players: List[object]) -> str:
    me = players[0]
    ally = players[1]

    # Keep the round active but avoid trying to cast when we cannot.
    keepalive_target = 2 if players[2].pv > 0 else 3
    keepalive_target = keepalive_target if players[keepalive_target].pv > 0 else 0

    if me.pv <= 0:
        return f";{keepalive_target}"
    if me.spell is not None:
        return f";{keepalive_target}"
    if me.time_silence > 0:
        return f";{keepalive_target}"
    if any(p.time_treve > 0 for p in players):
        return f";{keepalive_target}"

    sm = spell_map(me)

    def ready(name: str) -> bool:
        pair = sm.get(name)
        return pair is not None and pair[1].time_cooldown <= 0 and pair[1] is not me.interdit

    def cast(name: str, target_idx: int) -> Optional[str]:
        pair = sm.get(name)
        if pair is None:
            return None
        idx, spell = pair
        if spell.time_cooldown > 0 or spell is me.interdit:
            return None
        if target_idx < 0 or target_idx >= len(players) or players[target_idx].pv <= 0:
            return None
        return f"{idx};{target_idx}"

    enemy_low = choose_lowest_hp(players, [2, 3])
    enemy_threat = choose_highest_threat_enemy(players, [2, 3])
    ally_low = choose_lowest_hp(players, [0, 1])

    if enemy_low is None:
        return f";0"

    my_hp_ratio = me.pv / max(1, me.pv_max)
    ally_hp_ratio = ally.pv / max(1, ally.pv_max)
    enemy_low_hp_ratio = players[enemy_low].pv / max(1, players[enemy_low].pv_max)

    # 1) Emergency survival.
    if my_hp_ratio < 0.30:
        for spell_name in ["Invincibility", "Heal", "Shield", "Reanimation", "Regeneration", "Coagulation", "Truce", "Life steal"]:
            if ready(spell_name):
                cmd = cast(spell_name, 0)
                if cmd is not None:
                    return cmd

    # 2) Ally stabilization.
    if ally_hp_ratio < 0.35 and ally_low is not None:
        for spell_name in ["Invincibility", "Heal", "Shield", "Reanimation", "Regeneration", "Coagulation"]:
            if ready(spell_name):
                cmd = cast(spell_name, 1)
                if cmd is not None:
                    return cmd

    # 3) Interrupt dangerous enemy casts first.
    if enemy_threat is not None and players[enemy_threat].spell is not None:
        for spell_name in ["Cancelation", "Interdiction", "Silence", "Blindness", "Deviation", "Slow"]:
            if ready(spell_name):
                cmd = cast(spell_name, enemy_threat)
                if cmd is not None:
                    return cmd

    # 4) Offensive setup debuffs.
    if enemy_low is not None:
        if ready("Mark") and players[enemy_low].time_marque <= 0:
            cmd = cast("Mark", enemy_low)
            if cmd is not None:
                return cmd
        if ready("Poison") and players[enemy_low].time_poison <= 0:
            cmd = cast("Poison", enemy_low)
            if cmd is not None:
                return cmd
        if ready("Slow") and players[enemy_low].time_slow <= 0:
            cmd = cast("Slow", enemy_low)
            if cmd is not None:
                return cmd

    # 5) Finisher logic.
    if enemy_low_hp_ratio <= 0.12 and ready("Flash"):
        safe_target = target_not_countered(players, enemy_low)
        if safe_target is not None:
            cmd = cast("Flash", safe_target)
            if cmd is not None:
                return cmd

    # 6) Buff self for stronger exchanges.
    for spell_name in ["Speed up", "Puissance", "Magic concentration", "Shield", "Spell concentration"]:
        if ready(spell_name):
            cmd = cast(spell_name, 0)
            if cmd is not None:
                return cmd

    # 7) Main damage rotation.
    for spell_name in [
        "Cannon",
        "Fireball",
        "Magic projectile",
        "Sun ray",
        "Earthquake",
        "Laser",
        "Life steal",
        "Multiplier",
        "Quick slap",
        "TicTac",
        "Balance",
        "Difference",
        "Trade",
    ]:
        if ready(spell_name):
            safe_target = target_not_countered(players, enemy_low)
            if safe_target is None:
                safe_target = enemy_low
            # Fireball has recoil, avoid suicidal casts.
            if spell_name == "Fireball" and me.pv <= 70:
                continue
            cmd = cast(spell_name, safe_target)
            if cmd is not None:
                return cmd

    # 8) Utility / opportunistic casts.
    for spell_name in ["Tempo", "Specialisation", "Repeat", "Inversion", "Channeling", "Clean", "Spiritual link", "Prolongation", "Death penalty"]:
        if ready(spell_name):
            target_idx = enemy_low if spell_name not in {"Specialisation", "Nettoyage"} else 0
            cmd = cast(spell_name, target_idx)
            if cmd is not None:
                return cmd

    # 9) Last fallback: cast first ready spell on lowest enemy.
    for idx, spell in enumerate(me.s):
        if spell.time_cooldown <= 0 and spell is not me.interdit:
            safe_target = target_not_countered(players, enemy_low)
            if safe_target is None:
                safe_target = enemy_low
            return f"{idx};{safe_target}"

    return f";{keepalive_target}"


last_send = 0.0
while True:
    now = time.time()
    if now - last_send >= TICK_SECONDS:
        with state_lock:
            snapshot = list(players_state)
        command = choose_command(snapshot)
        send_obj(command)
        last_send = now
    time.sleep(0.01)
