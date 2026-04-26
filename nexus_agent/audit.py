"""Audit logging for Nexus Agent with append-only JSONL and chain verification."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.hazmat.primitives.serialization import load_pem_public_key

from .memory import atomic_write_text


@dataclass
class AuditEntry:
    timestamp: str
    transaction_id: str
    merchant_id: str
    amount: str
    category: str
    signature: str
    previous_hash: str
    metadata: dict[str, Any]


class AuditChain:
    """Append-only audit chain with SHA256 linking."""

    def __init__(self, audit_file: str, public_key_path: str) -> None:
        self._audit_path = Path(audit_file)
        self._public_key_path = Path(public_key_path)
        self._public_key = self._load_public_key()
        self._ensure_audit_file()

    def _load_public_key(self) -> Ed25519PublicKey:
        public_key_bytes = self._public_key_path.read_bytes()
        public_key = load_pem_public_key(public_key_bytes)
        if not isinstance(public_key, Ed25519PublicKey):
            raise ValueError("Audit public key must be Ed25519")
        return public_key

    def _ensure_audit_file(self) -> None:
        if not self._audit_path.exists():
            self._audit_path.parent.mkdir(parents=True, exist_ok=True)
            atomic_write_text(self._audit_path, "", mode=0o600)

    def _entry_hash(self, entry: dict[str, Any]) -> str:
        serialized = json.dumps(entry, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def append(self, entry: AuditEntry) -> None:
        record = asdict(entry)
        json_line = json.dumps(record, sort_keys=True)
        with self._audit_path.open("a", encoding="utf-8") as handle:
            handle.write(json_line)
            handle.write("\n")

    def verify_chain(self) -> bool:
        previous_hash = ""
        with self._audit_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                record = json.loads(line)
                if record.get("previous_hash", "") != previous_hash:
                    return False

                signature_hex = record.get("signature", "")
                if not signature_hex:
                    return False

                signing_payload = self._signing_payload(record)
                try:
                    self._public_key.verify(bytes.fromhex(signature_hex), signing_payload)
                except InvalidSignature:
                    return False

                previous_hash = self._entry_hash(record)
        return True

    def get_last_hash(self) -> str:
        last_hash = ""
        with self._audit_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                record = json.loads(line)
                last_hash = self._entry_hash(record)
        return last_hash

    def _signing_payload(self, record: dict[str, Any]) -> bytes:
        signing_record = {k: record[k] for k in record if k != "signature"}
        serialized = json.dumps(signing_record, sort_keys=True, separators=(",", ":"))
        return serialized.encode("utf-8")
