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

print(f"🧠 Total words: {len(all_nouns)} | Already processed: {len(processed_words)} | Remaining: {len(common_nouns)}")
