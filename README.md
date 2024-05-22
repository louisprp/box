# Box Project

Box is a smart, IoT-based image display device inspired by the Love Box product. This project allows users to upload images to a Supabase backend, which are then displayed on an OLED screen housed within the Box. The device is designed to be user-friendly, with features enabling easy WiFi connectivity by providing a WiFi portal as an access point, easily connected to by scanning a QR code and automated reconnection to known networks.

## Features

- **Image Display**: View images on an SSD1351 OLED display that are uploaded to Supabase.
- **WiFi Connectivity**: Simple setup via a WiFi portal to connect to nearby networks. The device remembers and automatically reconnects to known networks.
- **Power Management**: The OLED display turns off when the box is closed using a micro switch.
- **User-Friendly**: No technical programming skills required for setup and operation.
- **QR Code for Setup**: The WiFi portal will display a QR code and the hostname for easy connection.
- **mDNS Support**: The WiFi portal uses mDNS, accessible for example at `box.local` for straightforward setup.

## Gallery

<div style="display: flex; flex-wrap: wrap; justify-content: space-around; gap: 16px">
  <img src="https://i.imgur.com/8Zn48Xu.jpeg" alt="Box New Note" height="200"/> 
  <img src="https://i.imgur.com/RpDraTw.jpeg" alt="Box QR Code" height="200"/>
  <img src="https://i.imgur.com/eIeMXLr.png" alt="WiFi Portal Screenshot" height="200"/>
  <img src="https://i.imgur.com/3rFlrTz.jpeg" alt="iOS Markup Screenshot" height="200"/>
</div>

## Hardware

- **Microcontroller**: ESP32-S3 by Espressif
- **Display**: SSD1351 OLED display
- **Other Components**: Micro switch for lid detection (optionally a small speaker or buzzer)

## Software

- **Programming Language**: CircuitPython by Adafruit
- **Backend**: Supabase for image storage and retrieval

## Getting Started

### Prerequisites

- An ESP32-S3 microcontroller
- SSD1351 OLED display
- CircuitPython installed on the ESP32-S3
- Supabase account for image storage

### Installation

1. **Set up CircuitPython** on your ESP32-S3 by following the [Adafruit guide](https://learn.adafruit.com/welcome-to-circuitpython).
2. **Clone this repository** and copy the necessary CircuitPython files to your ESP32-S3.
    ```sh
    git clone https://github.com/yourusername/box.git
    ```
3. **Install required CircuitPython libraries**. Ensure the following libraries are included in your `lib` directory on the ESP32-S3:
    - `adafruit_displayio_ssd1351`
    - `adafruit_esp32spi`
    - `adafruit_requests`
    - `adafruit_minimqtt`
    - `adafruit_portalbase`

4. **Configure Supabase**:
    - Set up a new Supabase project and create a bucket for storing images.
    - Obtain your Supabase API keys and URL.

5. **Configure the Box**:
    - Update the `settings.toml` file with your Supabase credentials, the bucket name, and the image path.
    - Update `code.py` with the correct pins for the buttons and display if necessary.

### Usage

1. **Connecting to WiFi**:
    - On first boot, the Box will create a WiFi portal as an access point.
    - Connect to this portal with your device. The Box will display a QR code and the hostname (`box.local`) for easy connection.
    - Select your WiFi network from the list.

2. **Uploading Images**:
    - Upload images to your Supabase project. I use an iOS Shortcut with "Markup" for easy access.
    - The Box will detect new images and display them on the OLED screen.

3. **Closing the Box**:
    - When the Box is closed, the micro switch will turn off the OLED display to save power.

4. **Power loss**:
    - Once the power is re-connected, the Box will automatically reconnect to a known WiFi network, display the latest saved image and try to fetch the newest available image to display

## File Configuration

### `settings.toml`

Update the `settings.toml` file with your WiFi and Supabase credentials.

```toml
SUPABASE_URL=<YOUR URL HERE>
SUPABASE_ANON_KEY=<YOUR KEY HERE>
SUPABASE_BUCKET=<YOUR BUCKET NAME HERE>
SUPABASE_IMAGE_PATH=<YOUR PATH TO THE IMAGE HERE>

AP_SSID = "Box"
AP_PASSWORD = "wifiportal"
MDNS_HOSTNAME = "box"
```

### `code.py`

Ensure the `code.py` file is configured with the correct pins for your hardware setup. Example:

```python
# Define pins for buttons and display
BUTTON_PIN = board.GP42

DISPLAY_SCL = board.GP10
DISPLAY_SDA = board.GP11
DISPLAY_CS = board.GP13
DISPLAY_DC = board.GP34
DISPLAY_RESET = board.GP35
```

## Troubleshooting

- **WiFi Issues**: If the Box does not connect to a WiFi network, ensure your credentials are correct and that the network is in range.
- **Image Display Issues**: Verify that the images are in Bitmap format. Verify that the images are correctly uploaded to Supabase and that the API keys are correctly configured in `settings.toml`.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Adafruit CircuitPython](https://circuitpython.org/)
- [Supabase](https://supabase.io/)

---

Feel free to reach out if you have any questions or need further assistance.