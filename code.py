import displayio
import board
import busio
from digitalio import DigitalInOut, Direction, Pull
from adafruit_ssd1351 import SSD1351
import wifi
import time

import supervisor
import json
import os

from graphics import Graphics
from utils import is_readonly, file_exists
from wifimanager import WifiManager
from supabase import createClient

# Define pins for buttons and display
BUTTON_PIN = board.GP42

DISPLAY_SCL = board.GP10
DISPLAY_SDA = board.GP11
DISPLAY_CS = board.GP13
DISPLAY_DC = board.GP34
DISPLAY_RESET = board.GP35

supervisor.runtime.autoreload = False

# Clear displays
displayio.release_displays()

# Setup pins, change to match connections
spi = busio.SPI(DISPLAY_SCL, DISPLAY_SDA)
tft_cs = DISPLAY_CS
tft_dc = DISPLAY_DC
tft_rs = DISPLAY_RESET

# Initialize display SSD1351 type
display_bus = displayio.FourWire(spi, command=tft_dc, chip_select=tft_cs, reset=tft_rs)
display = SSD1351(display_bus, width=128, height=128, rotation=180)

# Set up open/close button, change to match connections
button = DigitalInOut(BUTTON_PIN)
button.direction = Direction.INPUT
button.pull = Pull.UP

graphics = Graphics(display)

graphics.add_text(
    (display.width / 2, display.height / 2),
    "fonts/hang-the-dj-12.bdf",
    0xFF00FF,
    line_spacing=1,
    text_scale=3,
    text_anchor_point=(0.5, 0.5),
    text="Box",
)

# When fs is mounted as read-only
if is_readonly():
    print("Mounted as read-only")
    graphics.add_text(
        (display.width / 2, display.height / 2),
        "fonts/vt323-12.bdf",
        0xFF00FF,
        line_spacing=1,
        text_scale=1,
        text_anchor_point=(0.5, 0.5),
        text="Mounted as read-only"
    )


opened = button.value

wifimanager = WifiManager(graphics, debug=True)

# Try to establish connection
if wifimanager.get_connection():
    # Add connected network text 
    graphics.add_text(
        (display.width / 2, display.height - 10),
        "fonts/vt323-12.bdf",
        0xFF00FF,
        line_spacing=1,
        text_scale=1,
        text_anchor_point=(0.5, 0.5),
        text=wifimanager.current_network().ssid
    )
    time.sleep(2)
else:
    # No connection could be established
    graphics.remove_all_text()
    graphics.add_text(
        (display.width / 2, (display.height / 2) - 15),
        "fonts/forkawesome-12.pcf",
        0xFF00FF,
        line_spacing=1,
        text_scale=3,
        text_anchor_point=(0.5, 0.5),
        text="\uf00d"
    )
    graphics.add_text(
        (display.width / 2, display.height - 15),
        "fonts/hang-the-dj-12.bdf",
        0xFF00FF,
        text_anchor_point=(0.5, 0.5),
        text="No connection!"
    )
    time.sleep(5)

    # Start wifi portal to establish new connection
    wifimanager.start_server()

# If a recent file exists, display it
if file_exists("/display.bmp"):
    graphics.remove_all_text()
    graphics.set_background("/display.bmp")

# Connect to supabase
supabase = createClient(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_ANON_KEY"))

# Load config
config = { "last-modified": None }
try:
    with open("config.json", "r") as file:
        config = json.load(file)
except:
    print("Config file not found / is corrupted. A new one will be created upon saving.")

next_event_time = time.monotonic()

print("Starting main loop...")
bucket = os.getenv("SUPABASE_BUCKET")
image_path = os.getenv("SUPABASE_IMAGE_PATH")

while True:
    # Display logic, turn off when button down (closed)
    if (button.value == False) and (button.value != opened):
        # Turn display OFF
        display_bus.send(0xAE, "")
        opened = False
    elif (button.value == True) and (button.value != opened):
        # Turn display ON
        display_bus.send(0xAF, "")
        opened = True

    if next_event_time < time.monotonic():
        print("Checking for updates...")

        # Needed to get latest image (avoid stale cache)
        version = time.monotonic()
        info = supabase.storage.get_public_object_info(bucket, image_path, params={"version": version})

        if info["last-modified"] != config["last-modified"]:
            # A new image is available
            print("New image available!")

            # Update last-modified
            config["last-modified"] = info["last-modified"]
            
            # Display notification
            graphics.set_background(0x000000)
            # Heart icon
            graphics.add_text(
            (display.width / 2, (display.height / 2) - 15),
            "fonts/forkawesome-12.pcf",
            0xFF00FF,
            line_spacing=1,
            text_scale=3,
            text_anchor_point=(0.5, 0.5),
            text="\uf004",
            )
            graphics.add_text(
            (display.width / 2, display.height - 15),
            "fonts/hang-the-dj-12.bdf",
            0xFF00FF,
            text_anchor_point=(0.5, 0.5),
            text="New Note!",
            )

            # Download new image
            image = supabase.storage.get_public_object(bucket, image_path, params={"version": version})

            # Save the image to file
            if not is_readonly():
                print("Saving new image to fs...")
                try:
                    with open("/display.bmp", "wb") as file:
                        file.write(image)
                    
                    # Display newly donwloaded image
                    graphics.remove_all_text()
                    graphics.set_background("/display.bmp")
                except Exception as e:
                    print(f"Failed to save the image file: {e}")

            # Save the config to file
            if not is_readonly():
                print("Saving new config to fs...")
                try:
                    with open("config.json", "w") as file:
                        json.dump(config, file)
                except Exception as e:
                    print(f"Failed to save the config file: {e}")
            
            print(config)

        next_event_time = time.monotonic() + 8

 