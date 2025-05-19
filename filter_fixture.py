import json

with open("data.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Remove system app entries
filtered_data = [
    entry for entry in data
    if not entry["model"].startswith(
        ("contenttypes.", "auth.permission", "admin.logentry")
    )
]

with open("cleaned_data.json", "w", encoding="utf-8") as f:
    json.dump(filtered_data, f, indent=2)

print(f"Filtered {len(data) - len(filtered_data)} system entries.")
