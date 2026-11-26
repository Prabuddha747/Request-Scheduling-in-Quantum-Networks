"""Phase 0 dependency probe for Apple Silicon (arm64) / Python 3.12.

Run with: /usr/local/bin/python3.12 scripts/smoke_test_deps.py
Checks core deps only. SeQUeNCe and NetSquid are probed separately (optional,
separate venvs) since they are not core-path dependencies.
"""
import importlib
import platform
import sys


def check(name, import_name=None, min_py=None):
    import_name = import_name or name
    try:
        mod = importlib.import_module(import_name)
        ver = getattr(mod, "__version__", "?")
        print(f"OK   {name:12s} {ver}")
        return True
    except ImportError as e:
        print(f"MISS {name:12s} ({e})")
        return False


def main():
    print(f"platform: {platform.machine()} / python {sys.version.split()[0]}")
    assert platform.machine() == "arm64", "expected Apple Silicon arm64"
    core = ["simpy", "numpy", "scipy", "pandas", "matplotlib", "yaml", "pytest", "torch"]
    results = {name: check(name) for name in core}
    if results.get("torch"):
        import torch
        print(f"     torch backends: cuda={torch.cuda.is_available()} mps={torch.backends.mps.is_available()}")
    missing = [k for k, v in results.items() if not v]
    if missing:
        print(f"\nMissing: {missing} -- install with: python3.12 -m pip install {' '.join(missing)}")
        sys.exit(1)
    print("\nAll core deps present.")


if __name__ == "__main__":
    main()
