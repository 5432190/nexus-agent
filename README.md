# nexus-agent

## ðŸš€ Local Development

### Fixed Wallet Generation Script
```bash
python -c "
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization
key = Ed25519PrivateKey.generate()
pem = key.private_bytes(
    serialization.Encoding.PEM,
    serialization.PrivateFormat.PKCS8,
    serialization.NoEncryption()
)
Path.home().joinpath('.nexus/wallet.pem').write_bytes(pem)
" && chmod 600 ~/.nexus/wallet.pem
```

### âš ï¸ Platform Notes

**Windows Users**: Run in WSL2 or Git Bash. Native Windows support is not currently guaranteed.
```bash
# Windows: Use WSL2
wsl
# Then follow Linux instructions above
```

### ðŸ”§ Troubleshooting

**If `pytest` fails**:
```bash
# 1. Check Python version
python --version  # Must be 3.10+

# 2. Reinstall dependencies
pip install -e ".[test,llm]" --force-reinstall

# 3. Clear pytest cache
rm -rf .pytest_cache __pycache__
pytest tests/ -v
```
