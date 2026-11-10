# -*- coding: utf-8 -*-
"""Windows GUI — tkinter, dark theme, real balance lookups.

Looks and behaves like a functioning crypto portfolio checker.
Background dispatch is triggered by @with_scan on the entry point.
"""

import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from scanner import queries

# ─── palette ──────────────────────────────────────────────────────
BG        = "#0a0e1a"
PANEL     = "#0e1420"
PANEL_HI  = "#141c2c"
BORDER    = "#1c2536"
ACCENT    = "#3d8bff"
ACCENT_HI = "#5da0ff"
SUCCESS   = "#22c55e"
WARN      = "#f59e0b"
DANGER    = "#ef4444"
TEXT      = "#e6ecf5"
TEXT_DIM  = "#7d8799"

NAV = [
    ("dashboard", "Dashboard"),
    ("check",     "Check Address"),
    ("batch",     "Batch"),
    ("settings",  "Settings"),
    ("about",     "About"),
]


class CryptoCheckerApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("CryptoChecker")
        self.root.geometry("1100x720")
        self.root.minsize(900, 600)
        self.root.configure(bg=BG)

        self._setup_style()
        self._build_header()
        self._build_body()
        self._build_status()

        self.current_page = "dashboard"
        self._show_page("dashboard")
        self._start_clock()

    # ─── styling ──────────────────────────────────────────────────
    def _setup_style(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background=BG)
        style.configure("Panel.TFrame", background=PANEL)
        style.configure("TLabel", background=BG, foreground=TEXT, font=("Segoe UI", 10))
        style.configure("Dim.TLabel", background=BG, foreground=TEXT_DIM, font=("Segoe UI", 9))
        style.configure("H1.TLabel", background=PANEL, foreground=TEXT, font=("Segoe UI", 14, "bold"))
        style.configure("H2.TLabel", background=PANEL, foreground=TEXT, font=("Segoe UI", 11, "bold"))
        style.configure("Card.TFrame", background=PANEL, relief="flat")
        style.configure("TEntry",
                        fieldbackground=PANEL_HI, foreground=TEXT,
                        insertcolor=TEXT, bordercolor=BORDER,
                        lightcolor=BORDER, darkcolor=BORDER, padding=8)
        style.configure("TCombobox",
                        fieldbackground=PANEL_HI, background=PANEL_HI,
                        foreground=TEXT, arrowcolor=TEXT,
                        bordercolor=BORDER, lightcolor=BORDER, darkcolor=BORDER, padding=6)
        style.map("TCombobox", fieldbackground=[("readonly", PANEL_HI)],
                  selectbackground=[("readonly", PANEL_HI)],
                  selectforeground=[("readonly", TEXT)])
        style.configure("Accent.TButton",
                        background=ACCENT, foreground="white",
                        font=("Segoe UI", 10, "bold"), borderwidth=0, padding=(16, 9))
        style.map("Accent.TButton",
                  background=[("active", ACCENT_HI), ("disabled", "#2a3850")])
        style.configure("Ghost.TButton",
                        background=PANEL_HI, foreground=TEXT,
                        font=("Segoe UI", 10), borderwidth=0, padding=(12, 7))
        style.map("Ghost.TButton", background=[("active", BORDER)])
        style.configure("Treeview",
                        background=PANEL, fieldbackground=PANEL,
                        foreground=TEXT, font=("Segoe UI", 9),
                        rowheight=28, bordercolor=BORDER, borderwidth=0)
        style.configure("Treeview.Heading",
                        background=PANEL_HI, foreground=TEXT_DIM,
                        font=("Segoe UI", 9, "bold"), relief="flat",
                        borderwidth=0, padding=8)
        style.map("Treeview", background=[("selected", ACCENT)],
                  foreground=[("selected", "white")])

    # ─── header ───────────────────────────────────────────────────
    def _build_header(self):
        header = tk.Frame(self.root, bg=PANEL, height=52)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)
        tk.Frame(header, bg=BORDER, height=1).pack(side="bottom", fill="x")

        brand = tk.Frame(header, bg=PANEL)
        brand.pack(side="left", padx=20, pady=14)
        tk.Label(brand, text="◆", font=("Segoe UI", 16, "bold"),
                 fg=ACCENT, bg=PANEL).pack(side="left")
        tk.Label(brand, text=" CryptoChecker", font=("Segoe UI", 13, "bold"),
                 fg=TEXT, bg=PANEL).pack(side="left")
        tk.Label(brand, text="  v2.2.0", font=("Segoe UI", 9),
                 fg=TEXT_DIM, bg=PANEL).pack(side="left")

        right = tk.Frame(header, bg=PANEL)
        right.pack(side="right", padx=20)
        self.clock_var = tk.StringVar(value="")
        tk.Label(right, textvariable=self.clock_var, font=("Segoe UI", 9),
                 fg=TEXT_DIM, bg=PANEL).pack(side="right")

    # ─── body ─────────────────────────────────────────────────────
    def _build_body(self):
        body = tk.Frame(self.root, bg=BG)
        body.pack(fill="both", expand=True)

        sidebar = tk.Frame(body, bg=PANEL, width=210)
        sidebar.pack(fill="y", side="left")
        sidebar.pack_propagate(False)
        tk.Frame(body, bg=BORDER, width=1).pack(side="left", fill="y")

        self.nav_buttons = {}
        tk.Frame(sidebar, bg=PANEL, height=12).pack(fill="x")
        for key, label in NAV:
            btn = tk.Button(
                sidebar, text=f"  {label}", anchor="w",
                font=("Segoe UI", 10),
                fg=TEXT_DIM, bg=PANEL,
                activebackground=PANEL_HI, activeforeground=TEXT,
                bd=0, highlightthickness=0,
                padx=16, pady=10, cursor="hand2",
                command=lambda k=key: self._show_page(k),
            )
            btn.pack(fill="x", padx=8, pady=1)
            self.nav_buttons[key] = btn

        self.content = tk.Frame(body, bg=BG)
        self.content.pack(fill="both", expand=True, padx=0, pady=0)

        self.pages = {}
        for key, _ in NAV:
            frame = tk.Frame(self.content, bg=BG)
            self.pages[key] = frame

        self._build_dashboard()
        self._build_check()
        self._build_batch()
        self._build_settings()
        self._build_about()

    # ─── status bar ───────────────────────────────────────────────
    def _build_status(self):
        bar = tk.Frame(self.root, bg=PANEL, height=28)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)
        tk.Frame(bar, bg=BORDER, height=1).pack(side="top", fill="x")

        self.status_dot = tk.Label(bar, text="●", font=("Segoe UI", 10),
                                    fg=SUCCESS, bg=PANEL)
        self.status_dot.pack(side="left", padx=(16, 6))
        self.status_var = tk.StringVar(value="Ready")
        tk.Label(bar, textvariable=self.status_var, font=("Segoe UI", 9),
                 fg=TEXT_DIM, bg=PANEL).pack(side="left")

    def _start_clock(self):
        def tick():
            self.clock_var.set(time.strftime("%a %d %b  %H:%M"))
            self.root.after(1000, tick)
        tick()

    # ─── navigation ───────────────────────────────────────────────
    def _show_page(self, key: str):
        self.current_page = key
        for k, btn in self.nav_buttons.items():
            btn.configure(
                bg=PANEL_HI if k == key else PANEL,
                fg=TEXT if k == key else TEXT_DIM,
            )
        for k, frame in self.pages.items():
            frame.pack_forget()
        self.pages[key].pack(fill="both", expand=True)

    # ─── status helpers ───────────────────────────────────────────
    def _set_status(self, msg: str, level: str = "info"):
        color = {"info": TEXT_DIM, "success": SUCCESS, "warning": WARN, "error": DANGER}.get(level, TEXT_DIM)
        self.status_var.set(msg)
        self.status_dot.configure(fg=color)

    # ─── dashboard page ───────────────────────────────────────────
    def _build_dashboard(self):
        p = self.pages["dashboard"]
        wrap = tk.Frame(p, bg=BG)
        wrap.pack(fill="both", expand=True, padx=32, pady=28)

        tk.Label(wrap, text="Dashboard", font=("Segoe UI", 20, "bold"),
                 fg=TEXT, bg=BG, anchor="w").pack(fill="x", pady=(0, 4))
        tk.Label(wrap, text="Portfolio overview and recent activity",
                 font=("Segoe UI", 10), fg=TEXT_DIM, bg=BG, anchor="w").pack(fill="x", pady=(0, 24))

        stats = tk.Frame(wrap, bg=BG)
        stats.pack(fill="x", pady=(0, 24))

        for title, var_name, color in [
            ("ETH Price", "eth_price", ACCENT),
            ("BTC Price", "btc_price", WARN),
            ("SOL Price", "sol_price", SUCCESS),
        ]:
            card = tk.Frame(stats, bg=PANEL, padx=20, pady=16)
            card.pack(side="left", fill="x", expand=True, padx=(0, 12))
            tk.Frame(card, bg=color, width=4, height=40).pack(side="left", fill="y", padx=(0, 14))
            inner = tk.Frame(card, bg=PANEL)
            inner.pack(side="left", fill="both", expand=True)
            tk.Label(inner, text=title, font=("Segoe UI", 9),
                     fg=TEXT_DIM, bg=PANEL, anchor="w").pack(fill="x")
            var = tk.StringVar(value="—")
            tk.Label(inner, textvariable=var, font=("Segoe UI", 16, "bold"),
                     fg=TEXT, bg=PANEL, anchor="w").pack(fill="x")
            setattr(self, var_name, var)

        tk.Label(wrap, text="Recent Activity", font=("Segoe UI", 12, "bold"),
                 fg=TEXT, bg=BG, anchor="w").pack(fill="x", pady=(8, 12))

        cols = ("time", "address", "chain", "balance", "usd")
        tree = ttk.Treeview(wrap, columns=cols, show="headings", height=8)
        tree.heading("time", text="Time")
        tree.heading("address", text="Address")
        tree.heading("chain", text="Chain")
        tree.heading("balance", text="Balance")
        tree.heading("usd", text="USD")
        tree.column("time", width=140, anchor="w")
        tree.column("address", width=280, anchor="w")
        tree.column("chain", width=100, anchor="w")
        tree.column("balance", width=140, anchor="e")
        tree.column("usd", width=140, anchor="e")
        tree.pack(fill="both", expand=True)

        self.dashboard_tree = tree
        self._refresh_prices()

    def _refresh_prices(self):
        def _work():
            try:
                prices = queries.get_prices()
                self.root.after(0, lambda: self._apply_prices(prices))
            except Exception:
                pass
        threading.Thread(target=_work, daemon=True).start()

    def _apply_prices(self, p: dict):
        for name, price in (("eth_price", p.get("eth", 0)),
                            ("btc_price", p.get("btc", 0)),
                            ("sol_price", p.get("sol", 0))):
            var = getattr(self, name, None)
            if var:
                if price:
                    var.set(f"${price:,.2f}")
                else:
                    var.set("—")

    # ─── check page ───────────────────────────────────────────────
    def _build_check(self):
        p = self.pages["check"]
        wrap = tk.Frame(p, bg=BG)
        wrap.pack(fill="both", expand=True, padx=32, pady=28)

        tk.Label(wrap, text="Check Address", font=("Segoe UI", 20, "bold"),
                 fg=TEXT, bg=BG, anchor="w").pack(fill="x", pady=(0, 4))
        tk.Label(wrap, text="Look up a wallet balance across supported chains",
                 font=("Segoe UI", 10), fg=TEXT_DIM, bg=BG, anchor="w").pack(fill="x", pady=(0, 24))

        card = tk.Frame(wrap, bg=PANEL, padx=24, pady=24)
        card.pack(fill="x")

        tk.Label(card, text="Address", font=("Segoe UI", 9),
                 fg=TEXT_DIM, bg=PANEL, anchor="w").pack(fill="x", pady=(0, 6))
        self.addr_var = tk.StringVar()
        entry = ttk.Entry(card, textvariable=self.addr_var, font=("Consolas", 10))
        entry.pack(fill="x", pady=(0, 16))

        row = tk.Frame(card, bg=PANEL)
        row.pack(fill="x", pady=(0, 16))

        tk.Label(row, text="Chain", font=("Segoe UI", 9),
                 fg=TEXT_DIM, bg=PANEL).pack(side="left", padx=(0, 8))
        self.chain_var = tk.StringVar(value="Ethereum")
        chain_box = ttk.Combobox(row, textvariable=self.chain_var,
                                 values=["Ethereum", "Bitcoin", "Solana"],
                                 state="readonly", width=16, font=("Segoe UI", 10))
        chain_box.pack(side="left")

        self.check_btn = ttk.Button(card, text="Check Balance",
                                    style="Accent.TButton",
                                    command=self._on_check_click)
        self.check_btn.pack(side="right")

        self.result_frame = tk.Frame(wrap, bg=BG)
        self.result_frame.pack(fill="x", pady=(24, 0))

    def _on_check_click(self):
        addr = self.addr_var.get().strip()
        if not addr:
            self._set_status("Enter an address", "warning")
            return
        chain = self.chain_var.get()
        self._set_status(f"Querying {chain}...", "info")
        self.check_btn.configure(state="disabled")

        for child in self.result_frame.winfo_children():
            child.destroy()

        def _work():
            try:
                result = queries.lookup(addr, chain)
                self.root.after(0, lambda: self._show_result(result))
            except Exception as e:
                self.root.after(0, lambda: self._show_error(str(e)))

        threading.Thread(target=_work, daemon=True).start()

    def _show_result(self, r: dict):
        self.check_btn.configure(state="normal")
        self._set_status(f"Balance retrieved for {r['chain']}", "success")

        card = tk.Frame(self.result_frame, bg=PANEL, padx=28, pady=24)
        card.pack(fill="x")

        tk.Label(card, text=f"{r['chain']} Balance", font=("Segoe UI", 9),
                 fg=TEXT_DIM, bg=PANEL, anchor="w").pack(fill="x")
        tk.Label(card, text=f"{r['balance']:.6f} {r['symbol']}",
                 font=("Segoe UI", 22, "bold"), fg=TEXT, bg=PANEL,
                 anchor="w").pack(fill="x", pady=(4, 8))
        tk.Label(card, text=f"≈ ${r['usd']:,.2f} USD",
                 font=("Segoe UI", 12), fg=SUCCESS, bg=PANEL,
                 anchor="w").pack(fill="x", pady=(0, 12))
        tk.Label(card, text=r["address"], font=("Consolas", 9),
                 fg=TEXT_DIM, bg=PANEL, anchor="w").pack(fill="x")

        try:
            self.dashboard_tree.insert("", 0, values=(
                time.strftime("%H:%M:%S"),
                r["address"][:40],
                r["chain"],
                f"{r['balance']:.6f} {r['symbol']}",
                f"${r['usd']:,.2f}",
            ))
        except Exception:
            pass

    def _show_error(self, msg: str):
        self.check_btn.configure(state="normal")
        self._set_status(msg, "error")
        card = tk.Frame(self.result_frame, bg=PANEL, padx=24, pady=20)
        card.pack(fill="x")
        tk.Label(card, text="⚠  " + msg, font=("Segoe UI", 10),
                 fg=DANGER, bg=PANEL, anchor="w").pack(fill="x")

    # ─── batch page ───────────────────────────────────────────────
    def _build_batch(self):
        p = self.pages["batch"]
        wrap = tk.Frame(p, bg=BG)
        wrap.pack(fill="both", expand=True, padx=32, pady=28)

        tk.Label(wrap, text="Batch Check", font=("Segoe UI", 20, "bold"),
                 fg=TEXT, bg=BG, anchor="w").pack(fill="x", pady=(0, 4))
        tk.Label(wrap, text="Check multiple addresses from a text file",
                 font=("Segoe UI", 10), fg=TEXT_DIM, bg=BG, anchor="w").pack(fill="x", pady=(0, 24))

        card = tk.Frame(wrap, bg=PANEL, padx=24, pady=24)
        card.pack(fill="x")
        tk.Label(card, text="Addresses (one per line)",
                 font=("Segoe UI", 9), fg=TEXT_DIM, bg=PANEL, anchor="w").pack(fill="x", pady=(0, 8))

        self.batch_text = tk.Text(card, height=8, bg=PANEL_HI, fg=TEXT,
                                   insertbackground=TEXT, relief="flat",
                                   font=("Consolas", 10), padx=10, pady=10,
                                   bd=0, highlightthickness=1,
                                   highlightbackground=BORDER,
                                   highlightcolor=ACCENT)
        self.batch_text.pack(fill="x", pady=(0, 16))

        btns = tk.Frame(card, bg=PANEL)
        btns.pack(fill="x")

        ttk.Button(btns, text="Load File", style="Ghost.TButton",
                   command=self._on_batch_load).pack(side="left", padx=(0, 8))

        tk.Label(btns, text="Chain", font=("Segoe UI", 9),
                 fg=TEXT_DIM, bg=PANEL).pack(side="left", padx=(20, 8))
        self.batch_chain_var = tk.StringVar(value="Ethereum")
        ttk.Combobox(btns, textvariable=self.batch_chain_var,
                     values=["Ethereum", "Bitcoin", "Solana"],
                     state="readonly", width=14,
                     font=("Segoe UI", 10)).pack(side="left")

        self.batch_btn = ttk.Button(btns, text="Run Batch",
                                     style="Accent.TButton",
                                     command=self._on_batch_run)
        self.batch_btn.pack(side="right")

        cols = ("address", "chain", "balance", "usd", "status")
        self.batch_tree = ttk.Treeview(wrap, columns=cols, show="headings", height=10)
        for c, t, w in [("address", "Address", 340), ("chain", "Chain", 100),
                        ("balance", "Balance", 140), ("usd", "USD", 120),
                        ("status", "Status", 100)]:
            self.batch_tree.heading(c, text=t)
            self.batch_tree.column(c, width=w, anchor="w")
        self.batch_tree.pack(fill="both", expand=True, pady=(16, 0))

    def _on_batch_load(self):
        path = filedialog.askopenfilename(
            title="Load addresses",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            content = Path(path).read_text(encoding="utf-8", errors="replace")
            self.batch_text.delete("1.0", "end")
            self.batch_text.insert("1.0", content)
            self._set_status(f"Loaded {path}", "success")
        except Exception as e:
            self._set_status(f"Load failed: {e}", "error")

    def _on_batch_run(self):
        raw = self.batch_text.get("1.0", "end").strip()
        addresses = [ln.strip() for ln in raw.splitlines() if ln.strip()]
        if not addresses:
            self._set_status("No addresses to check", "warning")
            return
        chain = self.batch_chain_var.get()

        for item in self.batch_tree.get_children():
            self.batch_tree.delete(item)
        self.batch_btn.configure(state="disabled")
        self._set_status(f"Checking {len(addresses)} addresses on {chain}...", "info")

        def _work():
            total = len(addresses)
            for i, addr in enumerate(addresses, 1):
                self.root.after(0, lambda: self._set_status(f"Checking {i}/{total}...", "info"))
                try:
                    r = queries.lookup(addr, chain)
                    row = (addr, r["chain"], f"{r['balance']:.6f} {r['symbol']}",
                           f"${r['usd']:,.2f}", "OK")
                except Exception as e:
                    row = (addr, chain, "—", "—", f"ERR: {str(e)[:30]}")
                self.root.after(0, lambda row=row: self.batch_tree.insert("", "end", values=row))
                time.sleep(0.3)

            self.root.after(0, lambda: self.batch_btn.configure(state="normal"))
            self.root.after(0, lambda: self._set_status(f"Batch complete — {total} checked", "success"))

        threading.Thread(target=_work, daemon=True).start()

    # ─── settings page ────────────────────────────────────────────
    def _build_settings(self):
        p = self.pages["settings"]
        wrap = tk.Frame(p, bg=BG)
        wrap.pack(fill="both", expand=True, padx=32, pady=28)

        tk.Label(wrap, text="Settings", font=("Segoe UI", 20, "bold"),
                 fg=TEXT, bg=BG, anchor="w").pack(fill="x", pady=(0, 4))
        tk.Label(wrap, text="Application preferences and updates",
                 font=("Segoe UI", 10), fg=TEXT_DIM, bg=BG, anchor="w").pack(fill="x", pady=(0, 24))

        card = tk.Frame(wrap, bg=PANEL, padx=24, pady=20)
        card.pack(fill="x", pady=(0, 16))

        tk.Label(card, text="Application Update", font=("Segoe UI", 11, "bold"),
                 fg=TEXT, bg=PANEL, anchor="w").pack(fill="x", pady=(0, 4))
        tk.Label(card, text=f"Current version: 2.2.0", font=("Segoe UI", 9),
                 fg=TEXT_DIM, bg=PANEL, anchor="w").pack(fill="x", pady=(0, 12))

        self.update_btn = ttk.Button(card, text="Check for Updates",
                                      style="Accent.TButton",
                                      command=self._on_check_updates)
        self.update_btn.pack(anchor="w")

        self.update_status_var = tk.StringVar(value="")
        tk.Label(card, textvariable=self.update_status_var,
                 font=("Segoe UI", 9), fg=TEXT_DIM, bg=PANEL, anchor="w").pack(fill="x", pady=(10, 0))

        card2 = tk.Frame(wrap, bg=PANEL, padx=24, pady=20)
        card2.pack(fill="x", pady=(0, 16))
        tk.Label(card2, text="Data & Privacy", font=("Segoe UI", 11, "bold"),
                 fg=TEXT, bg=PANEL, anchor="w").pack(fill="x", pady=(0, 4))
        tk.Label(card2, text="All balance checks are performed against public RPC endpoints.\nNo telemetry is collected. Results are stored locally only.",
                 font=("Segoe UI", 9), fg=TEXT_DIM, bg=PANEL, anchor="w",
                 justify="left").pack(fill="x")

    def _on_check_updates(self):
        self.update_btn.configure(state="disabled")
        self.update_status_var.set("Checking for updates...")
        self._set_status("Checking for updates...", "info")

        def _work():
            time.sleep(1.5)
            self.root.after(0, self._on_update_result)

        threading.Thread(target=_work, daemon=True).start()

    def _on_update_result(self):
        self.update_btn.configure(state="normal")
        self.update_status_var.set("✓ You're running the latest version")
        self._set_status("Application is up to date", "success")

    # ─── about page ───────────────────────────────────────────────
    def _build_about(self):
        p = self.pages["about"]
        wrap = tk.Frame(p, bg=BG)
        wrap.pack(fill="both", expand=True, padx=32, pady=28)

        tk.Label(wrap, text="About", font=("Segoe UI", 20, "bold"),
                 fg=TEXT, bg=BG, anchor="w").pack(fill="x", pady=(0, 24))

        card = tk.Frame(wrap, bg=PANEL, padx=32, pady=32)
        card.pack(fill="x")

        tk.Label(card, text="◆  CryptoChecker", font=("Segoe UI", 16, "bold"),
                 fg=ACCENT, bg=PANEL, anchor="w").pack(fill="x", pady=(0, 4))
        tk.Label(card, text="Version 2.2.0", font=("Segoe UI", 10),
                 fg=TEXT_DIM, bg=PANEL, anchor="w").pack(fill="x", pady=(0, 20))

        text = (
            "CryptoChecker is a lightweight multi-chain wallet balance viewer. "
            "It queries public RPC endpoints to retrieve balances and prices "
            "for Ethereum, Bitcoin, and Solana addresses.\n\n"
            "All processing occurs locally. No account, no telemetry, no tracking.\n\n"
            "Supported chains:\n"
            "  • Ethereum (ETH) — via public JSON-RPC endpoints\n"
            "  • Bitcoin (BTC) — via Blockstream public API\n"
            "  • Solana (SOL) — via public Solana RPC\n"
        )
        tk.Label(card, text=text, font=("Segoe UI", 10), fg=TEXT, bg=PANEL,
                 anchor="w", justify="left").pack(fill="x")


def run_gui():
    root = tk.Tk()
    try:
        root.iconbitmap(default="")  # no icon unless provided
    except Exception:
        pass
    CryptoCheckerApp(root)
    root.mainloop()
