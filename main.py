import base64
import random
import time
import tkinter as tk
from dataclasses import dataclass, field
from pathlib import Path


WIDTH = 1000
HEIGHT = 650
FPS_MS = 33
ASSET_DIR = Path(__file__).resolve().parent / "assets"

ASSET_FILES = {
    "kaladin": "kaladin.png",
    "ponteiro": "ponteiro.png",
    "ponte": "ponte.png",
    "chao": "chao.png",
    "cratera": "cratera.png",
    "monstro_abismo": "monstro_abismo.png",
    "gema": "gema.png",
    "flecha": "flecha.png",
    "efeito_vento": "efeito_vento.png",
    "tempestade": "tempestade.png",
    "fundo": "fundo.png",
    "icone_jogo": "icone_jogo.png",
}

DIRECTIONS = {
    "Up": ("↑", "levantar"),
    "Down": ("↓", "firmar"),
    "Left": ("←", "esquerda"),
    "Right": ("→", "direita"),
}

PIXEL_COLORS = {
    "K": "#101112",
    "O": "#24201f",
    "H": "#38191c",
    "h": "#66292a",
    "S": "#f29a5b",
    "s": "#c7663f",
    "B": "#057cc2",
    "b": "#044c7a",
    "C": "#16c4ee",
    "W": "#f4f1e6",
    "G": "#496070",
    "g": "#283742",
    "L": "#7a3b29",
    "l": "#4a211b",
    "M": "#dce8ea",
    "R": "#ca1634",
    "Q": "#79f0ff",
}

KALADIN_SPRITE = [
    ".......KKKKKKK......",
    ".....KKHHHHHHHKK....",
    "....KHHHHHHHHHHHK...",
    "...KHHhHHHHhHHHHK...",
    "..KHHHHHHHHHHHHHHK..",
    "..KHHHSSSHHSSHHHHK..",
    ".KHHHSSSSSSSSHHHHK..",
    ".KHHSSSSSSSSSSSHHK..",
    ".KHHSSSSSSSSSSSHHK..",
    "..KHHSSSSSSSSHHHK...",
    "...KKHSSSSSSHHKK....",
    ".....KbbCCbbK.......",
    "....KbbBCCCbbK......",
    "...KbbbBCCCbbbK.....",
    "...KbbbBCCCbbbK.....",
    "...KbbBCCCCBbbK.....",
    "....KBBBBBBBBK......",
    "....KWWWWWWWK.......",
    "....KLLLLLLLK.......",
    "....KLK...KLK.......",
    "...KKLK...KLKK......",
    "...KLLK...KLLK......",
    "...KLLK...KLLK......",
    "...KKK.....KKK......",
]

BRIDGEMAN_SPRITE = [
    "....KKKKK....",
    "...KHHHHHK...",
    "..KHHHHHHHK..",
    "..KSSSSSSK...",
    "..KSSSSSSK...",
    "...KSSSSK....",
    "....KbbK.....",
    "...KbbbbK....",
    "..KbbGGbbK...",
    "..KbbGGbbK...",
    "..KbbbbbbK...",
    "...KLLLLK....",
    "...KL..LK....",
    "..KKL..LKK...",
    "..KLL..LLK...",
    "..KK....KK...",
]


@dataclass
class FallingArrow:
    x: float
    y: float
    speed: float
    symbol: str


@dataclass
class GameState:
    mode: str = "menu"
    craters_total: int = 8
    crater_index: int = 0
    sequence: list[str] = field(default_factory=list)
    sequence_cursor: int = 0
    event_kind: str = "crater"
    event_time: float = 0.0
    event_time_max: float = 0.0
    rivals_time: float = 92.0
    bridge_resistance: float = 100.0
    morale: float = 0.0
    wounds: float = 0.0
    combo: int = 0
    best_combo: int = 0
    wind_time: float = 0.0
    wind_ignore_error: bool = False
    feedback: str = ""
    feedback_color: str = "#f5e6a6"
    feedback_time: float = 0.0
    final_started: bool = False
    falling_arrows: list[FallingArrow] = field(default_factory=list)
    storm_phase: float = 0.0
    last_tick: float = field(default_factory=time.perf_counter)


