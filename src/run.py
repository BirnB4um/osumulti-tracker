from Tracker import OsuMultiTracker
import time

try:
    tracker = OsuMultiTracker()
    tracker.run()
except Exception as e:
    print(f"Error running tracker: {e}")
    