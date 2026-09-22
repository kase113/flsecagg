#!/usr/bin/env python3
"""Check persisted-message recovery; this is not a DPSS or NIZK implementation."""

import copy
import itertools
import json
import math
import secrets
import subprocess
import sys

from nacl import bindings
from nacl.exceptions import CryptoError
from nacl.public import PrivateKey, SealedBox
from nacl.signing import SigningKey, VerifyKey


ORDER = 2**252 + 27742317777372353535851937790883648493
IDENTITY = b"\x01" + bytes(31)
CONTEXT = {"instance": "sid_b", "generation": 2, "members": [1, 2, 3, 4], "threshold": 3}


def multiply(scalar, point):
    scalar %= ORDER
    if scalar == 0 or point == IDENTITY:
        return IDENTITY
    return bindings.crypto_scalarmult_ed25519_noclamp(scalar.to_bytes(32, "little"), point)


def base(scalar):
    return multiply(scalar, bindings.crypto_scalarmult_ed25519_base_noclamp((1).to_bytes(32, "little")))


def make_fixture():
    sender = SigningKey.generate()
    recipients = [PrivateKey.generate() for _ in range(4)]
    batch = {}
    for index, recipient in enumerate(recipients):
        message = f"sid_a/2/recipient_{index}:".encode() + b"designated Reduce input"
        batch[f"recipient_{index}"] = SealedBox(recipient.public_key).encrypt(sender.sign(message)).hex()

    polynomial = [secrets.randbelow(ORDER - 1) + 1 for _ in range(3)]
    public_key = base(polynomial[0])
    client_coefficients = ((1, 2, -3), (4, -1, 1), (-2, -1, -2))
    ciphertexts = []
    for coordinate in zip(*client_coefficients):
        first, second = IDENTITY, IDENTITY
        for coefficient in coordinate:
            randomizer = secrets.randbelow(ORDER - 1) + 1
            first = bindings.crypto_core_ed25519_add(first, base(randomizer))
            encrypted = bindings.crypto_core_ed25519_add(base(coefficient), multiply(randomizer, public_key))
            second = bindings.crypto_core_ed25519_add(second, encrypted)
        ciphertexts.append([first.hex(), second.hex()])
    partials = []
    for member in CONTEXT["members"]:
        share = sum(coefficient * member**degree for degree, coefficient in enumerate(polynomial)) % ORDER
        partials.append({
            "context": dict(CONTEXT), "member": member,
            "points": [multiply(share, bytes.fromhex(first)).hex() for first, _ in ciphertexts],
        })
    return {
        "receiver_key": bytes(recipients[0]).hex(), "sender_public": bytes(sender.verify_key).hex(),
        "batch": batch,
        "opening": {"context": dict(CONTEXT), "ciphertexts": ciphertexts, "partials": partials, "bound": 48},
    }


def recover_input(packet, receiver_key, sender_key):
    message = sender_key.verify(SealedBox(receiver_key).decrypt(packet))
    prefix = b"sid_a/2/recipient_0:"
    if not message.startswith(prefix):
        raise ValueError("handoff context mismatch")
    return message[len(prefix):]


def combine(artifact):
    context = artifact["context"]
    partials = artifact["partials"]
    members = [partial["member"] for partial in partials]
    if context != CONTEXT:
        raise ValueError("unexpected opening context")
    if len(set(members)) != len(members) or len(members) < context["threshold"]:
        raise ValueError("insufficient distinct contributions")
    dimension = len(artifact["ciphertexts"])
    for partial in partials:
        if partial["context"] != context or partial["member"] not in context["members"]:
            raise ValueError("partial context mismatch")
        if len(partial["points"]) != dimension:
            raise ValueError("incomplete contribution")
    weights = []
    for member in members:
        others = [other for other in members if other != member]
        numerator = math.prod(-other for other in others)
        denominator = math.prod(member - other for other in others) % ORDER
        weights.append(numerator * pow(denominator, -1, ORDER) % ORDER)
    lookup = {base(value): value for value in range(-artifact["bound"], artifact["bound"] + 1)}
    recovered = []
    for coordinate, (_, second) in enumerate(artifact["ciphertexts"]):
        opening = IDENTITY
        for weight, partial in zip(weights, partials):
            term = multiply(weight, bytes.fromhex(partial["points"][coordinate]))
            opening = bindings.crypto_core_ed25519_add(opening, term)
        result = bindings.crypto_core_ed25519_sub(bytes.fromhex(second), opening)
        recovered.append(lookup[result])
    return recovered


