"""
Derive a Hedera private key from a 24-word HashPack seed phrase.

Usage:
    uv run python derive_key.py

You will be prompted to enter your seed phrase interactively.
The key is NEVER written to a file or sent anywhere.
"""

import hmac
import hashlib
import struct
import sys
import urllib.request
import json
import getpass


# ── BIP-39: mnemonic → 64-byte seed ─────────────────────────────────────────

def mnemonic_to_seed(mnemonic: str, passphrase: str = "") -> bytes:
    mnemonic_bytes = mnemonic.strip().encode("utf-8")
    salt = ("mnemonic" + passphrase).encode("utf-8")
    return hashlib.pbkdf2_hmac("sha512", mnemonic_bytes, salt, 2048)


# ── SLIP-0010: seed → ED25519 private key at given path ─────────────────────

def slip10_ed25519(seed: bytes, path: str) -> bytes:
    """Derive raw 32-byte ED25519 private key via SLIP-0010."""
    # Master node
    raw = hmac.new(b"ed25519 seed", seed, hashlib.sha512).digest()
    key, chain = raw[:32], raw[32:]

    for part in path.split("/"):
        if part in ("m", ""):
            continue
        hardened = part.endswith("'")
        index = int(part.rstrip("'"))
        if hardened:
            index |= 0x80000000
        # All ED25519 SLIP-0010 derivations must be hardened
        if not hardened:
            raise ValueError(f"Non-hardened derivation not supported for ED25519: {part}")
        data = b"\x00" + key + struct.pack(">I", index)
        raw = hmac.new(chain, data, hashlib.sha512).digest()
        key, chain = raw[:32], raw[32:]

    return key


# ── DER encoding ─────────────────────────────────────────────────────────────

ED25519_PRIVATE_DER_PREFIX = bytes.fromhex("302e020100300506032b657004220420")
ED25519_PUBLIC_DER_PREFIX  = bytes.fromhex("302a300506032b6570032100")


def private_key_to_der_hex(raw: bytes) -> str:
    return (ED25519_PRIVATE_DER_PREFIX + raw).hex()


def public_key_from_private(raw_private: bytes) -> bytes:
    """Derive raw 32-byte ED25519 public key from private key."""
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    return Ed25519PrivateKey.from_private_bytes(raw_private).public_key().public_bytes_raw()


def public_key_to_der_hex(raw: bytes) -> str:
    return (ED25519_PUBLIC_DER_PREFIX + raw).hex()


# ── Mirror Node lookup ───────────────────────────────────────────────────────

def lookup_account(public_key_der_hex: str, network: str = "testnet") -> str | None:
    """Return the account ID for a public key, or None if not found."""
    url = (
        f"https://{network}.mirrornode.hedera.com/api/v1/accounts"
        f"?publickey={public_key_der_hex}&limit=1"
    )
    try:
        with urllib.request.urlopen(url, timeout=8) as resp:
            data = json.loads(resp.read())
            accounts = data.get("accounts", [])
            if accounts:
                return accounts[0]["account"]
    except Exception:
        pass
    return None


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("=" * 55)
    print("  Hedera Key Derivation (BIP-39 + SLIP-0010 ED25519)")
    print("=" * 55)
    print()
    print("Enter your 24-word seed phrase below.")
    print("(Input is hidden — it won't show as you type)")
    print()

    phrase = getpass.getpass("Seed phrase: ").strip()
    words = phrase.split()

    if len(words) not in (12, 18, 24):
        print(f"\nExpected 12, 18, or 24 words — got {len(words)}. Check for typos.")
        sys.exit(1)

    print(f"\nDeriving from {len(words)}-word phrase…")

    seed = mnemonic_to_seed(phrase)

    # HashPack uses m/44'/3030'/0'/0'/0' for ED25519 accounts
    paths = [
        "m/44'/3030'/0'/0'/0'",   # standard (most HashPack accounts)
        "m/44'/3030'/0'",          # legacy path
    ]

    results = []
    for path in paths:
        raw_priv  = slip10_ed25519(seed, path)
        raw_pub   = public_key_from_private(raw_priv)
        priv_der  = private_key_to_der_hex(raw_priv)
        pub_der   = public_key_to_der_hex(raw_pub)

        print(f"\n── Path: {path}")
        print(f"   Private key : {priv_der}")
        print(f"   Public key  : {pub_der}")

        print(f"   Looking up account on testnet…", end=" ", flush=True)
        account_id = lookup_account(pub_der)
        if account_id:
            print(f"✓  Account ID: {account_id}")
        else:
            print("not found on testnet (may be mainnet or unfunded)")

        results.append((path, priv_der, pub_der, account_id))

    # ── Match against a known account ID ────────────────────────────────────
    print()
    known = input(
        "Enter your Hedera account ID to auto-identify the correct key\n"
        "(e.g. 0.0.12345 — press Enter to skip): "
    ).strip()

    matched = None
    if known:
        print(f"\nLooking up public key for {known} on testnet…", end=" ", flush=True)
        try:
            url = f"https://testnet.mirrornode.hedera.com/api/v1/accounts/{known}"
            with urllib.request.urlopen(url, timeout=8) as resp:
                data = json.loads(resp.read())
                on_chain_pub = data.get("key", {}).get("key", "").lower()
                print(f"found  (public key: {on_chain_pub[:20]}…)")
        except Exception as e:
            on_chain_pub = ""
            print(f"failed ({e})")

        if on_chain_pub:
            for path, priv, pub, acc in results:
                # Mirror node returns the raw hex public key (no DER prefix)
                raw_pub_hex = pub[len(ED25519_PUBLIC_DER_PREFIX.hex()):]
                if raw_pub_hex.lower() == on_chain_pub.lower() or pub.lower() == on_chain_pub.lower():
                    matched = (path, priv, pub)
                    break

    print()
    print("=" * 55)
    print("  RESULTS")
    print("=" * 55)

    if matched:
        path, priv, pub = matched
        print(f"\n✅  MATCH FOUND  —  Path: {path}")
        print(f"\n   Account ID   → {known}")
        print(f"   Private Key  → {priv}")
        print(f"   Public Key   → {pub}")
    else:
        for path, priv, pub, acc in results:
            print(f"\nPath: {path}")
            if acc:
                print(f"  Account ID   → {acc}")
            print(f"  Private Key  → {priv}")
            print(f"  Public Key   → {pub}")

    print()
    print("Put the matching private key into your .env as SHOP_PRIVATE_KEY=...")
    print("⚠  Keep your seed phrase and private key offline and private.")


if __name__ == "__main__":
    main()
