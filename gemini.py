import asyncio
import os
import csv
import ast
import json
import re
from dotenv import load_dotenv
import google.generativeai as genai
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd

# Load environment variables
load_dotenv()
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-pro")

your_words = [
    "Feather", "Coal", "Pebble", "Leaf", "Paper", "Rock", "Water", "Twig", "Sword", "Shield",
    "Gun", "Flame", "Rope", "Disease", "Cure", "Bacteria", "Shadow", "Light", "Virus", "Sound",
    "Time", "Fate", "Earthquake", "Storm", "Vaccine", "Logic", "Gravity", "Robots", "Stone", "Echo",
    "Thunder", "Karma", "Wind", "Ice", "Sandstorm", "Laser", "Magma", "Peace", "Explosion", "War",
    "Enlightenment", "Nuclear Bomb", "Volcano", "Whale", "Earth", "Moon", "Star", "Tsunami",
    "Supernova", "Antimatter", "Plague", "Rebirth", "Tectonic Shift", "Gamma-Ray Burst",
    "Human Spirit", "Apocalyptic Meteor", "Earth's Core", "Neutron Star"
]

# # Read first 200 lines from nounlist.txt
# with open("nounlist.txt", "r") as f:
#     all_nouns = [line.strip() for line in f.readlines() if line.strip()]


# Load all nouns from nounlist.txt
with open("nounlist.txt", "r") as f:
    all_nouns = [line.strip() for line in f if line.strip()]

# Load already processed words
processed_words = set()
if os.path.exists("large_beat_map_binary.csv"):
    df = pd.read_csv("large_beat_map_binary.csv")
    processed_words = set(df["word"].str.strip().str.lower())

# Filter only unprocessed nouns (case-insensitive match)
common_nouns = [w for w in all_nouns if w.lower() not in processed_words]    



output_csv = "large_beat_map_binary.csv"

def build_batch_prompt(target_words):
    return f"""
You are playing a metaphorical combat game where every word is a weapon. You must determine which of the following 58 words can beat each given target word.

Each player word can beat certain types of targets in poetic, symbolic, physical, scientific, or emotional ways.

A word "beats" another if it can overpower, destroy, disable, outmatch, nullify, counteract, or metaphorically dominate it.

## Examples of reasoning:
- Choose **Gun**, or **Sword**,**Disease** for everything alive that can be killed (e.g., "Lion", "Intruder").
- Choose **Water**, **Tsunami**, or **Ice** for things that can be extinguished or overwhelmed (e.g., "Flame", "Fire", "Desert").
- Choose **Rock**, **Earthquake**, or **Explosion** for things that can be physically broken or destroyed (e.g., "Glass", "PC", "Statue").
- Choose **Rope** or **Gravity** for something that can be tied down, restrained, or pulled (e.g., "Balloon", "Drone", "Elevator").
- Choose **Logic**, **Time**, or **Enlightenment** for abstract concepts (e.g., "Fear", "Ignorance", "Superstition").
- Choose **Vaccine** or **Cure** for diseases or biological threats (e.g., "Virus", "Plague").
- Choose **Sound**, **Echo**, or **Thunder** for silence, secrecy, or communication-related ideas (e.g., "Mute", "Silence", "Secret").
- Choose **Human Spirit**, **Patience**, or **Peace** for emotional or psychological states (e.g., "Hatred", "Grief", "Anxiety").
- Choose **Magma** or **Sandstorm** for landscapes or environments that can be reshaped or eroded.
- Choose **Time** or **Entropy** for things that naturally decay or fade (e.g., "Memory", "Youth", "Beauty").

⚠️ Do not include player words unless there is a **clear and justifiable reason** to do so — based on either real-world logic or strong symbolic metaphor.

---

Your task:

For each of the following 20 target words, return a list of player words (from the 58 below) that beat it.

Target words:
{chr(10).join(f"- {w}" for w in target_words)}

Player words:
{', '.join(your_words)}

Return ONLY a JSON object with one entry per target word. Each value should be a list of player words. Example:
{{
  "Lion": ["Gun", "Sword"],
  "Fire": ["Water", "Ice", "Tsunami"],
  "Fear": ["Logic", "Human Spirit", "Peace"]
}}
"""

failures = 0
MAX_FAILURES = 5

async def build_beat_database():
    # Write CSV headers
    with open(output_csv, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["word"] + your_words)

    # Process in batches of 20
    for i in range(0, len(common_nouns), 20):
        batch = common_nouns[i:i+20]
        prompt = build_batch_prompt(batch)
        print(f"\n🔹 Sending batch {i // 20 + 1}: {batch}")

        try:
            response = model.generate_content(prompt)
            text = response.text.strip()

            # Clean markdown/code block if needed
            if "```" in text:
                match = re.search(r"\{.*\}", text, re.DOTALL)
                if match:
                    text = match.group(0)

            try:
                results = json.loads(text)
                with open(output_csv, "a", newline="") as f:
                    writer = csv.writer(f)
                    for word in batch:
                        word_clean = word.lower()
                        matched = results.get(word) or results.get(word.title()) or results.get(word_clean) or []
                        binary_vector = [1 if w in matched else 0 for w in your_words]
                        writer.writerow([word] + binary_vector)
                        print(f"✅ Mapped {word}: {matched}")
            except Exception as e:
                print(f"⚠️ Failed to parse JSON: {e}\n{text}")

        except Exception as e:
            failures += 1
            print(f"❌ Gemini request failed for batch: {batch}\nError: {e}")
            if failures > MAX_FAILURES:
                print("❌ Too many consecutive failures. Stopping.")
                break

    print(f"\n✅ All done. Results saved to {output_csv}")

# FastAPI support (optional)
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    asyncio.run(build_beat_database())
