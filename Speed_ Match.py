# -*- coding: utf-8 -*-
"""
Speed Match - Lumosity-style
Start screen + Loading screen matching official screenshots
"""

import customtkinter as ctk
import random
import math
import json
import os
from typing import Optional

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

SAVE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.json")

DURATION = 45
BASE_POINTS = 50
MAX_MULT = 10
COMBO_NEED = 4

SYMBOLS = ["circle", "square", "triangle", "diamond", "star", "hexagon", "cross", "ring"]
COLORS = [
    "#E53935", "#43A047", "#1E88E5", "#FDD835",
    "#8E24AA", "#FB8C00", "#00ACC1", "#D81B60",
]


class Card:
    def __init__(self, symbol: str, color: str):
        self.symbol = symbol
        self.color = color

    def matches(self, other: Optional["Card"]) -> bool:
        if other is None:
            return False
        return self.symbol == other.symbol and self.color == other.color


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Speed Match")
        self.geometry("720x520")
        self.resizable(False, False)
        self.configure(fg_color="#0A4A8A")

        self.settings = self.load_settings()
        self.sound_on = self.settings.get("sound", True)
        self.music_on = self.settings.get("music", False)
        self.best_score = self.settings.get("best_score", 0)

        self.score = 0
        self.mult = 1
        self.combo = 0
        self.correct = 0
        self.wrong = 0
        self.max_mult = 1
        self.time_left = float(DURATION)
        self.playing = False
        self.paused = False
        self.can_answer = False
        self.prev: Optional[Card] = None
        self.curr: Optional[Card] = None
        self.timer_id = None
        self.count_id = None
        self.load_id = None

        self._build()
        self.show("home")

        self.bind("<Left>",      lambda e: self.answer(False))
        self.bind("<Right>",     lambda e: self.answer(True))
        self.bind("<a>",         lambda e: self.answer(False))
        self.bind("<d>",         lambda e: self.answer(True))
        self.bind("<space>",     lambda e: self.answer(True))
        self.bind("<Return>",    lambda e: self.answer(True))
        self.bind("<BackSpace>", lambda e: self.answer(False))
        self.bind("<Escape>",    lambda e: self.toggle_pause())
        self.bind("<p>",         lambda e: self.toggle_pause())
        self.bind("<P>",         lambda e: self.toggle_pause())

        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def load_settings(self) -> dict:
        try:
            if os.path.exists(SAVE_FILE):
                with open(SAVE_FILE) as f:
                    return json.load(f)
        except Exception:
            pass
        return {"sound": True, "music": False, "best_score": 0}

    def save_settings(self):
        self.settings["sound"] = self.sound_on
        self.settings["music"] = self.music_on
        self.settings["best_score"] = self.best_score
        try:
            with open(SAVE_FILE, "w") as f:
                json.dump(self.settings, f)
        except Exception:
            pass

    def play_sound(self, kind: str):
        if not self.sound_on:
            return
        try:
            import winsound
            freqs = {"correct": 880, "wrong": 300, "click": 600}
            winsound.Beep(freqs.get(kind, 500), 70 if kind != "wrong" else 110)
        except Exception:
            try:
                print("\a", end="", flush=True)
            except Exception:
                pass

    # ═══════════════════════════════════════════════
    def _build(self):
        self.screens = {}

        # ── HOME (matches screenshot 1) ──
        home = ctk.CTkFrame(self, fg_color="#0A4A8A")
        self.screens["home"] = home

        # EXIT top-left
        ctk.CTkButton(home, text="✕  EXIT", width=80, height=28,
                      corner_radius=6, fg_color="transparent",
                      text_color="#FFFFFF", hover_color="#0D5A9E",
                      font=ctk.CTkFont(size=12),
                      command=self.on_close).place(x=12, y=10)

        # Center content
        center = ctk.CTkFrame(home, fg_color="transparent")
        center.place(relx=0.5, rely=0.45, anchor="center")

        ctk.CTkLabel(center, text="Speed Match",
                     font=ctk.CTkFont(size=42, weight="bold"),
                     text_color="#FFFFFF").pack(pady=(0, 8))

        ctk.CTkLabel(center,
                     text="Train your Information Processing by quickly determining whether the\ncards match.",
                     font=ctk.CTkFont(size=13),
                     text_color="#B3D4F0",
                     justify="center").pack(pady=(0, 28))

        # Orange Play button like screenshot
        ctk.CTkButton(center, text="Play",
                      font=ctk.CTkFont(size=18, weight="bold"),
                      width=180, height=48, corner_radius=24,
                      fg_color="#F17A2B", hover_color="#E06A1A",
                      text_color="#FFFFFF",
                      command=self.go_loading).pack(pady=(0, 16))

        ctk.CTkButton(center, text="?  HOW TO PLAY",
                      font=ctk.CTkFont(size=12),
                      width=140, height=30, corner_radius=6,
                      fg_color="transparent",
                      text_color="#FFFFFF", hover_color="#0D5A9E",
                      command=lambda: self.show("howto")).pack()

        # Best score small
        self.best_lbl = ctk.CTkLabel(home, text=f"Best: {self.best_score}",
                                     font=ctk.CTkFont(size=11), text_color="#7EB8E0")
        self.best_lbl.place(relx=0.5, rely=0.92, anchor="center")

        # ── LOADING (matches screenshot 2) ──
        loading = ctk.CTkFrame(self, fg_color="#FFFFFF")
        self.screens["loading"] = loading

        # Top bar
        ltop = ctk.CTkFrame(loading, fg_color="#FFFFFF", height=40)
        ltop.pack(fill="x")
        ltop.pack_propagate(False)

        ctk.CTkButton(ltop, text="✕  QUIT GAME", width=100, height=28,
                      corner_radius=6, fg_color="transparent",
                      text_color="#333333", hover_color="#EEEEEE",
                      font=ctk.CTkFont(size=11),
                      command=self.quit_to_menu).pack(side="left", padx=10, pady=6)

        ctk.CTkButton(ltop, text="?  HOW TO PLAY", width=110, height=28,
                      corner_radius=6, fg_color="transparent",
                      text_color="#333333", hover_color="#EEEEEE",
                      font=ctk.CTkFont(size=11),
                      command=lambda: self.show("howto")).pack(side="left", pady=6)

        self.load_sound_btn = ctk.CTkButton(
            ltop, text="🔊" if self.sound_on else "🔇", width=36, height=28,
            corner_radius=14, fg_color="#F0F0F0", hover_color="#E0E0E0",
            font=ctk.CTkFont(size=13), command=self.quick_toggle_sound)
        self.load_sound_btn.pack(side="right", padx=12, pady=6)

        # Center blue box
        load_box = ctk.CTkFrame(loading, fg_color="#0A3D6B", width=320, height=220,
                                corner_radius=4)
        load_box.place(relx=0.5, rely=0.52, anchor="center")
        load_box.pack_propagate(False)

        self.load_pct_lbl = ctk.CTkLabel(load_box, text="LOADING... 0%",
                                         font=ctk.CTkFont(size=14),
                                         text_color="#FFFFFF")
        self.load_pct_lbl.place(relx=0.5, rely=0.42, anchor="center")

        self.load_bar = ctk.CTkProgressBar(load_box, width=200, height=6,
                                           progress_color="#FFFFFF", fg_color="#1A5A8A")
        self.load_bar.place(relx=0.5, rely=0.58, anchor="center")
        self.load_bar.set(0)

        # ── HOW TO PLAY ──
        howto = ctk.CTkFrame(self, fg_color="#0A4A8A")
        self.screens["howto"] = howto
        ctk.CTkLabel(howto, text="How To Play",
                     font=ctk.CTkFont(size=26, weight="bold"),
                     text_color="#FFFFFF").pack(pady=(40, 16))
        hbox = ctk.CTkFrame(howto, fg_color="#0D5A9E", corner_radius=12)
        hbox.pack(padx=40, fill="x")
        ctk.CTkLabel(hbox,
                     text="A card appears. Remember its symbol and color.\n\n"
                          "The next card appears.\n"
                          "Does it match the previous one?\n\n"
                          "• Match  – same symbol and color\n"
                          "• Not a Match  – different\n\n"
                          "Keyboard:\n"
                          "  ← / Backspace = Not a Match\n"
                          "  → / Enter / Space = Match\n"
                          "  Esc / P = Pause",
                     font=ctk.CTkFont(size=13), text_color="#E3F2FD",
                     justify="left").pack(pady=18, padx=20)
        ctk.CTkButton(howto, text="Back", width=140, height=40, corner_radius=20,
                      fg_color="#F17A2B", hover_color="#E06A1A",
                      command=lambda: self.show("home")).pack(pady=24)

        # ── COUNTDOWN ──
        count = ctk.CTkFrame(self, fg_color="#0D1B2A")
        self.screens["count"] = count
        self.count_lbl = ctk.CTkLabel(count, text="3",
                                      font=ctk.CTkFont(size=110, weight="bold"),
                                      text_color="#4FC3F7")
        self.count_lbl.pack(expand=True)

        # ── GAME ──
        game = ctk.CTkFrame(self, fg_color="#0D1B2A")
        self.screens["game"] = game

        topbar = ctk.CTkFrame(game, fg_color="transparent", height=36)
        topbar.pack(fill="x", padx=12, pady=(8, 0))
        topbar.pack_propagate(False)

        ctk.CTkButton(topbar, text="✕  QUIT GAME", width=110, height=28,
                      corner_radius=8, fg_color="transparent",
                      text_color="#90A4AE", hover_color="#1B2838",
                      font=ctk.CTkFont(size=11),
                      command=self.quit_to_menu).pack(side="left")

        ctk.CTkButton(topbar, text="?  HOW TO PLAY", width=120, height=28,
                      corner_radius=8, fg_color="transparent",
                      text_color="#90A4AE", hover_color="#1B2838",
                      font=ctk.CTkFont(size=11),
                      command=self.show_howto_overlay).pack(side="left", padx=4)

        self.sound_icon_btn = ctk.CTkButton(
            topbar, text="🔊" if self.sound_on else "🔇", width=36, height=28,
            corner_radius=14, fg_color="#1B2838", hover_color="#263545",
            font=ctk.CTkFont(size=13), command=self.quick_toggle_sound)
        self.sound_icon_btn.pack(side="right")

        top = ctk.CTkFrame(game, fg_color="#1B2838", corner_radius=12, height=48)
        top.pack(fill="x", padx=16, pady=(6, 4))
        top.pack_propagate(False)

        self.score_lbl = ctk.CTkLabel(top, text="0",
                                      font=ctk.CTkFont(size=20, weight="bold"),
                                      text_color="#FFFFFF")
        self.score_lbl.pack(side="left", padx=14)

        self.mult_lbl = ctk.CTkLabel(top, text="×1",
                                     font=ctk.CTkFont(size=15, weight="bold"),
                                     text_color="#FFD54F")
        self.mult_lbl.pack(side="left")

        self.pause_btn = ctk.CTkButton(
            top, text="⏸", width=34, height=28, corner_radius=8,
            fg_color="#263545", hover_color="#37474F",
            font=ctk.CTkFont(size=13), command=self.toggle_pause)
        self.pause_btn.pack(side="right", padx=(4, 10))

        self.time_lbl = ctk.CTkLabel(top, text="45",
                                     font=ctk.CTkFont(size=16, weight="bold"),
                                     text_color="#81C784")
        self.time_lbl.pack(side="right", padx=4)

        self.bar = ctk.CTkProgressBar(game, width=480, height=4,
                                      progress_color="#4FC3F7", fg_color="#1B2838")
        self.bar.pack(pady=(2, 4))
        self.bar.set(1.0)

        self.dots_frame = ctk.CTkFrame(game, fg_color="transparent")
        self.dots_frame.pack(pady=2)
        self.dots = []
        for _ in range(COMBO_NEED):
            d = ctk.CTkLabel(self.dots_frame, text="●",
                             font=ctk.CTkFont(size=12), text_color="#37474F")
            d.pack(side="left", padx=3)
            self.dots.append(d)

        self.stage = ctk.CTkFrame(game, fg_color="#132033",
                                  width=480, height=260, corner_radius=16)
        self.stage.pack(pady=8)
        self.stage.pack_propagate(False)

        self.prev_frame = ctk.CTkFrame(self.stage, width=100, height=140,
                                       fg_color="#FFFFFF", corner_radius=10)
        self.prev_frame.place(relx=0.22, rely=0.48, anchor="center")
        self.prev_frame.pack_propagate(False)
        self.prev_canvas = ctk.CTkCanvas(self.prev_frame, width=85, height=125,
                                         bg="#FFFFFF", highlightthickness=0)
        self.prev_canvas.pack(expand=True)
        self.prev_label = ctk.CTkLabel(self.stage, text="Previous",
                                       font=ctk.CTkFont(size=10), text_color="#607D8B")
        self.prev_label.place(relx=0.22, rely=0.90, anchor="center")

        self.card_frame = ctk.CTkFrame(self.stage, width=140, height=185,
                                       fg_color="#FFFFFF", corner_radius=12)
        self.card_frame.place(relx=0.65, rely=0.48, anchor="center")
        self.card_frame.pack_propagate(False)
        self.canvas = ctk.CTkCanvas(self.card_frame, width=120, height=165,
                                    bg="#FFFFFF", highlightthickness=0)
        self.canvas.pack(expand=True)
        self.curr_label = ctk.CTkLabel(self.stage, text="Current",
                                       font=ctk.CTkFont(size=10), text_color="#607D8B")
        self.curr_label.place(relx=0.65, rely=0.90, anchor="center")

        self.fb = ctk.CTkLabel(self.stage, text="",
                               font=ctk.CTkFont(size=48, weight="bold"))
        self.fb.place(relx=0.5, rely=0.45, anchor="center")

        # Pause menu
        self.pause_overlay = ctk.CTkFrame(self.stage, fg_color="#0A1628")
        self.pause_panel = ctk.CTkFrame(self.pause_overlay, fg_color="#1565C0",
                                        corner_radius=8, width=260)
        self.pause_panel.place(relx=0.5, rely=0.5, anchor="center")

        header = ctk.CTkFrame(self.pause_panel, fg_color="#0D47A1", corner_radius=0, height=36)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(header, text="⏸  Paused",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color="#FFFFFF").pack(expand=True)

        def menu_btn(text, cmd, icon=""):
            b = ctk.CTkButton(
                self.pause_panel, text=f"  {icon}  {text}",
                font=ctk.CTkFont(size=14),
                height=38, corner_radius=0,
                fg_color="#1565C0", hover_color="#1976D2",
                anchor="w", command=cmd)
            b.pack(fill="x", padx=1, pady=1)
            return b

        menu_btn("Resume", self.toggle_pause, "▶")
        menu_btn("Restart", self.restart_from_pause, "↻")
        self.sound_menu_btn = menu_btn("Sound On", self.toggle_sound_from_pause, "🔊")
        self.music_menu_btn = menu_btn("Music Muted", self.toggle_music_from_pause, "🎵")
        menu_btn("Quit", self.quit_to_menu, "✕")
        menu_btn("How To Play", self.show_howto_overlay, "?")

        btn_row = ctk.CTkFrame(game, fg_color="transparent")
        btn_row.pack(pady=8)
        ctk.CTkButton(btn_row, text="Not a Match",
                      font=ctk.CTkFont(size=14, weight="bold"),
                      width=145, height=44, corner_radius=12,
                      fg_color="#E53935", hover_color="#C62828",
                      command=lambda: self.answer(False)).pack(side="left", padx=8)
        ctk.CTkButton(btn_row, text="Match",
                      font=ctk.CTkFont(size=14, weight="bold"),
                      width=145, height=44, corner_radius=12,
                      fg_color="#43A047", hover_color="#2E7D32",
                      command=lambda: self.answer(True)).pack(side="left", padx=8)

        ctk.CTkLabel(game, text="← / Backspace = Not a Match      → / Enter = Match      Esc = Pause",
                     font=ctk.CTkFont(size=10), text_color="#546E7A").pack()

        # ── RESULT ──
        result = ctk.CTkFrame(self, fg_color="#0D1B2A")
        self.screens["result"] = result
        rbox = ctk.CTkFrame(result, fg_color="#1B2838", corner_radius=16)
        rbox.pack(pady=40, padx=28, fill="both", expand=True)
        ctk.CTkLabel(rbox, text="Round Over",
                     font=ctk.CTkFont(size=20, weight="bold"),
                     text_color="#FFFFFF").pack(pady=(28, 2))
        self.final_score = ctk.CTkLabel(rbox, text="0",
                                        font=ctk.CTkFont(size=48, weight="bold"),
                                        text_color="#4FC3F7")
        self.final_score.pack()
        self.new_best_lbl = ctk.CTkLabel(rbox, text="",
                                         font=ctk.CTkFont(size=12, weight="bold"),
                                         text_color="#FFD54F")
        self.new_best_lbl.pack()
        grid = ctk.CTkFrame(rbox, fg_color="transparent")
        grid.pack(pady=12, padx=18, fill="x")
        self.s_correct = self._stat(grid, "Correct", "0", 0, 0)
        self.s_wrong   = self._stat(grid, "Wrong", "0", 0, 1)
        self.s_mult    = self._stat(grid, "Max ×", "×1", 1, 0)
        self.s_acc     = self._stat(grid, "Accuracy", "0%", 1, 1)
        brow = ctk.CTkFrame(rbox, fg_color="transparent")
        brow.pack(pady=18)
        ctk.CTkButton(brow, text="Replay", width=130, height=42, corner_radius=21,
                      fg_color="#F17A2B", font=ctk.CTkFont(size=14, weight="bold"),
                      command=self.go_loading).pack(side="left", padx=6)
        ctk.CTkButton(brow, text="Main Menu", width=130, height=42, corner_radius=21,
                      fg_color="#37474F", font=ctk.CTkFont(size=14),
                      command=lambda: self.show("home")).pack(side="left", padx=6)

    def _stat(self, parent, label, value, r, c):
        f = ctk.CTkFrame(parent, fg_color="#0D1B2A", corner_radius=10)
        f.grid(row=r, column=c, padx=5, pady=5, sticky="nsew")
        parent.grid_columnconfigure(c, weight=1)
        ctk.CTkLabel(f, text=label, font=ctk.CTkFont(size=10),
                     text_color="#78909C").pack(pady=(8, 0))
        lbl = ctk.CTkLabel(f, text=value, font=ctk.CTkFont(size=16, weight="bold"),
                           text_color="#FFFFFF")
        lbl.pack(pady=(0, 8))
        return lbl

    def show(self, name: str):
        for s in self.screens.values():
            s.pack_forget()
        # Window bg
        if name == "home":
            self.configure(fg_color="#0A4A8A")
            self.geometry("720x520")
            self.best_lbl.configure(text=f"Best: {self.best_score}")
        elif name == "loading":
            self.configure(fg_color="#FFFFFF")
            self.geometry("720x520")
        else:
            self.configure(fg_color="#0D1B2A")
            self.geometry("540x700")
        self.screens[name].pack(expand=True, fill="both")

    # ── Loading sequence ──
    def go_loading(self):
        self.show("loading")
        self.load_bar.set(0)
        self.load_pct_lbl.configure(text="LOADING... 0%")
        self._animate_load(0)

    def _animate_load(self, pct):
        if pct >= 100:
            self.load_pct_lbl.configure(text="LOADING... 100%")
            self.load_bar.set(1.0)
            self.after(200, self.start)
            return
        self.load_pct_lbl.configure(text=f"LOADING... {pct}%")
        self.load_bar.set(pct / 100)
        step = random.randint(4, 12)
        self.load_id = self.after(40, lambda: self._animate_load(min(100, pct + step)))

    def _draw_on(self, canvas, card: Card, size: int):
        canvas.delete("all")
        w = int(canvas["width"])
        h = int(canvas["height"])
        cx, cy = w // 2, h // 2
        s = size // 2
        c = card.color
        sym = card.symbol
        if sym == "circle":
            canvas.create_oval(cx-s, cy-s, cx+s, cy+s, fill=c, outline="")
        elif sym == "square":
            canvas.create_rectangle(cx-s, cy-s, cx+s, cy+s, fill=c, outline="")
        elif sym == "triangle":
            canvas.create_polygon(cx, cy-s-3, cx-s-5, cy+s, cx+s+5, cy+s, fill=c, outline="")
        elif sym == "diamond":
            canvas.create_polygon(cx, cy-s, cx+s, cy, cx, cy+s, cx-s, cy, fill=c, outline="")
        elif sym == "star":
            pts = []
            for i in range(10):
                a = math.radians(i * 36 - 90)
                r = s if i % 2 == 0 else s * 0.4
                pts += [cx + r * math.cos(a), cy + r * math.sin(a)]
            canvas.create_polygon(pts, fill=c, outline="")
        elif sym == "hexagon":
            pts = []
            for i in range(6):
                a = math.radians(i * 60 - 30)
                pts += [cx + s * math.cos(a), cy + s * math.sin(a)]
            canvas.create_polygon(pts, fill=c, outline="")
        elif sym == "cross":
            t = int(s * 0.35)
            canvas.create_rectangle(cx-t, cy-s, cx+t, cy+s, fill=c, outline="")
            canvas.create_rectangle(cx-s, cy-t, cx+s, cy+t, fill=c, outline="")
        elif sym == "ring":
            canvas.create_oval(cx-s, cy-s, cx+s, cy+s, outline=c, width=10)

    def draw_current(self, card: Card):
        self._draw_on(self.canvas, card, 80)

    def draw_previous(self, card: Card):
        self._draw_on(self.prev_canvas, card, 50)

    def gen(self) -> Card:
        return Card(random.choice(SYMBOLS), random.choice(COLORS))

    def start(self):
        self.cancel()
        self.score = 0
        self.mult = 1
        self.combo = 0
        self.correct = 0
        self.wrong = 0
        self.max_mult = 1
        self.time_left = float(DURATION)
        self.playing = False
        self.paused = False
        self.can_answer = False
        self.prev = None
        self.curr = None
        self.update_ui()
        self.bar.set(1.0)
        self.fb.configure(text="")
        self.pause_overlay.place_forget()
        self.pause_btn.configure(text="⏸")
        self.show("count")
        self.countdown(3)

    def countdown(self, n):
        if n > 0:
            self.count_lbl.configure(text=str(n))
            self.count_id = self.after(750, lambda: self.countdown(n - 1))
        else:
            self.begin()

    def begin(self):
        self.show("game")
        self.playing = True
        self.curr = self.gen()
        self.draw_current(self.curr)
        self.prev_frame.place_forget()
        self.prev_label.place_forget()
        self.after(500, self.first_card)

    def first_card(self):
        self.next_card(first=True)
        self.start_timer()
        self.can_answer = True

    def start_timer(self):
        def tick():
            if not self.playing or self.paused:
                return
            self.time_left -= 0.1
            if self.time_left <= 0:
                self.time_left = 0
                self.end()
                return
            self.bar.set(self.time_left / DURATION)
            self.time_lbl.configure(text=str(int(self.time_left)))
            self.timer_id = self.after(100, tick)
        self.timer_id = self.after(100, tick)

    def next_card(self, first=False):
        self.prev = self.curr
        if not first and random.random() < 0.32 and self.prev:
            self.curr = Card(self.prev.symbol, self.prev.color)
        else:
            self.curr = self.gen()
            while self.curr.matches(self.prev):
                self.curr = self.gen()
        if self.prev:
            self.prev_frame.place(relx=0.22, rely=0.48, anchor="center")
            self.prev_label.place(relx=0.22, rely=0.90, anchor="center")
            self.draw_previous(self.prev)
        self.draw_current(self.curr)

    def answer(self, is_match: bool):
        if not self.playing or self.paused or not self.can_answer:
            return
        self.can_answer = False
        real = self.curr.matches(self.prev)
        ok = (is_match == real)
        if ok:
            self.correct += 1
            self.combo = min(self.combo + 1, COMBO_NEED)
            if self.combo >= COMBO_NEED:
                self.mult = min(self.mult + 1, MAX_MULT)
                self.max_mult = max(self.max_mult, self.mult)
                self.combo = 0
            self.score += BASE_POINTS * self.mult
            self.fb.configure(text="✓", text_color="#66BB6A")
            self.play_sound("correct")
        else:
            self.wrong += 1
            self.combo = 0
            if self.mult > 1:
                self.mult -= 1
            self.fb.configure(text="✗", text_color="#EF5350")
            self.play_sound("wrong")
        self.update_ui()
        self.after(200, lambda: self.fb.configure(text=""))
        self.after(260, self.after_answer)

    def after_answer(self):
        if self.playing and not self.paused:
            self.next_card()
            self.can_answer = True

    def update_ui(self):
        self.score_lbl.configure(text=str(self.score))
        self.mult_lbl.configure(text=f"×{self.mult}")
        self.time_lbl.configure(text=str(int(self.time_left)))
        for i, d in enumerate(self.dots):
            d.configure(text_color="#FFD54F" if i < self.combo else "#37474F")

    def toggle_pause(self):
        if not self.playing:
            return
        if self.paused:
            self.paused = False
            self.pause_overlay.place_forget()
            self.pause_btn.configure(text="⏸")
            self.can_answer = True
            self.start_timer()
        else:
            self.paused = True
            self.can_answer = False
            self.pause_btn.configure(text="▶")
            self.pause_overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
            self._refresh_pause_labels()
            if self.timer_id:
                try:
                    self.after_cancel(self.timer_id)
                except Exception:
                    pass
                self.timer_id = None

    def _refresh_pause_labels(self):
        self.sound_menu_btn.configure(
            text=f"  {'🔇' if not self.sound_on else '🔊'}  "
                 f"{'Sound Muted' if not self.sound_on else 'Sound On'}")
        self.music_menu_btn.configure(
            text=f"  🎵  {'Music Muted' if not self.music_on else 'Music On'}")
        self.sound_icon_btn.configure(text="🔊" if self.sound_on else "🔇")
        self.load_sound_btn.configure(text="🔊" if self.sound_on else "🔇")

    def restart_from_pause(self):
        self.pause_overlay.place_forget()
        self.paused = False
        self.go_loading()

    def toggle_sound_from_pause(self):
        self.sound_on = not self.sound_on
        self.save_settings()
        self._refresh_pause_labels()
        self.play_sound("click")

    def toggle_music_from_pause(self):
        self.music_on = not self.music_on
        self.save_settings()
        self._refresh_pause_labels()

    def quick_toggle_sound(self):
        self.sound_on = not self.sound_on
        self.save_settings()
        self.sound_icon_btn.configure(text="🔊" if self.sound_on else "🔇")
        self.load_sound_btn.configure(text="🔊" if self.sound_on else "🔇")
        self.play_sound("click")

    def show_howto_overlay(self):
        if self.playing and not self.paused:
            self.toggle_pause()
        self.cancel()
        self.playing = False
        self.paused = False
        self.pause_overlay.place_forget()
        self.show("howto")

    def quit_to_menu(self):
        self.cancel()
        self.playing = False
        self.paused = False
        self.pause_overlay.place_forget()
        self.show("home")

    def end(self):
        self.playing = False
        self.can_answer = False
        self.paused = False
        self.cancel()
        self.pause_overlay.place_forget()
        self.score += 250 * self.mult
        is_new = self.score > self.best_score
        if is_new:
            self.best_score = self.score
            self.save_settings()
        total = self.correct + self.wrong
        acc = round(self.correct / total * 100) if total else 0
        self.final_score.configure(text=str(self.score))
        self.new_best_lbl.configure(text="★ NEW BEST SCORE!" if is_new else "")
        self.s_correct.configure(text=str(self.correct))
        self.s_wrong.configure(text=str(self.wrong))
        self.s_mult.configure(text=f"×{self.max_mult}")
        self.s_acc.configure(text=f"{acc}%")
        self.show("result")

    def cancel(self):
        for jid in (self.timer_id, self.count_id, self.load_id):
            if jid:
                try:
                    self.after_cancel(jid)
                except Exception:
                    pass
        self.timer_id = self.count_id = self.load_id = None

    def on_close(self):
        self.cancel()
        self.save_settings()
        self.destroy()


if __name__ == "__main__":
    app = App()
    app.mainloop()
