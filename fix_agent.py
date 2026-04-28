from pathlib import Path

p = Path("nexus_agent/agent.py")
lines = p.read_text(encoding="utf-8").split("\n")

# Find the malformed block and fix it
new_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    
    # Look for the exact malformed pattern
    if "try:" in line and i+1 < len(lines) and "purchase_response = await self._commerce.purchase(payload)" in lines[i+1]:
        # Found the try block - copy it
        new_lines.append(line)  # try:
        new_lines.append(lines[i+1])  # purchase_response = ...
        i += 2
        
        # Skip the stranded signature line and add proper except
        new_lines.append("        except Exception:")
        new_lines.append("            raise")
        
        # Look for the finally block and copy it
        while i < len(lines) and "finally:" not in lines[i]:
            if "signature = self._commerce._wallet.sign_payload(" in lines[i]:
                # Save this line to re-insert later
                signature_lines = []
                while i < len(lines) and ").hex()" not in lines[i]:
                    signature_lines.append(lines[i])
                    i += 1
                signature_lines.append(lines[i])  # ).hex()
                i += 1
                # Re-insert signature AFTER finally block
                new_lines.append("        # Signature moved after finally")
                for sig_line in signature_lines:
                    new_lines.append(sig_line)
            else:
                i += 1
        
        # Copy the finally block
        if i < len(lines):
            new_lines.append(lines[i])  # finally:
            i += 1
            if i < len(lines):
                new_lines.append(lines[i])  # await self._commerce.close()
                i += 1
    else:
        new_lines.append(line)
        i += 1

p.write_text("\n".join(new_lines), encoding="utf-8")
print("✅ Fixed agent.py try/except/finally structure")
