"""Entrada para el ejecutable Windows: abre el wizard (doble clic)."""

from dotenv import load_dotenv

from taxos.gui import run_wizard

load_dotenv()


def main() -> None:
    run_wizard()


if __name__ == "__main__":
    main()
