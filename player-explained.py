import requests
import pandas as pd
from time import sleep

# === Configuration ===
host = "http://172.18.4.158:8000/"
post_url = f"{host}/submit-word"
get_url = f"{host}/get-word"
status_url = f"{host}/status"
NUM_ROUNDS = 5
FALLBACK_WORD = "Pebble"
FALLBACK_WORD_ID = 3  # Pebble's ID

# === Word Cost Reference (from hackathon docs) ===
word_costs = {
    "Feather": 1, "Coal": 1, "Pebble": 1, "Leaf": 2, "Paper": 2, "Rock": 2,
    "Water": 3, "Twig": 3, "Sword": 4, "Shield": 4, "Gun": 5, "Flame": 5,
    "Rope": 5, "Disease": 6, "Cure": 6, "Bacteria": 6, "Shadow": 7, "Light": 7,
    "Virus": 7, "Sound": 8, "Time": 8, "Fate": 8, "Earthquake": 9, "Storm": 9,
    "Vaccine": 9, "Logic": 10, "Gravity": 10, "Robots": 10, "Stone": 11,
    "Echo": 11, "Thunder": 12, "Karma": 12, "Wind": 13, "Ice": 13,
    "Sandstorm": 13, "Laser": 14, "Magma": 14, "Peace": 14, "Explosion": 15,
    "War": 15, "Enlightenment": 15, "Nuclear Bomb": 16, "Volcano": 16,
    "Whale": 17, "Earth": 17, "Moon": 17, "Star": 18, "Tsunami": 18,
    "Supernova": 19, "Antimatter": 19, "Plague": 20, "Rebirth": 20,
    "Tectonic Shift": 21, "Gamma-Ray Burst": 22, "Human Spirit": 23,
    "Apocalyptic Meteor": 24, "Earth's Core": 25, "Neutron Star": 26,
    "Supermassive Black Hole": 35, "Entropy": 45
}

# === Load Beat Map from CSV ===
df = pd.read_csv("large_beat_map_binary2.csv")
beat_map = {
    row["word"].lower(): row[1:].tolist()
    for _, row in df.iterrows()
}
word_list = df.columns[1:].tolist()

# === Word Selection Logic ===
def what_beats(system_word):
    system_word = system_word.lower()
    print(f"\n🔍 Looking for word to beat: '{system_word}'")

    if system_word not in beat_map:
        print(f"⚠️  '{system_word}' not found in beat map. Using fallback: {FALLBACK_WORD}")
        return FALLBACK_WORD_ID

    binary = beat_map[system_word]

    candidates = [
        (i + 1, word_list[i], word_costs[word_list[i]])
        for i, beat in enumerate(binary)
        if beat == 1 and word_list[i] not in ["Supermassive Black Hole", "Entropy"]
    ]

    if not candidates:
        print(f"⚠️  No known beaters for '{system_word}'. Using fallback: {FALLBACK_WORD}")
        return FALLBACK_WORD_ID

    print("✅ Valid counter-words:")
    for i, word, cost in candidates:
        print(f"   - {word} (ID {i}, cost ${cost})")

    best = min(candidates, key=lambda x: x[2])
    print(f"🏆 Choosing: {best[1]} (ID {best[0]}, cost ${best[2]})")
    return best[0]

# === Main Game Function ===
def play_game(player_id):
    total_cost = 0

    for round_id in range(1, NUM_ROUNDS + 1):
        print(f"\n🎲 === ROUND {round_id} ===")
        round_num = -1
        while round_num != round_id:
            response = requests.get(get_url)
            data = response.json()
            sys_word = data['word']
            round_num = data['round']
            sleep(1)

        if round_id > 1:
            status = requests.get(status_url)
            print("📊 Last round status:", status.json())

        chosen_word_id = what_beats(sys_word)
        payload = {"player_id": player_id, "word_id": chosen_word_id, "round_id": round_id}
        response = requests.post(post_url, json=payload)
        result = response.json()
        print("📬 Submitted:", payload)
        print("📣 Server response:", result)

        # Track cost
        chosen_word = word_list[chosen_word_id - 1]
        word_cost = word_costs[chosen_word]
        round_total = word_cost + (30 if not result.get("success", False) else 0)
        total_cost += round_total
        print(f"💸 Round cost: ${round_total} | Total so far: ${total_cost}")

    print(f"\n🏁 Game complete! Final total cost: ${total_cost}")

# === Run the Game ===
play_game("rUk5kAbAYf")  # Replace with your real player ID

# print(what_beats("audience"))