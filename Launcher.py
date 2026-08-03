import os
import sys
import subprocess
from pathlib import Path

import pygame


pygame.init()

WIDTH, HEIGHT = 980, 620
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Sorcer Launcher")

BASE_DIR = Path(__file__).resolve().parent
PYTHON_EXE = sys.executable
FPS = 60

BG = (20, 24, 32)
PANEL = (33, 39, 53)
PANEL_2 = (45, 52, 70)
TEXT = (235, 239, 247)
MUTED = (159, 171, 189)
GREEN = (59, 179, 126)
RED = (200, 79, 79)
BLUE = (66, 132, 245)
AMBER = (214, 167, 61)

font = pygame.font.SysFont("segoeui", 22)
small_font = pygame.font.SysFont("segoeui", 18)
title_font = pygame.font.SysFont("segoeui", 34, bold=True)


class InputBox:
    def __init__(self, rect, text):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.active = False

    def handle(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self.active = False
            elif len(self.text) < 40 and event.unicode.isprintable():
                self.text += event.unicode

    def draw(self, surface, label):
        pygame.draw.rect(surface, PANEL_2, self.rect, border_radius=8)
        border = BLUE if self.active else (72, 83, 104)
        pygame.draw.rect(surface, border, self.rect, width=2, border_radius=8)
        surface.blit(small_font.render(label, True, MUTED), (self.rect.x, self.rect.y - 22))
        surface.blit(font.render(self.text, True, TEXT), (self.rect.x + 10, self.rect.y + 8))


class Button:
    def __init__(self, rect, label, color, action):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.color = color
        self.action = action

    def click(self, pos):
        return self.rect.collidepoint(pos)

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self.rect, border_radius=10)
        pygame.draw.rect(surface, (255, 255, 255), self.rect, width=1, border_radius=10)
        txt = font.render(self.label, True, (250, 250, 250))
        tx = self.rect.x + (self.rect.width - txt.get_width()) // 2
        ty = self.rect.y + (self.rect.height - txt.get_height()) // 2
        surface.blit(txt, (tx, ty))


class ProcessGroup:
    def __init__(self):
        self.server = None
        self.bots = []
        self.clients = []

    def _spawn(self, script_name, args):
        script_path = BASE_DIR / script_name
        if not script_path.exists():
            raise FileNotFoundError(f"Missing script: {script_name}")

        cmd = [PYTHON_EXE, str(script_path)] + args
        creationflags = subprocess.CREATE_NEW_CONSOLE if os.name == "nt" else 0
        return subprocess.Popen(cmd, cwd=str(BASE_DIR), creationflags=creationflags)

    def cleanup_finished(self):
        self.bots = [p for p in self.bots if p.poll() is None]
        self.clients = [p for p in self.clients if p.poll() is None]
        if self.server is not None and self.server.poll() is not None:
            self.server = None

    def start_server(self, host, port):
        if self.server is not None and self.server.poll() is None:
            return "Server already running"
        self.server = self._spawn("Server.py", ["--host", host, "--port", str(port)])
        return "Server started"

    def stop_server(self):
        if self.server is None or self.server.poll() is not None:
            self.server = None
            return "No running server"
        self.server.terminate()
        self.server = None
        return "Server stop requested"

    def add_bot(self, host, port, idle=False):
        script = "Bot_void.py" if idle else "Bot.py"
        proc = self._spawn(script, ["--host", host, "--port", str(port)])
        self.bots.append(proc)
        return "Idle bot added" if idle else "Smart bot added"

    def add_client(self, host, port):
        proc = self._spawn("Client.py", ["--host", host, "--port", str(port)])
        self.clients.append(proc)
        return "Client launched"

    def stop_all_workers(self):
        for proc in self.bots + self.clients:
            if proc.poll() is None:
                proc.terminate()
        self.bots = []
        self.clients = []

    def stop_everything(self):
        self.stop_all_workers()
        if self.server is not None and self.server.poll() is None:
            self.server.terminate()
        self.server = None


