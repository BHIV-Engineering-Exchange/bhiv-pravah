import sys
from pathlib import Path

project_root = str(Path(__file__).parent.parent)
sys.path.insert(0, project_root)

from mangum import Mangum
from cet_service import app

handler = Mangum(app)
