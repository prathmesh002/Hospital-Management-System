import hashlib

from django.contrib.auth.hashers import BasePasswordHasher, mask_hash
from django.utils.crypto import constant_time_compare
from django.utils.translation import gettext_noop as _


class LegacyMD5PasswordHasher(BasePasswordHasher):
    """
    Verifies passwords stored as plain, unsalted MD5 (what the PHP app used).

    Stored format: ``legacy_md5$$<32-hex-md5>``. It is intentionally *not* the
    preferred hasher, so Django upgrades the stored hash to PBKDF2 on the user's
    next successful login. Never use this hasher for new passwords.
    """

    algorithm = "legacy_md5"

    def salt(self):
        return ""

    def encode(self, password, salt=""):
        digest = hashlib.md5(password.encode("utf-8")).hexdigest()
        return "%s$$%s" % (self.algorithm, digest)

    def decode(self, encoded):
        algorithm, _empty, digest = encoded.split("$", 2)
        assert algorithm == self.algorithm
        return {"algorithm": algorithm, "hash": digest, "salt": None}

    def verify(self, password, encoded):
        decoded = self.decode(encoded)
        expected = self.encode(password).split("$", 2)[2]
        return constant_time_compare(decoded["hash"], expected)

    def safe_summary(self, encoded):
        decoded = self.decode(encoded)
        return {_("algorithm"): decoded["algorithm"], _("hash"): mask_hash(decoded["hash"])}

    def must_update(self, encoded):
        return True

    def harden_runtime(self, password, encoded):
        pass
