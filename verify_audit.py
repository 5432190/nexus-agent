#!/usr/bin/env python
"""Verify audit chain integrity end-to-end."""

import argparse
import json
import sys
from pathlib import Path

from nexus_agent.audit import AuditChain


def main():
    parser = argparse.ArgumentParser(
        description="Verify Nexus Agent audit chain integrity."
    )
    parser.add_argument(
        "--audit-log",
        required=True,
        help="Path to audit log JSONL file",
    )
    parser.add_argument(
        "--public-key",
        default=None,
        help="Path to Ed25519 public key PEM file (optional, auto-detect from env if not provided)",
    )

    args = parser.parse_args()

    audit_log_path = Path(args.audit_log)
    if not audit_log_path.exists():
        print(f"❌ Audit log not found: {audit_log_path}")
        return 1

    # Determine public key path
    if args.public_key:
        public_key_path = Path(args.public_key)
    else:
        # Try common locations
        candidates = [
            Path.home() / ".nexus" / "agent.pub",
            Path("/opt/nexus/keys/agent.pub"),
            Path("./keys/agent.pub"),
        ]
        public_key_path = None
        for candidate in candidates:
            if candidate.exists():
                public_key_path = candidate
                break

        if not public_key_path:
            print("❌ Public key not found. Tried:")
            for candidate in candidates:
                print(f"   - {candidate}")
            print("\nProvide with --public-key flag")
            return 1

    try:
        chain = AuditChain(str(audit_log_path), str(public_key_path))
    except Exception as e:
        print(f"❌ Failed to initialize audit chain: {e}")
        return 1

    # Verify chain integrity
    if not chain.verify_chain():
        print("❌ Chain verification failed: signature or hash mismatch detected")
        return 1

    # Get last hash and entry count
    last_hash = chain.get_last_hash()
    entry_count = sum(
        1 for line in audit_log_path.read_text().splitlines() if line.strip()
    )

    print(f"✅ Chain verified from genesis to {last_hash[:16]}...")
    print(f"   Total entries: {entry_count}")
    print(f"   Public key: {public_key_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
