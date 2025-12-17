"""
Test launcher - Quick access to test world
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test.test_world import run_test_world

if __name__ == "__main__":
    run_test_world()
