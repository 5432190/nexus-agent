p = "run_demo.py"
content = open(p, "r", encoding="utf-8").read()

# Strategy: Find "Wallet(backend=backend)" and ensure backend.initialize() is right before it
import re

# Pattern: backend = Ed25519Backend(...) followed by anything, then Wallet(backend=backend)
pattern = r'(backend = Ed25519Backend\(key_path=[^)]+\)\n)(.*?)(wallet = Wallet\(backend=backend\))'

def replacer(match):
    backend_line = match.group(1)
    middle = match.group(2)
    wallet_line = match.group(3)
    # Ensure initialize() is called
    if "backend.initialize()" not in middle:
        # Get indentation from backend_line
        indent = len(backend_line) - len(backend_line.lstrip())
        middle = middle + " " * indent + "backend.initialize()\n"
    return backend_line + middle + wallet_line

new_content = re.sub(pattern, replacer, content, flags=re.DOTALL)
open(p, "w", encoding="utf-8").write(new_content)
print("✅ Fixed run_demo.py wallet initialization")
