import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd
import itertools
import threading
import random
import csv

font = ("Arial", 11)

# ------------------ Core Frequency Data ------------------
class FreqData:
    def __init__(self, text):
        self.fA = {}
        self.fB = {}
        self._parse(text)

    def _parse(self, text):
        lines = text.strip().split('\n')
        if len(lines) != 3: return
        try:
            nums, freqsA, freqsB = [[int(n) for n in line.split()] for line in lines]
            self.fA = dict(zip(nums, freqsA))
            self.fB = dict(zip(nums, freqsB))
        except:
            pass

# ------------------ Priority Scoring ------------------
def calculate_priority_score(num, freq_data, mode):
    fA = freq_data.fA.get(num, 0)
    fB = freq_data.fB.get(num, 0)

    if mode == "EuroMillions":
        if fA >= 6 and (fB == 0 or fB == 1):
            return 100
        if (fA == 2 or fA == 3) and fB == 0:
            return 75
        if fA >= 6 and fB > 1:
            return 25
    else:
        if fA >= 10 and (fB == 0 or fB == 1):
            return 100
        if (fA == 3 or fA == 4) and fB == 0:
            return 75
        if fA >= 10 and fB > 1:
            return 25

    return 0

# ------------------ Pool Building ------------------
def build_child_pools(parent_draws, freq_data, mode):
    pools = {}
    all_parents = set(sum(parent_draws, []))
    limit = 50 if mode == "EuroMillions" else 69

    for i, parents in enumerate(zip(*parent_draws), start=1):
        pool = set()
        for p in parents:
            for shift in (-10, -9, 9, 10):
                c = p + shift
                if 1 <= c <= limit and c not in all_parents:
                    pool.add(c)
        pools[f"P{i}"] = sorted(list(pool), key=lambda x: calculate_priority_score(x, freq_data, mode), reverse=True)
    return pools

# ------------------ Combination Generation ------------------
def has_same_last_digit_pair(combo):
    last_digits = [num % 10 for num in combo]
    return len(last_digits) != len(set(last_digits))

def generate_combinations(pools, freq_data, mode, limit=5):
    rules = {
        0: {"P1", "P2"},
        1: {"P1", "P2", "P3"},
        2: {"P2", "P3", "P4"},
        3: {"P3", "P4", "P5"},
        4: {"P4", "P5"}
    }

    all_paths = []

    def search(slot, path, used_pools, used_nums):
        if slot == 5:
            all_paths.append(path[:])
            return
        for pool in rules.get(slot, []):
            if pool in used_pools: continue
            for child in pools.get(pool, []):
                if child in used_nums: continue
                path.append((child, pool, freq_data.fA.get(child, 0), freq_data.fB.get(child, 0)))
                search(slot + 1, path, used_pools | {pool}, used_nums | {child})
                path.pop()

    search(0, [], set(), set())

    # Unique combos only
    unique_combos = {}
    for path in all_paths:
        combo = tuple(sorted(num for num, *_ in path))
        if combo not in unique_combos:
            unique_combos[combo] = path

    candidates_with_pair = [(combo, path) for combo, path in unique_combos.items() if has_same_last_digit_pair(combo)]

    random.shuffle(candidates_with_pair)

    final_paths = []
    all_used_numbers = set()
    for combo, path in candidates_with_pair:
        if all_used_numbers.isdisjoint(combo):
            final_paths.append(path)
            all_used_numbers.update(combo)
            if len(final_paths) == limit:
                break

    return final_paths

# ------------------ Save Pools to CSV ------------------
def save_pools_to_csv():
    try:
        freq_data = FreqData(freq_entry.get("1.0", tk.END))
        if not freq_data.fA:
            messagebox.showerror("Input Error", "Please paste valid frequency data with 3 lines.")
            return

        mode = current_mode.get()

        d1 = [int(e.get()) for e in draw1_entries if e.get().strip().isdigit()]
        d2 = [int(e.get()) for e in draw2_entries if e.get().strip().isdigit()]
        d3 = [int(e.get()) for e in draw3_entries if e.get().strip().isdigit()]

        if mode == "Powerball":
            if not (len(d1) == 5 and len(d2) == 5 and len(d3) == 5):
                messagebox.showerror("Error", "Please enter exactly 5 numbers for each of the three draws.")
                return
            parents = [d1, d2, d3]
        else:
            if not (len(d1) == 5 and len(d2) == 5):
                messagebox.showerror("Error", "Please enter exactly 5 numbers for both draws.")
                return
            parents = [d1, d2]

        pools = build_child_pools(parents, freq_data, mode)

        with open("child_pools.csv", "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Pool", "Numbers"])
            for pool_name, numbers in pools.items():
                writer.writerow([pool_name, " ".join(map(str, numbers))])

        messagebox.showinfo("Saved", "Child pools saved to child_pools.csv")
    except Exception as e:
        messagebox.showerror("Error", str(e))

