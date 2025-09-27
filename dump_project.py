import os

# Set your project root (current folder)
project_root = "."

# Output file
output_file = "project_dump.txt"

# File extensions you want to include (to avoid collecting unnecessary stuff)
include_exts = [".py", ".html", ".css", ".js", ".json", ".txt", ".md"]

with open(output_file, "w", encoding="utf-8") as outfile:
    for root, dirs, files in os.walk(project_root):
        # Skip virtual environment folders and __pycache__
        if "venv" in dirs:
            dirs.remove("venv")
        if "__pycache__" in dirs:
            dirs.remove("__pycache__")

        for file in files:
            if any(file.endswith(ext) for ext in include_exts):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, "r", encoding="utf-8") as infile:
                        outfile.write(f"\n{'='*80}\n")
                        outfile.write(f"File: {filepath}\n")
                        outfile.write(f"{'='*80}\n\n")
                        outfile.write(infile.read())
                        outfile.write("\n\n")
                except Exception as e:
                    outfile.write(f"\n[Could not read {filepath}: {e}]\n")

print(f"✅ All file contents have been saved to {output_file}")
