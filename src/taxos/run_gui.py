"""Entrada para el ejecutable Windows: abre el wizard (doble clic)."""

import os
import sys

# PyInstaller --windowed deja stdout/stderr en None.
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w", encoding="utf-8")  # noqa: SIM115
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w", encoding="utf-8")  # noqa: SIM115

from dotenv import load_dotenv

load_dotenv()


def main() -> None:
    from taxos.gui import run_wizard

    run_wizard()


if __name__ == "__main__":
    main()
