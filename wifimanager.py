import wifi
import json
import socketpool
import mdns
import time
from adafruit_httpserver import (
    Server as HTTPServer,
    Response as HTTPResponse,
    Request as HTTPRequest,
    MIMETypes,
)
from utils import is_readonly
from adafruit_templateengine import render_template
import adafruit_miniqr

MIMETypes.configure(
    default_to="text/plain",
    # Unregistering unnecessary MIME types can save memory
    keep_for=[".html", ".css", ".png", ".ico"],
)

AP_SSID = os.getenv("AP_SSID")
AP_PASSWORD = os.getenv("AP_PASSWORD")
MDNS_HOSTNAME = os.getenv("AP_MDNS_HOSTNAME")
CONFIG_FILE_PATH = "/wifi.json"

class WifiManager:
    def __init__(self, graphics, debug=False):
        self._debug = debug
        self.graphics = graphics

        if self._debug:
            print("Init Wifi Manager")

        self.config = {"latest": None, "known_networks": {}}
        self.load_config()

    def get_connection(self) -> bool:
        if self.is_connected() is True:
            if self._debug:
                print("Already connected.")
            return True

        if self._debug:
            print("Checking for existing credentials...")

        if self.config["latest"] is not None:
            if self._debug:
                print("Connecting with the latest credentials...")
            
            ssid = self.config["latest"]["ssid"]
            password = self.config["latest"]["password"]
            if self.connect(ssid, password):
                return True
        
        if self._debug:
            print("Scanning for known networks...")

        networks = []
        for network in wifi.radio.start_scanning_networks():
            networks.append({"ssid": network.ssid, "rssi": network.rssi})
        wifi.radio.stop_scanning_networks()

        networks.sort(key=lambda x: x["rssi"], reverse=True)

        # Check if there are any known networks matching the scanned SSIDs
        for network in networks:
            ssid = network["ssid"]
            if ssid in self.config["known_networks"]:
                if self._debug:
                    print(f"Trying to connect to known network: {ssid}")
                if self.connect(ssid, self.config["known_networks"][ssid]["password"]):

                    if self._debug:
                        print(f"Updating the latest network to: {ssid}")
                    # Update the latest network information
                    self.config['latest'] = {
                        'ssid': ssid,
                        'password': self.config["known_networks"][ssid]["password"]
                    }

                    if not is_readonly():
                        # Save the updated configuration
                        self._debug and print("Saving the updated Wi-Fi configuration to the file system.")
                        self.save_config()

                    return True
        
        if self._debug:
            print("No known networks found.")
        
        return False

    def connect(self, ssid: str, password: str) -> bool:
        try:
            wifi.radio.connect(ssid, password)
            if self._debug:
                print("Connected to: " + ssid)
            return True
        except Exception as e:
            if self._debug:
                print("Error while connecting to: " + ssid)
                print(e)
            return False

    def start_server(self):
        if self._debug:
            print("Starting AP...")
        wifi.radio.start_ap(AP_SSID, AP_PASSWORD)

        if self._debug:
            print("Starting mDNS...")
        mdns_server = mdns.Server(wifi.radio)
        mdns_server.hostname = MDNS_HOSTNAME
        mdns_server.advertise_service(service_type="_http", protocol="_tcp", port=80)
        if self._debug:
            print("Reachable at: " + str(mdns_server.hostname) + ".local")

        pool = socketpool.SocketPool(wifi.radio)
        server = HTTPServer(pool, "/static", debug=self._debug)

        qr = adafruit_miniqr.QRCode(qr_type=3)
        qr.add_data(
            b"WIFI:T:WPA;S:" + AP_SSID.encode() + b";P:" + AP_PASSWORD.encode() + b";"
        )
        qr.make()

        self.graphics.remove_all_text()

        self.graphics.add_text(
            (self.graphics.display.width / 2, 10),
            "fonts/vt323-12.bdf",
            0xFF00FF,
            line_spacing=1,
            text_scale=1,
            text_anchor_point=(0.5, 0.5),
            text="Scan to connect & visit:",
        )
        self.graphics.add_text(
            (self.graphics.display.width / 2, 25),
            "fonts/vt323-12.bdf",
            0xFF00FF,
            line_spacing=1,
            text_scale=1,
            text_anchor_point=(0.5, 0.5),
            text="http://" + str(mdns_server.hostname) + ".local",
        )
        self.graphics.add_qrcode(
            qr,
            qr_color=0xFF00FF,
            qr_size=3,
            x=self.graphics.display.width // 2,
            y=self.graphics.display.height // 2 + 20,
            qr_anchor_point=(0.5, 0.5),
        )

        @server.route("/")
        def route_func(request: HTTPRequest):
            ssids = []
            for network in wifi.radio.start_scanning_networks():
                ssids.append(network.ssid)
            wifi.radio.stop_scanning_networks()

            context = { "ssids": ssids }
            response = render_template("/templates/index.html", context)

            return HTTPResponse(request, content_type="text/html", body=response)

        @server.route("/connect", methods=["POST"])
        def route_func(request: HTTPRequest):
            ssid = request.form_data.get("ssid", "")
            password = request.form_data.get("password", "")

            if self._debug:
                print("Connecting to: " + ssid)

            if self.connect(ssid, password):
                # Save the new network to the configuration
                self.add_new_wifi_network(ssid, password)
                
                # TODO: Render a success page instead of this
                return HTTPResponse(
                    request,
                    body="Connected!",
                    content_type="text/plain",
                )
            else:
                response = render_template("/templates/error.html")
                return HTTPResponse(
                    request,
                    body=response,
                    content_type="text/html",
                )

        server.start(str(wifi.radio.ipv4_address_ap), 80)

        while True:
            if wifi.radio.ap_info is None:
                server.poll()
            else:
                if self._debug:
                    print("Connected. Stopping...")
                
                self.graphics.remove_all_text()
                self.graphics.remove_all_qr()
                self.graphics.add_text((self.graphics.display.width / 2, (self.graphics.display.height / 2) - 15),
                "fonts/forkawesome-12.pcf",
                0xFF00FF,
                line_spacing=1,
                text_scale=3,
                text_anchor_point=(0.5, 0.5),
                text="\uf1eb",
                )
                self.graphics.add_text(
                (self.graphics.display.width / 2, self.graphics.display.height - 15),
                "fonts/hang-the-dj-12.bdf",
                0xFF00FF,
                text_anchor_point=(0.5, 0.5),
                text="Connected!",
                )

                server.stop()
                mdns_server.deinit()
                if self._debug:
                    print("Stopped mDNS.")
                wifi.radio.stop_ap()
                if self._debug:
                    print("Stopped AP.")

                time.sleep(5)

                return

    def is_connected(self) -> bool:
        return False if wifi.radio.ap_info is None else True

    def load_config(self):
        try:
            with open(CONFIG_FILE_PATH, "r") as file:
                self.config = json.load(file)
            self._debug and print("Loaded the wifi configuration from the file system.")
        except:
            print("Config file not found / is corrupted. A new one will be created upon saving.")

    def save_config(self):
        '''Save the wifi configuration to the file system.
            Example:
            {
                "latest": {
                    "ssid": "my_wifi",
                    "password": "my_password"
                },
                "known_networks": {
                    "my_wifi": {
                        "password": "my_password"
                    }
                }
            }
        '''
        try:
            with open(CONFIG_FILE_PATH, 'w') as file:
                json.dump(self.config, file)
        except Exception as e:
            print(f"Failed to save the wifi configuration file: {e}")

    def add_new_wifi_network(self, ssid:str, password:str):
        # Update the latest network information
        self.config['latest'] = {
            'ssid': ssid,
            'password': password
        }

        # Check if the SSID is in known networks and update the password
        if ssid in self.config['known_networks']:
            self.config['known_networks'][ssid]['password'] = password
        else:
            # Add the new network if the SSID is not found
            self.config['known_networks'][ssid] = {'password': password}

        if not is_readonly():
            # Save the updated configuration
            if self._debug:
                print("Saving the updated Wi-Fi configuration to the file system.")
            self.save_config()
        
        else:
            self._debug and print("File system is read-only. The configuration will not be saved.")

    def current_network(self) -> wifi.Network | None:
        if self.is_connected():
            return wifi.radio.ap_info