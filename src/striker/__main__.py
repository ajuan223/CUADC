"""Entry point for ``python -m striker``."""

from striker import __version__


def main() -> None:
    """Print version and exit."""
    print(f"Striker v{__version__}")


if __name__ == "__main__":
    main()