# ------------------ GUI Logic ------------------
def load_excel_freq():
    filepath = filedialog.askopenfilename(filetypes=[("Excel Files", "*.xlsx *.xls")])
    if not filepath: return
    try:
        df = pd.read_excel(filepath, header=None)
        if len(df.index) < 3:
            messagebox.showerror("Excel Error", "Excel file must contain 3 rows:", )
            return
        nums, fA, fB = [df.iloc[i].dropna().astype(int).tolist() for i in range(3)]
        text_to_paste = f"{' '.join(map(str, nums))}\n{' '.join(map(str, fA))}\n{' '.join(map(str, fB))}"
        freq_entry.delete("1.0", tk.END)
        freq_entry.insert("1.0", text_to_paste)
    except Exception as e:
        messagebox.showerror("Excel Error", f"Could not read Excel file.\n{e}")

def run_analysis():
    try:
        freq_data = FreqData(freq_entry.get("1.0", tk.END))
        if not freq_data.fA:
            messagebox.showerror("Input Error", "Please paste valid frequency data with 3 lines.")
            return

        mode = current_mode.get()

        d1 = [int(e.get()) for e in draw1_entries if e.get().strip().isdigit()]
        d2 = [int(e.get()) for e in draw2_entries if e.get().strip().isdigit()]
        d3 = [int(e.get()) for e in draw3_entries if e.get().strip().isdigit()]

        if mode == "Powerball":
            if not (len(d1) == 5 and len(d2) == 5 and len(d3) == 5):
                messagebox.showerror("Error", "Please enter exactly 5 numbers for each of the three draws.")
                return
            parents = [d1, d2, d3]
        else:
            if not (len(d1) == 5 and len(d2) == 5):
                messagebox.showerror("Error", "Please enter exactly 5 numbers for both draws.")
                return
            parents = [d1, d2]

        pools = build_child_pools(parents, freq_data, mode)
        preds = generate_combinations(pools, freq_data, mode, limit=5)

        pred_out.delete("1.0", tk.END)
        pred_out.insert(tk.END, "⚡ These are not random picks — they are rule-based combinations following frequency and lineage rules.\n")
        pred_out.insert(tk.END, "Disclaimer: This program is for educational purposes only. It does not guarantee lottery results.\n\n")


        if not preds:
            pred_out.insert(tk.END, "--- 0 Predictions Generated ---\n\nCould not find any disjoint combinations that satisfy your rules.")
        else:
            pred_out.insert(tk.END, f"--- Found {len(preds)}/5 Disjoint Predictions ---\n")
            pred_out.insert(tk.END, "(Biased towards 'Sleeping Giants' and 'Deep Sleepers')\n\n")

        for i, path in enumerate(preds, 1):
            combo = sorted(num for num, *_ in path)
            pred_out.insert(tk.END, f"{i}. Predicted Numbers: {combo}\n")
            pred_out.insert(tk.END, "   Lineage (fA/fB):\n")
            for num, pool, fA_val, fB_val in path:
                pred_out.insert(tk.END, f"      {num} ← {pool} [fA:{fA_val}, fB:{fB_val}]\n")
    finally:
        generate_btn.config(state=tk.NORMAL)

def start_analysis_thread():
    generate_btn.config(state=tk.DISABLED)
    pred_out.delete("1.0", tk.END)
    pred_out.insert(tk.END, "Analyzing using your priority rules...")
    analysis_thread = threading.Thread(target=run_analysis)
    analysis_thread.start()

# ------------------ Mode Switching ------------------
def set_mode(mode):
    current_mode.set(mode)
    if mode == "EuroMillions":
        for e in draw3_entries:
            e.grid_remove()
        freq_frame.config(text="Paste or Load Frequencies (3 Lines: Nums, Freq50, Freq10)")
    else:
        for e in draw3_entries:
            e.grid()
        freq_frame.config(text="Paste or Load Frequencies (3 Lines: Nums, Freq75, Freq20)")