class BridgeToGemGame:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("Ponte para a Gema")
        self.root.resizable(False, False)

        self.canvas = tk.Canvas(
            self.root,
            width=WIDTH,
            height=HEIGHT,
            bg="#15191d",
            highlightthickness=0,
        )
        self.canvas.pack()

        self.images = self.load_assets()
        if "icone_jogo" in self.images:
            self.root.iconphoto(False, self.images["icone_jogo"])

        self.state = GameState()
        self.root.bind("<KeyPress>", self.on_key_press)
        self.loop()

    def load_assets(self) -> dict[str, tk.PhotoImage]:
        images: dict[str, tk.PhotoImage] = {}
        for key, filename in ASSET_FILES.items():
            path = ASSET_DIR / filename
            if path.exists():
                image_data = base64.b64encode(path.read_bytes())
                images[key] = tk.PhotoImage(data=image_data)
        return images

    def start(self) -> None:
        self.root.mainloop()

    def reset_game(self) -> None:
        self.state = GameState(mode="playing", last_tick=time.perf_counter())
        self.make_next_event()

    def make_next_event(
        self,
        feedback: str | None = None,
        feedback_color: str = "#f5e6a6",
        feedback_time: float = 1.1,
    ) -> None:
        state = self.state
        progress = state.crater_index

        if state.crater_index >= state.craters_total:
            state.event_kind = "gem"
            state.final_started = True
            length = 10
            base_time = 8.0
        else:
            state.event_kind = "crater"
            length = 4 + progress // 2
            if progress >= 5:
                length += 1
            base_time = max(4.2, 8.2 - progress * 0.45)

        state.sequence = [random.choice(list(DIRECTIONS.keys())) for _ in range(length)]
        state.sequence_cursor = 0
        state.event_time_max = base_time + length * 0.45
        state.event_time = state.event_time_max
        state.feedback = feedback or ("Nova cratera!" if state.event_kind == "crater" else "A gema esta a frente!")
        state.feedback_color = feedback_color
        state.feedback_time = feedback_time

    def on_key_press(self, event: tk.Event) -> None:
        state = self.state
        key = event.keysym

        if state.mode == "menu":
            if key == "space":
                self.reset_game()
            return

        if state.mode in {"victory", "defeat"}:
            if key.lower() == "r" or key == "space":
                self.reset_game()
            return

        if key == "space":
            self.try_activate_wind()
            return

        if key not in DIRECTIONS:
            return

        expected = state.sequence[state.sequence_cursor]
        if key == expected:
            self.handle_correct_input()
        else:
            self.handle_wrong_input()

    def try_activate_wind(self) -> None:
        state = self.state
        if state.morale < 100 or state.wind_time > 0:
            return

        state.morale = 20
        state.wind_time = 8.0
        state.wind_ignore_error = True
        state.event_time = min(state.event_time_max * 1.25, state.event_time + 2.5)
        state.feedback = "Vento Protetor!"
        state.feedback_color = "#9be7ff"
        state.feedback_time = 1.4

    def handle_correct_input(self) -> None:
        state = self.state
        state.sequence_cursor += 1
        state.morale = min(100, state.morale + 3 + state.combo * 0.4)
        state.feedback = "Certo!"
        state.feedback_color = "#9df78f"
        state.feedback_time = 0.35

        if state.sequence_cursor >= len(state.sequence):
            self.complete_event()

    def handle_wrong_input(self) -> None:
        state = self.state

        if state.wind_time > 0 and state.wind_ignore_error:
            state.wind_ignore_error = False
            state.feedback = "O vento segurou o erro."
            state.feedback_color = "#9be7ff"
            state.feedback_time = 0.9
            return

        if state.event_kind == "gem":
            self.end_game("defeat", "A sequencia final falhou. Os rivais tomaram a gema.")
            return

        state.bridge_resistance = max(0, state.bridge_resistance - random.randint(8, 13))
        state.wounds = min(100, state.wounds + random.randint(7, 12))
        state.rivals_time = max(0, state.rivals_time - 3.5)
        state.combo = 0
        state.morale = max(0, state.morale - 12)
        self.make_next_event("Erro! A ponte sofreu.", "#ff8f8f", 1.0)

    def complete_event(self) -> None:
        state = self.state

        if state.event_kind == "gem":
            self.end_game("victory", "Kaladin alcancou a gema do monstro do abismo!")
            return

        state.crater_index += 1
        state.combo += 1
        state.best_combo = max(state.best_combo, state.combo)
        state.morale = min(100, state.morale + 12 + state.combo * 2)
        state.rivals_time = min(92, state.rivals_time + 1.4)
        self.make_next_event("Ponte colocada. Avancem!", "#f5e6a6", 0.9)

    def fail_event_by_time(self) -> None:
        state = self.state
        if state.event_kind == "gem":
            self.end_game("defeat", "A gema brilhou perto demais, mas o tempo acabou.")
            return

        state.bridge_resistance = max(0, state.bridge_resistance - 10)
        state.wounds = min(100, state.wounds + 10)
        state.rivals_time = max(0, state.rivals_time - 5)
        state.combo = 0
        self.make_next_event("Demorou demais!", "#ffbc75", 1.0)

    def end_game(self, mode: str, message: str) -> None:
        self.state.mode = mode
        self.state.feedback = message
        self.state.feedback_color = "#9df78f" if mode == "victory" else "#ff8f8f"
        self.state.feedback_time = 10

    def update(self, dt: float) -> None:
        state = self.state
        if state.mode != "playing":
            return

        wind_factor = 0.52 if state.wind_time > 0 else 1.0
        state.rivals_time -= dt * wind_factor
        state.event_time -= dt * wind_factor
        state.feedback_time = max(0, state.feedback_time - dt)
        state.wind_time = max(0, state.wind_time - dt)
        state.storm_phase += dt

        if state.event_time <= 0:
            self.fail_event_by_time()

        if state.rivals_time <= 0:
            self.end_game("defeat", "Os outros exercitos chegaram primeiro.")
        elif state.bridge_resistance <= 0:
            self.end_game("defeat", "A ponte quebrou nas Planicies Fragmentadas.")
        elif state.wounds >= 100:
            self.end_game("defeat", "Os ponteiros nao conseguem continuar.")

        self.update_falling_arrows(dt)

    def update_falling_arrows(self, dt: float) -> None:
        state = self.state
        intensity = state.crater_index / max(1, state.craters_total)
        spawn_chance = 0.015 + intensity * 0.035
        if state.crater_index >= 3 and random.random() < spawn_chance:
            state.falling_arrows.append(
                FallingArrow(
                    x=random.randint(80, WIDTH - 80),
                    y=-20,
                    speed=random.uniform(110, 210 + intensity * 120),
                    symbol=random.choice(["↓", "↘", "↙"]),
                )
            )

        for arrow in state.falling_arrows:
            arrow.y += arrow.speed * dt
        state.falling_arrows = [arrow for arrow in state.falling_arrows if arrow.y < HEIGHT + 40]

    def loop(self) -> None:
        now = time.perf_counter()
        dt = now - self.state.last_tick
        self.state.last_tick = now
        self.update(min(dt, 0.08))
        self.draw()
        self.root.after(FPS_MS, self.loop)

    def draw(self) -> None:
        self.canvas.delete("all")
        if self.state.mode == "menu":
            self.draw_menu()
        else:
            self.draw_scene()
            if self.state.mode in {"victory", "defeat"}:
                self.draw_end_overlay()

    def draw_menu(self) -> None:
        c = self.canvas
        self.draw_background()
        c.create_text(
            WIDTH // 2,
            115,
            text="Ponte para a Gema",
            fill="#f5e6a6",
            font=("Segoe UI", 42, "bold"),
        )
        c.create_text(
            WIDTH // 2,
            175,
            text="Conduza Kaladin pelas crateras antes que os rivais cheguem.",
            fill="#d4dddf",
            font=("Segoe UI", 16),
        )
        c.create_text(
            WIDTH // 2,
            260,
            text="↑ levantar   ↓ firmar   ← esquerda   → direita",
            fill="#eef7f4",
            font=("Segoe UI", 21, "bold"),
        )
        c.create_text(
            WIDTH // 2,
            308,
            text="Espaco ativa o Vento Protetor quando a moral estiver cheia.",
            fill="#9be7ff",
            font=("Segoe UI", 15),
        )
        c.create_text(
            WIDTH // 2,
            410,
            text="Pressione Espaco",
            fill="#ffffff",
            font=("Segoe UI", 26, "bold"),
        )
        self.draw_bridge_team(0.0)

    def draw_scene(self) -> None:
        self.draw_background()
        self.draw_world()
        self.draw_hud()
        self.draw_sequence()
        self.draw_feedback()
        self.draw_falling_arrows()
        self.draw_storm()

    def draw_background(self) -> None:
        c = self.canvas
        if "fundo" in self.images:
            c.create_image(0, 0, image=self.images["fundo"], anchor="nw")
            return

        c.create_rectangle(0, 0, WIDTH, HEIGHT, fill="#15191d", outline="")
        c.create_rectangle(0, 0, WIDTH, 190, fill="#202a30", outline="")
        for i in range(18):
            x = i * 72 - 30
            c.create_polygon(
                x,
                190,
                x + 70,
                92 + (i % 4) * 15,
                x + 150,
                190,
                fill="#2f3838",
                outline="#3d4743",
            )

    def draw_world(self) -> None:
        c = self.canvas
        state = self.state
        progress = state.crater_index / max(1, state.craters_total)

        if "chao" in self.images:
            c.create_image(0, 430, image=self.images["chao"], anchor="nw")
        else:
            c.create_rectangle(0, 430, WIDTH, HEIGHT, fill="#5a5143", outline="")

        for i in range(7):
            x = 80 + i * 145 - progress * 60
            if "cratera" in self.images:
                c.create_image(x + 58, 522, image=self.images["cratera"], anchor="center")
            else:
                c.create_oval(x, 458, x + 115, 585, fill="#211d1c", outline="#7d6f5c", width=3)

        if state.final_started or state.crater_index >= state.craters_total - 1:
            if "monstro_abismo" in self.images:
                c.create_image(830, 382, image=self.images["monstro_abismo"], anchor="center")
            else:
                c.create_oval(710, 272, 960, 505, fill="#33292a", outline="#69574e", width=4)

            if "gema" in self.images:
                c.create_image(850, 372, image=self.images["gema"], anchor="center")
            else:
                c.create_oval(815, 340, 882, 407, fill="#33e6b5", outline="#d9fff2", width=5)

        self.draw_bridge_team(progress)

    def draw_pixel_sprite(self, sprite: list[str], x: float, y: float, scale: int, palette_shift: dict[str, str] | None = None) -> None:
        c = self.canvas
        colors = PIXEL_COLORS | (palette_shift or {})
        for row, line in enumerate(sprite):
            for col, key in enumerate(line):
                if key == ".":
                    continue
                color = colors.get(key)
                if not color:
                    continue
                x1 = x + col * scale
                y1 = y + row * scale
                c.create_rectangle(x1, y1, x1 + scale, y1 + scale, fill=color, outline=color)

    def draw_pixel_shadow(self, x: float, y: float, width: float, height: float) -> None:
        self.canvas.create_rectangle(x, y, x + width, y + height, fill="#111312", outline="")
        self.canvas.create_rectangle(x + width * 0.12, y + height, x + width * 0.88, y + height + 7, fill="#111312", outline="")

    def draw_pixel_bridge(self, x: float, y: float, width: float) -> None:
        c = self.canvas
        c.create_rectangle(x, y, x + width, y + 14, fill="#8b623e", outline="#2a1b13", width=2)
        c.create_rectangle(x, y + 14, x + width, y + 22, fill="#5a3927", outline="")
        for brace_x in range(int(x) + 18, int(x + width) - 20, 38):
            c.create_rectangle(brace_x, y - 3, brace_x + 12, y + 25, fill="#6d472e", outline="#2a1b13")
        c.create_rectangle(x - 16, y + 6, x, y + 18, fill="#3d2a20", outline="")
        c.create_rectangle(x + width, y + 6, x + width + 16, y + 18, fill="#3d2a20", outline="")

    def draw_kaladin_sprite(self, x: float, ground_y: float, wind_active: bool) -> None:
        c = self.canvas
        if "kaladin" in self.images:
            top = ground_y - self.images["kaladin"].height()
            self.draw_pixel_shadow(x + 14, ground_y - 4, self.images["kaladin"].width() - 24, 11)
            if wind_active and "efeito_vento" in self.images:
                c.create_image(x + 64, top + 62, image=self.images["efeito_vento"], anchor="center")
            c.create_image(x, top, image=self.images["kaladin"], anchor="nw")
            c.create_text(
                x + self.images["kaladin"].width() / 2,
                ground_y + 24,
                text="Kaladin",
                fill="#eef7f4",
                font=("Segoe UI", 11, "bold"),
            )
            return

        scale = 4
        sprite_width = len(KALADIN_SPRITE[0]) * scale
        sprite_height = len(KALADIN_SPRITE) * scale
        top = ground_y - sprite_height

        self.draw_pixel_shadow(x - 10, ground_y - 4, sprite_width + 26, 11)

        weapon_y = top + 58
        c.create_rectangle(x - 31, weapon_y, x + 98, weapon_y + 8, fill="#1d2636", outline="#0c1118")
        c.create_rectangle(x + 35, weapon_y, x + 67, weapon_y + 8, fill="#6b7182", outline="")
        c.create_rectangle(x + 88, weapon_y - 10, x + 104, weapon_y + 18, fill="#f2f7f4", outline="#0c1118")
        c.create_rectangle(x + 77, weapon_y - 2, x + 90, weapon_y + 10, fill="#ca1634", outline="")
        c.create_rectangle(x + 104, weapon_y + 1, x + 118, weapon_y + 7, fill="#101112", outline="")
        c.create_rectangle(x - 43, weapon_y + 1, x - 30, weapon_y + 7, fill="#101112", outline="")

        self.draw_pixel_sprite(KALADIN_SPRITE, x, top, scale)

        if wind_active:
            for dx, dy, size in [(-8, 8, 8), (74, -18, 10), (90, 18, 7), (10, -14, 6)]:
                c.create_rectangle(x + dx, top + dy, x + dx + size, top + dy + size, fill="#79f0ff", outline="")
            c.create_line(x - 20, top + 18, x + 92, top - 8, fill="#79f0ff", width=3)
            c.create_line(x - 28, top + 84, x + 106, top + 38, fill="#79f0ff", width=2)

        c.create_text(
            x + sprite_width / 2,
            ground_y + 24,
            text="Kaladin",
            fill="#eef7f4",
            font=("Segoe UI", 11, "bold"),
        )

    def draw_bridgeman_sprite(self, x: float, ground_y: float, palette_shift: dict[str, str]) -> None:
        if "ponteiro" in self.images:
            sprite = self.images["ponteiro"]
            self.draw_pixel_shadow(x + 8, ground_y - 2, sprite.width() - 16, 7)
            self.canvas.create_image(x, ground_y - sprite.height(), image=sprite, anchor="nw")
            return

        scale = 3
        sprite_height = len(BRIDGEMAN_SPRITE) * scale
        sprite_width = len(BRIDGEMAN_SPRITE[0]) * scale
        self.draw_pixel_shadow(x - 3, ground_y - 2, sprite_width + 6, 7)
        self.draw_pixel_sprite(BRIDGEMAN_SPRITE, x, ground_y - sprite_height, scale, palette_shift)

    def draw_bridge_team(self, progress: float) -> None:
        x = 118 + progress * 525
        ground_y = 438
        bob = 2 if int(self.state.storm_phase * 6) % 2 == 0 else 0

        if "ponte" in self.images:
            self.canvas.create_image(x - 60, ground_y - 124 + bob, image=self.images["ponte"], anchor="nw")
        else:
            self.draw_pixel_bridge(x - 58, ground_y - 86 + bob, 314)

        crew_palettes = [
            {"B": "#0f6fa4", "b": "#064466", "H": "#2e1b17"},
            {"B": "#3f5f73", "b": "#263d4a", "H": "#4a251c"},
            {"B": "#146c81", "b": "#0d4050", "H": "#1f1816"},
            {"B": "#59606d", "b": "#363b46", "H": "#512721"},
            {"B": "#0c7f9e", "b": "#075061", "H": "#31201d"},
        ]
        for i, palette in enumerate(crew_palettes):
            px = x + 82 + i * 38
            self.draw_bridgeman_sprite(px, ground_y - 4 + (i % 2) * 2, palette)

        self.draw_kaladin_sprite(x - 44, ground_y + bob, self.state.wind_time > 0)

    def draw_hud(self) -> None:
        state = self.state
        self.draw_bar(28, 26, 286, 46, state.rivals_time / 92, "#f4b860", "Tempo ate os rivais")
        self.draw_bar(28, 70, 286, 90, state.bridge_resistance / 100, "#8fd18a", "Resistencia da ponte")
        self.draw_bar(714, 26, 972, 46, state.morale / 100, "#74d9ff", "Moral")
        self.draw_bar(714, 70, 972, 90, state.wounds / 100, "#ed7777", "Ferimentos")

        c = self.canvas
        c.create_text(
            WIDTH // 2,
            37,
            text=f"Crateras: {min(state.crater_index, state.craters_total)}/{state.craters_total}",
            fill="#eef7f4",
            font=("Segoe UI", 18, "bold"),
        )
        c.create_text(
            WIDTH // 2,
            75,
            text=f"Combo {state.combo}  |  Melhor {state.best_combo}",
            fill="#f5e6a6",
            font=("Segoe UI", 14, "bold"),
        )

        event_ratio = max(0, state.event_time / max(0.1, state.event_time_max))
        self.draw_bar(300, 113, 700, 133, event_ratio, "#f5e6a6", "Evento")

        if state.wind_time > 0:
            c.create_text(
                WIDTH // 2,
                158,
                text=f"Vento Protetor {state.wind_time:0.1f}s",
                fill="#9be7ff",
                font=("Segoe UI", 15, "bold"),
            )
        elif state.morale >= 100:
            c.create_text(
                WIDTH // 2,
                158,
                text="Vento Protetor pronto",
                fill="#9be7ff",
                font=("Segoe UI", 15, "bold"),
            )

    def draw_bar(self, x1: int, y1: int, x2: int, y2: int, ratio: float, color: str, label: str) -> None:
        c = self.canvas
        ratio = max(0, min(1, ratio))
        c.create_rectangle(x1, y1, x2, y2, fill="#273036", outline="#8a9698")
        c.create_rectangle(x1 + 2, y1 + 2, x1 + 2 + (x2 - x1 - 4) * ratio, y2 - 2, fill=color, outline="")
        c.create_text(x1, y1 - 4, text=label, anchor="sw", fill="#ccd7d8", font=("Segoe UI", 9, "bold"))

    def draw_sequence(self) -> None:
        state = self.state
        c = self.canvas
        start_x = WIDTH // 2 - (len(state.sequence) * 64) // 2
        y = 230

        for index, direction in enumerate(state.sequence):
            symbol = DIRECTIONS[direction][0]
            x = start_x + index * 64
            done = index < state.sequence_cursor
            current = index == state.sequence_cursor

            if state.wind_time > 0:
                fill = "#d9fff2" if current else "#496c74"
                outline = "#9be7ff"
            elif done:
                fill = "#42583d"
                outline = "#9df78f"
            elif current:
                fill = "#f5e6a6"
                outline = "#ffffff"
            else:
                fill = "#2b3439"
                outline = "#8a9698"

            c.create_rectangle(x, y, x + 52, y + 58, fill=fill, outline=outline, width=3)
            c.create_text(
                x + 26,
                y + 28,
                text=symbol,
                fill="#101617" if current else "#eef7f4",
                font=("Segoe UI", 28, "bold"),
            )

        if state.crater_index >= 6 and state.mode == "playing":
            self.draw_fake_commands(start_x, y + 78)

    def draw_fake_commands(self, start_x: int, y: int) -> None:
        c = self.canvas
        fake_rng = random.Random(self.state.crater_index * 99 + int(self.state.event_time * 10))
        for i in range(4):
            x = start_x + i * 82 + 18
            symbol = fake_rng.choice(["↑", "↓", "←", "→"])
            c.create_text(x, y, text=symbol, fill="#7a5555", font=("Segoe UI", 24, "bold"))

    def draw_feedback(self) -> None:
        state = self.state
        if state.feedback and state.feedback_time > 0:
            self.canvas.create_text(
                WIDTH // 2,
                327,
                text=state.feedback,
                fill=state.feedback_color,
                font=("Segoe UI", 19, "bold"),
            )

    def draw_falling_arrows(self) -> None:
        c = self.canvas
        for arrow in self.state.falling_arrows:
            if "flecha" in self.images:
                c.create_image(arrow.x, arrow.y, image=self.images["flecha"], anchor="center")
            else:
                c.create_text(
                    arrow.x,
                    arrow.y,
                    text=arrow.symbol,
                    fill="#c7d6d8",
                    font=("Segoe UI", 24, "bold"),
                )

    def draw_storm(self) -> None:
        state = self.state
        if state.crater_index < 5 or state.mode != "playing":
            return

        c = self.canvas
        if "tempestade" in self.images:
            offset = int((state.storm_phase * 80) % WIDTH)
            c.create_image(-offset, 0, image=self.images["tempestade"], anchor="nw")
            c.create_image(WIDTH - offset, 0, image=self.images["tempestade"], anchor="nw")
            return

        alpha_color = "#6d7475" if state.wind_time <= 0 else "#8bdfff"
        offset = int((state.storm_phase * 130) % 90)
        for i in range(-2, 15):
            x = i * 90 + offset
            c.create_line(x, 185, x - 140, 540, fill=alpha_color, width=2)

    def draw_end_overlay(self) -> None:
        state = self.state
        c = self.canvas
        c.create_rectangle(0, 0, WIDTH, HEIGHT, fill="#0d1012", stipple="gray50", outline="")
        title = "Vitoria" if state.mode == "victory" else "Derrota"
        color = "#9df78f" if state.mode == "victory" else "#ff8f8f"
        c.create_text(WIDTH // 2, 220, text=title, fill=color, font=("Segoe UI", 48, "bold"))
        c.create_text(WIDTH // 2, 290, text=state.feedback, fill="#eef7f4", font=("Segoe UI", 18, "bold"))
        c.create_text(
            WIDTH // 2,
            350,
            text=f"Crateras {min(state.crater_index, state.craters_total)}/{state.craters_total}  |  Melhor combo {state.best_combo}",
            fill="#f5e6a6",
            font=("Segoe UI", 16),
        )
        c.create_text(WIDTH // 2, 430, text="Pressione R ou Espaco", fill="#ffffff", font=("Segoe UI", 24, "bold"))


if __name__ == "__main__":
    BridgeToGemGame().start()
