from app.services.genesis.genesis_runtime import genesis_runtime


def main() -> int:
    status = genesis_runtime.status()
    print(f"installed={status.installed}")
    print(f"version={status.version}")
    print(f"backend={status.backend}")
    print(f"error={status.error}")
    return 0 if status.installed else 1


if __name__ == "__main__":
    raise SystemExit(main())
