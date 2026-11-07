"""
CPU Scheduling screen (the window part).

The math lives in logic/cpu_scheduling.py. This file only builds the
screen: input boxes, tables, buttons and the Gantt chart.

main.py loads this file automatically and creates one `Module` object,
which becomes the page you see.
"""

import random
import tkinter as tk
from tkinter import ttk, font as tkfont

# We can't "import main" here (it would start the whole app a second time),
# so the few colours we need are copied from main.py.
BG = "#1a1c2c"
PANEL = "#333c57"
TEXT = "#f4f4f4"
MUTED = "#94b0c2"
HILITE = "#566c86"
YELLOW = "#ffcd75"
GOOD = "#a7f070"      # green: success messages
BAD = "#ff6b81"       # red: error messages

# Colours for the Gantt blocks. Each process takes the next colour in the list.
BLOCK_COLORS = ["#41a6f6", "#ef7d57", "#c9a0ff", "#a7f070",
                "#ffcd75", "#ff6b81", "#73eff7", "#f4a6c8"]
IDLE_COLOR = "#566c86"

# A well-known textbook example, handy for checking the answers by hand.
SAMPLE = [
    {"pid": "P1", "arrival": 0, "burst": 5},
    {"pid": "P2", "arrival": 1, "burst": 3},
    {"pid": "P3", "arrival": 2, "burst": 8},
    {"pid": "P4", "arrival": 3, "burst": 6},
]

# Drawing thousands of Gantt blocks would be slow, and Tk canvases get
# unreliable at huge widths, so the chart shows only the first blocks.
# (The results TABLE always shows every process.)
MAX_GANTT_BLOCKS = 500


def parse_whole_number(text, name, minimum):
    """Turn what the user typed into a whole number, or explain what's wrong.

    Raises ValueError with a friendly message if the text is blank, not a
    whole number, or smaller than `minimum`. The caller catches the error
    and shows the message, so bad input never crashes the program.
    """
    text = text.strip()
    if text == "":
        raise ValueError(f"{name} is required.")
    try:
        value = int(text)
    except ValueError:
        raise ValueError(f"{name} must be a whole number (you typed '{text}').")
    if value < minimum:
        raise ValueError(f"{name} must be {minimum} or more (you typed {value}).")
    return value


def make_table(parent, columns, widths):
    """Build a table (Treeview) with a scrollbar. Returns (frame, table)."""
    box = ttk.Frame(parent)
    tree = ttk.Treeview(box, columns=columns, show="headings", height=8)
    for col, width in zip(columns, widths):
        tree.heading(col, text=col)
        tree.column(col, width=width, anchor="center")
    bar = ttk.Scrollbar(box, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=bar.set)
    tree.pack(side="left", fill="both", expand=True)
    bar.pack(side="right", fill="y")
    return box, tree


