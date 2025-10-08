# main.py
import sys
from pathlib import Path

if getattr(sys, 'frozen', False):  # Running as a PyInstaller EXE
    root_path = Path(sys.executable).parent
else:  # Running as a Python script
    root_path = Path(__file__).parent.parent
sys.path.append(str(root_path))

from core.dependencies import DependencyChecker
from core.environment import EnvironmentSetup


def main():
    DependencyChecker.check()
    setup = EnvironmentSetup()
    setup.setup()


if __name__ == "__main__":
    main()