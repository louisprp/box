import board
from digitalio import DigitalInOut, Direction, Pull
import storage

# Customize to fit your board
button = DigitalInOut(board.GP42)
button.direction = Direction.INPUT
button.pull = Pull.UP

# Remounts as r/w, unless button is pressed
if button.value == False:
    print("Button pressed. Skipping remount.")
else:
    storage.remount("/", False)