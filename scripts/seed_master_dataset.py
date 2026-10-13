"""
Legacy entrypoint redirecting to the unified master seed pipeline (scripts/seed.py).
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scripts.seed import seed_database


def seed_master_dataset(reset: bool = False):
    return seed_database(reset=reset)


if __name__ == "__main__":
    reset = "--reset" in sys.argv
    seed_master_dataset(reset=reset)
