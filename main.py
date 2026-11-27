# main.py
import sys
from pathlib import Path

def get_project_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent


def ensure_root_on_sys_path() -> Path:
    root = get_project_root()
    root_str = str(root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)
    return root

from core.environment import EnvironmentSetup


def main():
    ensure_root_on_sys_path()
    setup = EnvironmentSetup()
    setup.setup()


if __name__ == "__main__":
    main()