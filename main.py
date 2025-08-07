import tkinter as tk
import pandas as pd
import json
import random
import os
from datetime import datetime

DATA_FILE = "lc_flashcards.json"
STATS_FILE = "lc_stats.csv"
NO_WEIGHT = 5     # Repeat more on 'no'
YES_WEIGHT = 2    # Repeat less on 'yes'

# Load Cards
def load_cards():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

# Always create or update today's stats file
def load_stats():
    today = datetime.now().date().isoformat()
    if os.path.exists(STATS_FILE):
        try:
            stats = pd.read_csv(STATS_FILE)
            # Remove today's entries if rerunning
            stats = stats[stats["date"] != today]
        except pd.errors.EmptyDataError:
            # File exists but is empty—start fresh!
            stats = pd.DataFrame(columns=["date", "status", "title"])
    else:
        stats = pd.DataFrame(columns=["date", "status", "title"])
    return stats

def save_stats(stats):
    stats.to_csv(STATS_FILE, index=False)

def build_deck(cards, stats):
    """Build the card deck per spaced repetition stats. Fresh session each run."""
    deck = []
    today = datetime.now().date().isoformat()
    for card in cards:
        recent = stats[(stats["title"] == card["title"]) & (stats["date"] == today)]
        # Check if already solved today; if so, skip
        if not recent.empty and recent["status"].iloc[-1] == "solved":
            continue  # Already solved, skip from deck
        # Pull previous attempts to weight card appropriately
        prev = stats[stats["title"] == card["title"]]
        if not prev.empty and prev["status"].iloc[-1] == "solved":
            deck += [card] * YES_WEIGHT
        else:
            deck += [card] * NO_WEIGHT
    random.shuffle(deck)
    return deck

class FlashcardApp:
    def __init__(self, master):
        self.master = master
        master.title("LeetCode Flashcards")
        self.cards = load_cards()
        self.stats = load_stats()
        self.deck = build_deck(self.cards, self.stats)
        self.index = 0
        self.showing_front = True

        # UI
        self.frame = tk.Frame(master)
        self.frame.pack(padx=14, pady=14)
        self.label = tk.Label(self.frame, text="", wraplength=480, font=('Arial', 13), justify="left", anchor="w")
        self.label.pack(pady=12)
        self.flip_btn = tk.Button(self.frame, text="Show Solution", command=self.flip_card)
        self.flip_btn.pack(pady=6)
        self.yes_btn = tk.Button(self.frame, text="Solved (Yes)", command=lambda: self.mark_card("solved"))
        self.no_btn = tk.Button(self.frame, text="Unsolved (No)", command=lambda: self.mark_card("unsolved"))
        self.yes_btn.pack(side="left", padx=16)
        self.no_btn.pack(side="right", padx=16)
        self.status = tk.Label(self.frame, text="")
        self.status.pack(pady=6)
        self.display_card()

    def display_card(self):
        if self.index >= len(self.deck):
            self.label.config(
                text="🎉 Finished today's flashcards! Check lc_stats.csv for your progress."
            )
            self.flip_btn.config(state='disabled')
            self.yes_btn.config(state='disabled')
            self.no_btn.config(state='disabled')
            return

        card = self.deck[self.index]
        # Card front
        front = (
            f"📝 Title: {card['title']}\n\n"
            f"Description: {card['description']}\n\n"
            f"Example: {card['example']}\n\n"
            f"Constraints: {card['constraints']}"
        )
        self.label.config(text=front)
        self.flip_btn.config(text="Show Solution")
        self.showing_front = True
        self.status.config(text=f"Card {self.index+1}/{len(self.deck)}")

    def flip_card(self):
        card = self.deck[self.index]
        if self.showing_front:
            # Card back
            back = (
                f"(LeetCode #{card['lc_number']}, {card['level']})\n"
                f"Topics: {', '.join(card['topics'])}\n\n"
                f"Hints: {card['hints']}\n\n"
                f"Solution: {card['solution']}"
            )
            self.label.config(text=back)
            self.flip_btn.config(text="Show Question")
            self.showing_front = False
        else:
            self.display_card()

    def mark_card(self, result):
        card = self.deck[self.index]
        today = datetime.now().date().isoformat()

        # Update stats: mark "solved: title"/"unsolved: title"
        display_title = card["title"]
        new_row = pd.DataFrame([{
            "date": today,
            "status": result,
            "title": display_title
        }])
        self.stats = pd.concat([self.stats, new_row], ignore_index=True)
        save_stats(self.stats)

        # Repeat logic: if unsolved, reinsert more
        if result == "unsolved":
            extra = random.randint(1, NO_WEIGHT-1)
            insert_pos = random.randint(self.index+1, len(self.deck))
            for _ in range(extra):
                self.deck.insert(insert_pos, card)
        self.index += 1
        self.display_card()

# MAIN
if __name__ == "__main__":
    root = tk.Tk()
    app = FlashcardApp(root)
    root.mainloop()
