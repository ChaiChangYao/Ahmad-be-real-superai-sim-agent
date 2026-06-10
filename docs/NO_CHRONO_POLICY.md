# Simulation Engine Policy

This sandbox uses Genesis World as the only simulation engine.

Policy requirements:
- no alternate physics engine dependencies
- no alternate engine adapters or fallback layers
- no references to alternate engine APIs in runtime paths

Use `python tools/check_no_forbidden_engines.py` to enforce this policy.
