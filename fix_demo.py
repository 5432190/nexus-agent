p = "run_demo.py"
lines = open(p, "r", encoding="utf-8").readlines()

# Find the line with Ed25519Backend and add .initialize() after it
new_lines = []
for i, line in enumerate(lines):
    new_lines.append(line)
    # Look for: backend = Ed25519Backend(key_path=...)
    if "backend = Ed25519Backend(key_path=" in line and "wallet.pem" in line:
        # Add initialize() on next line with same indentation
        indent = len(line) - len(line.lstrip())
        new_lines.append(" " * indent + "backend.initialize()\n")

open(p, "w", encoding="utf-8").writelines(new_lines)
print("✅ Added backend.initialize() to run_demo.py")
