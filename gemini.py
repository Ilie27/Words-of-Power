import asyncio
import os
import csv
import ast
import re
from dotenv import load_dotenv
import google.generativeai as genai
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import pandas as pd

# Load environment variables
load_dotenv()

# Configure Gemini API key
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

# Use the most capable Gemini model for reasoning
model = genai.GenerativeModel("gemini-1.5-pro")

# Your 58 powerful words (excluding Supermassive Black Hole and Entropy)
your_words = [
    "Feather", "Coal", "Pebble", "Leaf", "Paper", "Rock", "Water", "Twig", "Sword", "Shield",
    "Gun", "Flame", "Rope", "Disease", "Cure", "Bacteria", "Shadow", "Light", "Virus", "Sound",
    "Time", "Fate", "Earthquake", "Storm", "Vaccine", "Logic", "Gravity", "Robots", "Stone", "Echo",
    "Thunder", "Karma", "Wind", "Ice", "Sandstorm", "Laser", "Magma", "Peace", "Explosion", "War",
    "Enlightenment", "Nuclear Bomb", "Volcano", "Whale", "Earth", "Moon", "Star", "Tsunami",
    "Supernova", "Antimatter", "Plague", "Rebirth", "Tectonic Shift", "Gamma-Ray Burst",
    "Human Spirit", "Apocalyptic Meteor", "Earth's Core", "Neutron Star"
]

# Load the first 5 words from freq-words.csv (no header)
noun_df = pd.read_csv("freq-words.csv", header=None)
common_nouns = noun_df.iloc[:100, 0].tolist()


# Output CSV path
output_csv = "beat_map_binary.csv"

# Gemini prompt template
def build_prompt(noun):
    return f"""
You are playing a metaphorical combat game, similar to rock-paper-scissors.

You are given a target word: "{noun}".
Your task is to decide which of the following 58 words could metaphorically, symbolically, or realistically "beat" the target word.

A word can "beat" another in many ways — it might overpower, break, contain, cure, counteract, replace, outlast, or symbolically dominate it. Be creative and flexible. Consider both poetic metaphors and real-world cause-effect relationships.

Here are the 58 candidate words:
{', '.join(your_words)}

Return ONLY a JSON array (not markdown) of the names of the words from the list above that beat "{noun}".

Example of valid output:
["Water", "Tsunami", "Cure", "Peace"]
"""

# Main function to call Gemini and collect data
async def build_beat_database():
    # Prepare the CSV file with headers
    with open(output_csv, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["word"] + your_words)

    for noun in common_nouns:
        prompt = build_prompt(noun)
        print("Sending prompt to Gemini:\n", prompt)
        try:
            response = model.generate_content(prompt)
            text = response.text.strip()
            print(f"Raw Gemini response (with markers): >>{text}<<")

            # Clean response of markdown code block if present
            if "```" in text:
                parts = re.findall(r"\[.*?\]", text, re.DOTALL)
                if parts:
                    text = parts[0].replace("\n", "").strip()

            try:
                result = ast.literal_eval(text)
                if isinstance(result, list):
                    binary_vector = [1 if word in result else 0 for word in your_words]
                    with open(output_csv, "a", newline="") as csvfile:
                        writer = csv.writer(csvfile)
                        writer.writerow([noun] + binary_vector)
                    print(f"Mapped {noun}: {binary_vector}")
                else:
                    print(f"Unexpected format (not a list) for {noun}: {result}")
            except Exception as e:
                print(f"Failed to parse result for {noun}: {text}\nError: {e}")
        except Exception as e:
            print(f"Failed to process {noun}: {e}")

    print(f"Completed. Final results saved to {output_csv}")

# FastAPI (optional, not used here, but kept for compatibility)
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Run the script
if __name__ == "__main__":
    asyncio.run(build_beat_database())