processes = ProcessGroup()

host_input = InputBox((42, 136, 280, 44), "127.0.0.1")
port_input = InputBox((340, 136, 140, 44), "5000")

status_lines = [
    "Ready",
    "Tip: host 127.0.0.1 for local connection, 0.0.0.0 only for server bind.",
]


def set_status(message):
    status_lines.insert(0, message)
    del status_lines[6:]


def get_config():
    host = host_input.text.strip() or "127.0.0.1"
    try:
        port = int(port_input.text.strip())
    except ValueError:
        raise ValueError("Port must be an integer")
    if port < 1 or port > 65535:
        raise ValueError("Port must be between 1 and 65535")

    return host, port


buttons = [
    Button((42, 220, 280, 52), "Start Server", GREEN, "start_server"),
    Button((340, 220, 280, 52), "Stop Server", RED, "stop_server"),
    Button((638, 220, 280, 52), "Connect Client", BLUE, "connect_client"),
    Button((42, 290, 280, 52), "Add Smart Bot", AMBER, "add_bot"),
    Button((340, 290, 280, 52), "Add Idle Bot", AMBER, "add_idle_bot"),
    Button((638, 290, 280, 52), "Stop Bots/Clients", RED, "stop_workers"),
]

running = True
clock = pygame.time.Clock()

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            for button in buttons:
                if button.click(event.pos):
                    try:
                        host, port = get_config()
                        if button.action == "start_server":
                            set_status(processes.start_server("0.0.0.0", port))
                        elif button.action == "stop_server":
                            set_status(processes.stop_server())
                        elif button.action == "connect_client":
                            set_status(processes.add_client(host, port))
                        elif button.action == "add_bot":
                            set_status(processes.add_bot(host, port, idle=False))
                        elif button.action == "add_idle_bot":
                            set_status(processes.add_bot(host, port, idle=True))
                        elif button.action == "stop_workers":
                            processes.stop_all_workers()
                            set_status("All bots and clients stop requested")
                    except Exception as ex:
                        set_status(f"Error: {ex}")

        host_input.handle(event)
        port_input.handle(event)

    processes.cleanup_finished()

    SCREEN.fill(BG)

    pygame.draw.rect(SCREEN, PANEL, (24, 20, WIDTH - 48, HEIGHT - 40), border_radius=14)
    SCREEN.blit(title_font.render("Sorcer Control Center", True, TEXT), (42, 44))
    SCREEN.blit(small_font.render("Start a UDP server, spawn bots, and open game clients.", True, MUTED), (44, 86))

    host_input.draw(SCREEN, "Server host (for bots/clients)")
    port_input.draw(SCREEN, "Port")
    SCREEN.blit(small_font.render("Clients max : 4", True, MUTED), (500, 148))

    for button in buttons:
        button.draw(SCREEN)

    y = 374
    server_running = processes.server is not None and processes.server.poll() is None
    server_state = "RUNNING" if server_running else "STOPPED"
    server_color = GREEN if server_running else RED

    pygame.draw.rect(SCREEN, PANEL_2, (42, y, 876, 190), border_radius=12)
    SCREEN.blit(font.render("Runtime status", True, TEXT), (58, y + 16))
    SCREEN.blit(font.render(f"Server: {server_state}", True, server_color), (58, y + 52))
    SCREEN.blit(font.render(f"Bots running: {len(processes.bots)}", True, TEXT), (58, y + 84))
    SCREEN.blit(font.render(f"Clients running: {len(processes.clients)}", True, TEXT), (58, y + 116))

    SCREEN.blit(small_font.render("Recent messages:", True, MUTED), (370, y + 50))
    for i, line in enumerate(status_lines):
        SCREEN.blit(small_font.render(line, True, TEXT), (370, y + 78 + i * 24))

    pygame.display.flip()
    clock.tick(FPS)

processes.stop_everything()
pygame.quit()
