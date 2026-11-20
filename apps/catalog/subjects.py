"""Stable hashes for install dedupe. Raw origins, install ids, and user ids are not stored."""

from __future__ import annotations

import hashlib


def subject_hash(*parts: str) -> str:
    material = '\n'.join(parts)
    return hashlib.sha256(material.encode('utf-8')).hexdigest()


def user_subject(sub: str) -> str:
    return subject_hash('user', sub)


def anonymous_subject(origin: str, install_id: str) -> str:
    return subject_hash('anon', origin, install_id)
