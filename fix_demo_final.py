p = "run_demo.py"
lines = open(p, "r", encoding="utf-8").readlines()

new_lines = []
for i, line in enumerate(lines):
    # Look for the line that calls process_purchase
    if "await agent.process_purchase(intent_payload=" in line:
        # Get the indentation of this line
        indent = len(line) - len(line.lstrip())
        # Add re-initialize right BEFORE the purchase call
        new_lines.append(" " * indent + "# Ensure wallet backend is initialized before signing\n")
        new_lines.append(" " * indent + "agent._commerce._wallet._backend.initialize()\n")
    new_lines.append(line)

open(p, "w", encoding="utf-8").writelines(new_lines)
print("✅ Added backend re-initialize before purchase call")
