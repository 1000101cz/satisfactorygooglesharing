import sys
from pathlib import Path

def get_resource_path(relative_path: str) -> Path:
    if hasattr(sys, '_MEIPASS'):
        base_path = Path(sys._MEIPASS)
    else:
        base_path = Path(__file__).parent.parent

    return base_path / relative_path