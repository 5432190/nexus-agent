p = "nexus_agent/agent.py"
lines = open(p, "r", encoding="utf-8").readlines()

# Find the start marker: line with payload["merchant_id"] = intent.merchant_id
start_idx = None
for i, line in enumerate(lines):
    if 'payload["merchant_id"] = intent.merchant_id' in line:
        start_idx = i + 1  # Start replacing AFTER this line
        break

# Find the end marker: line with audit_entry = AuditEntry(
end_idx = None
for i, line in enumerate(lines):
    if "audit_entry = AuditEntry(" in line and i > start_idx:
        end_idx = i  # End replacing BEFORE this line
        break

if start_idx and end_idx:
    # The correct code to insert between markers
    correct_code = '''
        self._commerce.initialize()
        try:
            purchase_response = await self._commerce.purchase(payload)
        except Exception:
            raise
        finally:
            await self._commerce.close()
        
        # Sign the payload for audit (after commerce call completes)
        signature = self._commerce._wallet.sign_payload(
            json.dumps(payload, sort_keys=True).encode("utf-8")
        ).hex()
'''
    
    # Replace the broken section
    new_lines = lines[:start_idx] + [correct_code + "\n"] + lines[end_idx:]
    open(p, "w", encoding="utf-8").writelines(new_lines)
    print("✅ Fixed agent.py using marker-based replacement")
else:
    print(f"⚠️ Markers not found: start={start_idx}, end={end_idx}")
    # Debug: show lines around where we expected markers
    for i, line in enumerate(lines[140:170], start=141):
        print(f"{i}: {line.rstrip()}")
