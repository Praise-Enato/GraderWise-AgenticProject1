import sys
import os

# Setup Path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

print("Attempting to import backend.src.main...")
try:
    from backend.src import main
    print("✅ Successfully imported backend.src.main")
except Exception as e:
    print(f"❌ Failed to import backend.src.main: {e}")
    sys.exit(1)