class Module(ttk.Frame):
    """The CPU Scheduling page."""

    def __init__(self, parent):
        super().__init__(parent, padding=14)
        from logic.cpu_scheduling import ALGORITHMS, DESCRIPTIONS   # algorithms + their text
        self.algorithms = ALGORITHMS
        self.descriptions = DESCRIPTIONS

        self.procs = []              # the processes the user has entered
        self.mono = tkfont.nametofont("TkFixedFont").actual("family")

        # tkinter "variables" stay linked to the box/label they are given to.
        self.pid_var = tk.StringVar(value="P1")
        self.arrival_var = tk.StringVar()
        self.burst_var = tk.StringVar()
        self.count_var = tk.StringVar(value="50")
        self.algo_var = tk.StringVar(value=next(iter(self.algorithms)))
        self.msg_var = tk.StringVar(value="Add some processes, then press RUN.")
        self.desc_var = tk.StringVar(value=self.descriptions[self.algo_var.get()])
        self.summary_var = tk.StringVar()

        self._build_screen()

    # ------------------------------------------------------------ building
    def _build_screen(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)     # the tables get the spare space

        ttk.Label(self, style="Sub.TLabel", textvariable=self.desc_var
                  ).grid(row=0, column=0, sticky="w", pady=(0, 8))

        # ---- input box ----
        box = ttk.LabelFrame(self, text="ENTER PROCESSES", padding=10)
        box.grid(row=1, column=0, sticky="ew")

        def put(widget, row, col, span=1):
            widget.grid(row=row, column=col, columnspan=span, padx=4, pady=4)

        put(ttk.Label(box, text="PID"), 0, 0)
        pid_entry = ttk.Entry(box, textvariable=self.pid_var, width=8)
        put(pid_entry, 0, 1)
        put(ttk.Label(box, text="ARRIVAL"), 0, 2)
        arrival_entry = ttk.Entry(box, textvariable=self.arrival_var, width=8)
        put(arrival_entry, 0, 3)
        put(ttk.Label(box, text="BURST"), 0, 4)
        burst_entry = ttk.Entry(box, textvariable=self.burst_var, width=8)
        put(burst_entry, 0, 5)
        put(ttk.Button(box, text="ADD", command=self.add_process), 0, 6)
        put(ttk.Button(box, text="REMOVE SELECTED", command=self.remove_selected), 0, 7)
        put(ttk.Button(box, text="CLEAR ALL", command=self.clear_all), 0, 8)

        put(ttk.Button(box, text="LOAD SAMPLE", command=self.load_sample), 1, 0, 2)
        put(ttk.Label(box, text="RANDOM"), 1, 2)
        put(ttk.Entry(box, textvariable=self.count_var, width=8), 1, 3)
        put(ttk.Button(box, text="GENERATE", command=self.generate_random), 1, 4, 2)
        put(ttk.Label(box, text="ALGORITHM"), 1, 6)
        algo_box = ttk.Combobox(box, textvariable=self.algo_var, state="readonly",
                                width=12, values=list(self.algorithms))
        put(algo_box, 1, 7)
        # When a different algorithm is picked, update the description and
        # clear the old results (they belong to the previous algorithm).
        algo_box.bind("<<ComboboxSelected>>", lambda event: self.algorithm_changed())
        put(ttk.Button(box, text="RUN", command=self.run), 1, 8)

        # Pressing Enter in any of the three boxes adds the process.
        for entry in (pid_entry, arrival_entry, burst_entry):
            entry.bind("<Return>", lambda event: self.add_process())
        arrival_entry.focus_set()

        # ---- message line (errors show in red, successes in green) ----
        self.msg_label = ttk.Label(self, textvariable=self.msg_var, foreground=MUTED)
        self.msg_label.grid(row=2, column=0, sticky="w", pady=(6, 6))

        # ---- the two tables, side by side ----
        tables = ttk.Frame(self)
        tables.grid(row=3, column=0, sticky="nsew")
        tables.columnconfigure(0, weight=2)
        tables.columnconfigure(1, weight=5)
        tables.rowconfigure(0, weight=1)

        left = ttk.LabelFrame(tables, text="PROCESSES", padding=6)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        box_in, self.input_tree = make_table(left, ("PID", "ARRIVAL", "BURST"),
                                             (60, 70, 70))
        box_in.pack(fill="both", expand=True)

        right = ttk.LabelFrame(tables, text="RESULTS", padding=6)
        right.grid(row=0, column=1, sticky="nsew")
        box_out, self.result_tree = make_table(
            right,
            ("PID", "ARRIVAL", "BURST", "START", "FINISH", "TURNAROUND", "WAITING"),
            (60, 80, 70, 70, 70, 100, 80))
        box_out.pack(fill="both", expand=True)

        # ---- averages ----
        ttk.Label(self, textvariable=self.summary_var, foreground=YELLOW
                  ).grid(row=4, column=0, sticky="w", pady=(8, 4))

        # ---- Gantt chart (scrolls sideways when it's long) ----
        gantt_box = ttk.LabelFrame(self, text="GANTT CHART", padding=6)
        gantt_box.grid(row=5, column=0, sticky="ew")
        gantt_box.columnconfigure(0, weight=1)
        self.gantt = tk.Canvas(gantt_box, height=100, bg=BG, highlightthickness=0)
        bar = ttk.Scrollbar(gantt_box, orient="horizontal", command=self.gantt.xview)
        self.gantt.configure(xscrollcommand=bar.set)
        self.gantt.grid(row=0, column=0, sticky="ew")
        bar.grid(row=1, column=0, sticky="ew")

    # ------------------------------------------------------------ helpers
    def _say(self, text, good=False):
        """Show a message under the input box (green if good, red if not)."""
        self.msg_var.set(text)
        self.msg_label.configure(foreground=GOOD if good else BAD)

    def algorithm_changed(self):
        self.desc_var.set(self.descriptions[self.algo_var.get()])
        self._clear_results()
        self._say(f"{self.algo_var.get()} selected. Press RUN.", good=True)

    def _next_free_pid(self):
        """Suggest P1, P2, ... skipping any name already used."""
        used = {p["pid"] for p in self.procs}
        k = len(self.procs) + 1
        while f"P{k}" in used:
            k += 1
        return f"P{k}"

    def _clear_results(self):
        """Empty the results (used when the process list changes)."""
        self.result_tree.delete(*self.result_tree.get_children())
        self.gantt.delete("all")
        self.summary_var.set("")

    def _refresh_input_table(self):
        self.input_tree.delete(*self.input_tree.get_children())
        for p in self.procs:
            self.input_tree.insert("", "end", iid=p["pid"],
                                   values=(p["pid"], p["arrival"], p["burst"]))
        self.pid_var.set(self._next_free_pid())

    # ------------------------------------------------------------ buttons
    def add_process(self):
        try:
            pid = self.pid_var.get().strip()
            if pid == "":
                raise ValueError("PID is required.")
            if any(p["pid"] == pid for p in self.procs):
                raise ValueError(f"PID '{pid}' is already used. Pick a different one.")
            arrival = parse_whole_number(self.arrival_var.get(), "Arrival time", 0)
            burst = parse_whole_number(self.burst_var.get(), "Burst time", 1)
        except ValueError as error:
            self._say(str(error))
            return

        self.procs.append({"pid": pid, "arrival": arrival, "burst": burst})
        self._clear_results()
        self._refresh_input_table()
        self.arrival_var.set("")
        self.burst_var.set("")
        self._say(f"Added {pid}. ({len(self.procs)} processes so far)", good=True)

    def remove_selected(self):
        chosen = set(self.input_tree.selection())
        if not chosen:
            self._say("Click a process in the PROCESSES table first.")
            return
        self.procs = [p for p in self.procs if p["pid"] not in chosen]
        self._clear_results()
        self._refresh_input_table()
        self._say(f"Removed {len(chosen)} process(es).", good=True)

    def clear_all(self):
        self.procs = []
        self._clear_results()
        self._refresh_input_table()
        self._say("Cleared everything.", good=True)

    def load_sample(self):
        self.procs = [dict(p) for p in SAMPLE]    # copies, so SAMPLE stays safe
        self._clear_results()
        self._refresh_input_table()
        self._say("Loaded the sample. Press RUN.", good=True)

    def generate_random(self):
        """Make lots of processes at once, to test with a big dataset."""
        try:
            count = parse_whole_number(self.count_var.get(), "Random count", 1)
        except ValueError as error:
            self._say(str(error))
            return
        self.procs = [
            {"pid": f"P{i}",
             "arrival": random.randint(0, count * 2),
             "burst": random.randint(1, 15)}
            for i in range(1, count + 1)
        ]
        self._clear_results()
        self._refresh_input_table()
        self._say(f"Generated {count} random processes. Press RUN.", good=True)

    def run(self):
        if not self.procs:
            self._say("Add at least one process first (or press LOAD SAMPLE).")
            return
        from logic.cpu_scheduling import summarize
        algorithm = self.algorithms[self.algo_var.get()]
        rows, segments = algorithm(self.procs)

        # fill the results table
        self.result_tree.delete(*self.result_tree.get_children())
        for r in rows:
            self.result_tree.insert("", "end", values=(
                r["pid"], r["arrival"], r["burst"], r["start"], r["finish"],
                r["turnaround"], r["waiting"]))

        # averages
        s = summarize(rows, segments)
        self.summary_var.set(
            f"AVG WAITING: {s['avg_waiting']:.2f}    "
            f"AVG TURNAROUND: {s['avg_turnaround']:.2f}    "
            f"CPU UTILIZATION: {s['cpu_utilization']:.1f}%    "
            f"TOTAL TIME: {s['total_time']}")

        # Gantt chart
        colors = {r["pid"]: BLOCK_COLORS[i % len(BLOCK_COLORS)]
                  for i, r in enumerate(rows)}
        shown = self._draw_gantt(segments, colors)
        note = ""
        if shown < len(segments):
            note = f" (Gantt chart shows the first {shown} blocks only.)"
        self._say(f"{self.algo_var.get()} finished for {len(rows)} processes.{note}",
                  good=True)

    def _draw_gantt(self, segments, colors):
        """Draw the chart. Returns how many blocks were drawn."""
        c = self.gantt
        c.delete("all")
        x, top, height = 12, 14, 44          # where to start drawing, block height
        unit, min_width = 22, 42             # pixels per time unit, narrowest block
        label_font = (self.mono, 10, "bold")
        time_font = (self.mono, 9)

        drawn = segments[:MAX_GANTT_BLOCKS]
        for label, start, end in drawn:
            width = max(min_width, (end - start) * unit)
            fill = IDLE_COLOR if label == "IDLE" else colors[label]
            c.create_rectangle(x, top, x + width, top + height,
                               fill=fill, outline=TEXT, width=2)
            c.create_text(x + width / 2, top + height / 2, text=label,
                          fill=BG, font=label_font)
            c.create_text(x, top + height + 12, text=str(start),
                          fill=MUTED, font=time_font)      # time the block starts
            x += width
        c.create_text(x, top + height + 12, text=str(drawn[-1][2]),
                      fill=MUTED, font=time_font)          # time the last block ends

        c.configure(scrollregion=(0, 0, x + 30, top + height + 30))
        c.xview_moveto(0)
        return len(drawn)