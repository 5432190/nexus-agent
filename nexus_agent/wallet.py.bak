"""Wallet signing implementation for Nexus Agent."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from cryptography.exceptions import UnsupportedAlgorithm
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from .exceptions import WalletError


class SigningBackend(Protocol):
    """Protocol for a signing backend."""

    def initialize(self) -> None:
        ...

    def sign(self, data: bytes) -> bytes:
        ...

    def close(self) -> None:
        ...


class Ed25519Backend:
    """Ed25519 signing backend using a private key loaded from disk."""

    def __init__(self, key_path: str) -> None:
        self._key_path = Path(key_path)
        self._key: Ed25519PrivateKey | None = None

    def initialize(self) -> None:
        if not self._key_path.exists():
            raise WalletError(f"Signing key file not found: {self._key_path}")

        file_mode = self._key_path.stat().st_mode & 0o777
        if file_mode != 0o600:
            raise WalletError(
                f"Signing key file must be chmod 600, found {oct(file_mode)}"
            )

        key_bytes = self._key_path.read_bytes()
        try:
            private_key = serialization.load_pem_private_key(
                key_bytes,
                password=None,
            )
        except (ValueError, UnsupportedAlgorithm) as exc:
            raise WalletError("Failed to load Ed25519 private key") from exc

        if not isinstance(private_key, Ed25519PrivateKey):
            raise WalletError("Loaded key is not an Ed25519 private key")

        self._key = private_key

    def sign(self, data: bytes) -> bytes:
        if self._key is None:
            raise WalletError("Signing backend is not initialized")
        return self._key.sign(data)

    def close(self) -> None:
        self._key = None


class Wallet:
    """Wallet abstraction that delegates signing to a backend."""

    def __init__(self, backend: SigningBackend) -> None:
        self._backend = backend

    def initialize(self) -> None:
        self._backend.initialize()

    def close(self) -> None:
        self._backend.close()

    def sign_payload(self, payload: bytes) -> bytes:
        return self._backend.sign(payload)