# ------------------ GUI ------------------
import os
root = tk.Tk()
icon_path = os.path.join(os.path.dirname(__file__), "lotto.ico")
root.iconbitmap(icon_path)

root.title("Priority Prediction Engine (Dual Mode)")
root.geometry("800x600")
root.configure(bg="lightgreen")

current_mode = tk.StringVar(root)
current_mode.set("Powerball")

# --- Menu ---
menu = tk.Menu(root)
root.config(menu=menu)
game_menu = tk.Menu(menu, tearoff=0)
menu.add_cascade(label="Choose Game", menu=game_menu)
game_menu.add_command(label="EuroMillions (10 numbers)", command=lambda: set_mode("EuroMillions"))
game_menu.add_command(label="Powerball (15 numbers)", command=lambda: set_mode("Powerball"))

# --- Draw input frame ---
draw_frame = tk.LabelFrame(root, text="Enter Draws", padx=10, pady=10, font=("Arial", 12, "bold"),bg="lightblue" )
draw_frame.pack(padx=10, pady=(10, 5))

draw1_entries, draw2_entries, draw3_entries = [], [], []
tk.Label(draw_frame, text="Draw 1 (Most Recent):", font=font,bg="lightblue" ).grid(row=0, column=0, sticky="w", pady=2)
for i in range(5):
    e = tk.Entry(draw_frame, width=5, font=font, justify="center")
    e.grid(row=0, column=i+1, padx=3); draw1_entries.append(e)

tk.Label(draw_frame, text="Draw 2 (Previous):", font=font,bg="lightblue" ).grid(row=1, column=0, sticky="w", pady=2)
for i in range(5):
    e = tk.Entry(draw_frame, width=5, font=font, justify="center")
    e.grid(row=1, column=i+1, padx=3); draw2_entries.append(e)

tk.Label(draw_frame, text="Draw 3 (Next Previous):", font=font,bg="lightblue" ).grid(row=2, column=0, sticky="w", pady=2)
for i in range(5):
    e = tk.Entry(draw_frame, width=5, font=font, justify="center")
    e.grid(row=2, column=i+1, padx=3); draw3_entries.append(e)

btn_frame_top = tk.Frame(draw_frame); btn_frame_top.grid(row=3, column=0, columnspan=6, pady=10)
tk.Button(btn_frame_top, text="Clear All", font=font,bg="lightblue", 
          command=lambda: [e.delete(0, tk.END) for e in draw1_entries+draw2_entries+draw3_entries]).pack(side="left", padx=5)

# --- Frequency frame ---
freq_frame = tk.LabelFrame(root, text="Paste or Load Frequencies", padx=10, pady=10, font=("Arial", 12, "bold"),bg="lightblue" )
freq_frame.pack(fill="x", padx=10, pady=(5, 5))
freq_entry = tk.Text(freq_frame, height=4, width=120, font=font); freq_entry.pack()

# --- Buttons ---
btn_frame_mid = tk.Frame(root); btn_frame_mid.pack(pady=5)
tk.Button(btn_frame_mid, text="Load 3-Row Excel", font=font,bg="lightgreen", command=load_excel_freq).pack(side="left", padx=5)
generate_btn = tk.Button(btn_frame_mid, text="Generate Predictions", font=font,bg="lightgreen", command=start_analysis_thread)
generate_btn.pack(side="left", padx=5)
tk.Button(btn_frame_mid, text="Save Pools", font=font,bg="lightgreen", command=save_pools_to_csv).pack(side="left", padx=5)

# --- Predictions output ---
tk.Frame(root, height=2, bg="lightblue").pack(fill="x", padx=10, pady=5)
pred_frame = tk.LabelFrame(root, text="Predictions", padx=10, pady=10, font=("Arial", 12, "bold"),bg="lightblue")
pred_frame.pack(fill="both", expand=True, padx=10, pady=(5, 10))
pred_out = tk.Text(pred_frame, height=12, width=80, wrap="word", bg="#f4f4f4", font=font)
pred_out.pack(fill="both", expand=True)

# Disclaimer label at bottom of GUI
disclaimer_label = tk.Label(root, text="This program is for educational purposes only. It does not guarantee lottery results.", font=("Arial", 9), fg="red")
disclaimer_label.pack(pady=5)

# Default mode
set_mode("Powerball")

root.mainloop()
