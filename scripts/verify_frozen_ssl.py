"""Check the executable's bundled SSL module and certificate data without network access."""

import sys
import tempfile
import types
from pathlib import Path

from PyInstaller.archive.readers import CArchiveReader


def verify(executable: str):
    archive = CArchiveReader(executable)
    pyz = archive.open_embedded_archive("PYZ.pyz")
    with tempfile.TemporaryDirectory(prefix="parrotink-ssl-") as directory:
        root = Path(directory)
        for name in ("codex-rejected-cas.pem", "certifi\\cacert.pem"):
            if name in archive.toc:
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(archive.extract(name))
        module = types.ModuleType("_parrotink_frozen_ssl_check")
        module.__file__ = str(root / "ssl.py")
        sys.modules[module.__name__] = module
        try:
            exec(pyz.extract("ssl"), module.__dict__)
            context = module.create_default_context(cafile=str(root / "certifi" / "cacert.pem"))
            assert context.check_hostname
            assert context.verify_mode == module.CERT_REQUIRED
        finally:
            del sys.modules[module.__name__]
    print("PASS: bundled SSL context initializes with certificate verification enabled")


if __name__ == "__main__":
    verify(sys.argv[1] if len(sys.argv) > 1 else "dist/ParrotInk.exe")