def child(mode, payload=None):
    result = subprocess.run(
        [sys.executable, __file__, mode], input=json.dumps(payload),
        text=True, capture_output=True, check=True, timeout=30,
    )
    return json.loads(result.stdout)


def rejected(exception, operation):
    try:
        operation()
    except exception:
        return
    raise AssertionError("invalid recovery input accepted")


def check():
    fixture = child("--produce")
    assert isinstance(fixture, dict), "sender must export recoverable material before exiting"
    receiver = PrivateKey(bytes.fromhex(fixture["receiver_key"]))
    sender = VerifyKey(bytes.fromhex(fixture["sender_public"]))
    batch = {recipient: bytes.fromhex(packet) for recipient, packet in fixture["batch"].items()}
    replicas = [copy.deepcopy(batch) for _ in range(3)]
    batch.clear()
    replicas[0].clear()
    packet = replicas[1]["recipient_0"]
    assert recover_input(packet, receiver, sender) == b"designated Reduce input"
    rejected(KeyError, lambda: replicas[0]["recipient_0"])
    rejected(CryptoError, lambda: recover_input(packet, PrivateKey.generate(), sender))
    rejected(CryptoError, lambda: recover_input(packet, receiver, SigningKey.generate().verify_key))
    damaged = packet[:-1] + bytes([packet[-1] ^ 1])
    rejected(CryptoError, lambda: recover_input(damaged, receiver, sender))
    rejected(CryptoError, lambda: recover_input(replicas[1]["recipient_1"], receiver, sender))
    print("PASS: sender process exited; retained recipient key recovers signed payload from replica")
    print("PASS: absent payload, lost/replaced key, wrong sender, changed ciphertext, wrong recipient")

    artifact = fixture["opening"]
    assert set(artifact) == {"context", "ciphertexts", "partials", "bound"}
    for selected in itertools.combinations(artifact["partials"], 3):
        subset = dict(artifact, partials=list(selected))
        assert child("--combine", subset) == [3, 0, -4]
    assert child("--combine", artifact) == [3, 0, -4]
    rejected(ValueError, lambda: combine(dict(artifact, partials=artifact["partials"][:2])))
    rejected(ValueError, lambda: combine(dict(artifact, partials=[artifact["partials"][0]] * 3)))
    for field, value in (("generation", 1), ("instance", "sid_other")):
        mixed = copy.deepcopy(artifact)
        mixed["partials"][0]["context"][field] = value
        rejected(ValueError, lambda: combine(mixed))
    truncated = copy.deepcopy(artifact)
    truncated["partials"][0]["points"].pop()
    rejected(ValueError, lambda: combine(truncated))
    print("PASS: every 3-of-4 subset and 4-of-4 reconstruct [3, 0, -4] in a fresh process")
    print("PASS: insufficient, duplicate, mixed-generation/instance and incomplete contributions rejected")

    altered = copy.deepcopy(artifact)
    for partial in altered["partials"]:
        point = bytes.fromhex(partial["points"][0])
        partial["points"][0] = bindings.crypto_core_ed25519_add(point, base(1)).hex()
    assert combine(altered) == [2, 0, -4]
    print("CONTROL: altered contributions change result; public proof verification remains required")


if __name__ == "__main__":
    if sys.argv[1:] == ["--produce"]:
        print(json.dumps(make_fixture()))
    elif sys.argv[1:] == ["--combine"]:
        print(json.dumps(combine(json.load(sys.stdin))))
    else:
        check()
