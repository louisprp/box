import ssl
import adafruit_requests
import socketpool
import wifi
import time

try:
    from typing import Dict, Any, List, TypedDict
except ImportError:
    pass

class User:
    email: str
    email_confirmed_at: str
    phone: str
    confirmed_at: str
    last_sign_in_at: str
    app_metadata: Dict[str, Any]
    user_metadata: Dict[str, Any]
    identities: List[Dict[str, Any]]
    created_at: str
    updated_at: str

class Session:
    access_token: str
    aud: str
    role: str
    user: User

# FIXME: Needed as of now. This is a workaround for the SSL issue (should be fixed with updated root.pem in newer versions of CircuitPython 9.x+)
cadata = """
-----BEGIN CERTIFICATE-----
MIIFNDCCBNugAwIBAgIQCamWVslPeD+A6HPUczuNRDAKBggqhkjOPQQDAjBKMQsw
CQYDVQQGEwJVUzEZMBcGA1UEChMQQ2xvdWRmbGFyZSwgSW5jLjEgMB4GA1UEAxMX
Q2xvdWRmbGFyZSBJbmMgRUNDIENBLTMwHhcNMjMwODIwMDAwMDAwWhcNMjQwODE5
MjM1OTU5WjB1MQswCQYDVQQGEwJVUzETMBEGA1UECBMKQ2FsaWZvcm5pYTEWMBQG
A1UEBxMNU2FuIEZyYW5jaXNjbzEZMBcGA1UEChMQQ2xvdWRmbGFyZSwgSW5jLjEe
MBwGA1UEAxMVc25pLmNsb3VkZmxhcmVzc2wuY29tMFkwEwYHKoZIzj0CAQYIKoZI
zj0DAQcDQgAEEHU93Scmy23XeGyGl1D73SlxjhQlfti8Co89r3RKqcx2QGRmJuVb
qeZxOs9ax+qSNBXyRq0I16dhai7o+BMcRKOCA3YwggNyMB8GA1UdIwQYMBaAFKXO
N+rrsHUOlGeItEX62SQQh5YfMB0GA1UdDgQWBBTeJgSjJ9g+9HJK/v+ZgmvR/0K4
ODA8BgNVHREENTAzggtzdXBhYmFzZS5jb4INKi5zdXBhYmFzZS5jb4IVc25pLmNs
b3VkZmxhcmVzc2wuY29tMA4GA1UdDwEB/wQEAwIHgDAdBgNVHSUEFjAUBggrBgEF
BQcDAQYIKwYBBQUHAwIwewYDVR0fBHQwcjA3oDWgM4YxaHR0cDovL2NybDMuZGln
aWNlcnQuY29tL0Nsb3VkZmxhcmVJbmNFQ0NDQS0zLmNybDA3oDWgM4YxaHR0cDov
L2NybDQuZGlnaWNlcnQuY29tL0Nsb3VkZmxhcmVJbmNFQ0NDQS0zLmNybDA+BgNV
HSAENzA1MDMGBmeBDAECAjApMCcGCCsGAQUFBwIBFhtodHRwOi8vd3d3LmRpZ2lj
ZXJ0LmNvbS9DUFMwdgYIKwYBBQUHAQEEajBoMCQGCCsGAQUFBzABhhhodHRwOi8v
b2NzcC5kaWdpY2VydC5jb20wQAYIKwYBBQUHMAKGNGh0dHA6Ly9jYWNlcnRzLmRp
Z2ljZXJ0LmNvbS9DbG91ZGZsYXJlSW5jRUNDQ0EtMy5jcnQwDAYDVR0TAQH/BAIw
ADCCAX4GCisGAQQB1nkCBAIEggFuBIIBagFoAHUAdv+IPwq2+5VRwmHM9Ye6NLSk
zbsp3GhCCp/mZ0xaOnQAAAGKEOGAMAAABAMARjBEAiBmaPsEFxNn8WQBagEDagKF
kxeQMIfRXS6smUypnUZ+QwIgb72QHDAmkAhstsTPZKdWHfdcLY7PhYhpuVtxiuDL
68sAdgBIsONr2qZHNA/lagL6nTDrHFIBy1bdLIHZu7+rOdiEcwAAAYoQ4X/bAAAE
AwBHMEUCICPSteAouY2sYycBMW9AG+ELmPsnEsMeNKT1QnmNVH3UAiEA0egTm5B9
LzXWmsQxJXwZY1af78Vdmr3xUjQy6s6WlcgAdwDatr9rP7W2Ip+bwrtca+hwkXFs
u1GEhTS9pD0wSNf7qwAAAYoQ4X/vAAAEAwBIMEYCIQC9txFpkDwgZUvjaO2FjmrI
ZbOERjMbdK6LsgitPztk1QIhAOL1CFuZJ4yMItUxjZkcF77Kmchd41f2cl05qrGV
aqHmMAoGCCqGSM49BAMCA0cAMEQCIBvhmIBbIn6YM6fuw5PxNIxxuOUwN+3/GvgH
s3/hfSA1AiBl7ZriVn7iHN3dQmE1O80DnZubGQvi6Yyqlr8+sBwktA==
-----END CERTIFICATE-----
-----BEGIN CERTIFICATE-----
MIIDzTCCArWgAwIBAgIQCjeHZF5ftIwiTv0b7RQMPDANBgkqhkiG9w0BAQsFADBa
MQswCQYDVQQGEwJJRTESMBAGA1UEChMJQmFsdGltb3JlMRMwEQYDVQQLEwpDeWJl
clRydXN0MSIwIAYDVQQDExlCYWx0aW1vcmUgQ3liZXJUcnVzdCBSb290MB4XDTIw
MDEyNzEyNDgwOFoXDTI0MTIzMTIzNTk1OVowSjELMAkGA1UEBhMCVVMxGTAXBgNV
BAoTEENsb3VkZmxhcmUsIEluYy4xIDAeBgNVBAMTF0Nsb3VkZmxhcmUgSW5jIEVD
QyBDQS0zMFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAEua1NZpkUC0bsH4HRKlAe
nQMVLzQSfS2WuIg4m4Vfj7+7Te9hRsTJc9QkT+DuHM5ss1FxL2ruTAUJd9NyYqSb
16OCAWgwggFkMB0GA1UdDgQWBBSlzjfq67B1DpRniLRF+tkkEIeWHzAfBgNVHSME
GDAWgBTlnVkwgkdYzKz6CFQ2hns6tQRN8DAOBgNVHQ8BAf8EBAMCAYYwHQYDVR0l
BBYwFAYIKwYBBQUHAwEGCCsGAQUFBwMCMBIGA1UdEwEB/wQIMAYBAf8CAQAwNAYI
KwYBBQUHAQEEKDAmMCQGCCsGAQUFBzABhhhodHRwOi8vb2NzcC5kaWdpY2VydC5j
b20wOgYDVR0fBDMwMTAvoC2gK4YpaHR0cDovL2NybDMuZGlnaWNlcnQuY29tL09t
bmlyb290MjAyNS5jcmwwbQYDVR0gBGYwZDA3BglghkgBhv1sAQEwKjAoBggrBgEF
BQcCARYcaHR0cHM6Ly93d3cuZGlnaWNlcnQuY29tL0NQUzALBglghkgBhv1sAQIw
CAYGZ4EMAQIBMAgGBmeBDAECAjAIBgZngQwBAgMwDQYJKoZIhvcNAQELBQADggEB
AAUkHd0bsCrrmNaF4zlNXmtXnYJX/OvoMaJXkGUFvhZEOFp3ArnPEELG4ZKk40Un
+ABHLGioVplTVI+tnkDB0A+21w0LOEhsUCxJkAZbZB2LzEgwLt4I4ptJIsCSDBFe
lpKU1fwg3FZs5ZKTv3ocwDfjhUkV+ivhdDkYD7fa86JXWGBPzI6UAPxGezQxPk1H
goE6y/SJXQ7vTQ1unBuCJN0yJV0ReFEQPaA1IwQvZW+cwdFD19Ae8zFnWSfda9J1
CZMRJCQUzym+5iPDuI9yP+kHyCREU3qzuWFloUwOxkgAyXVjBYdwRVKD05WdRerw
6DEdfgkfCv4+3ao8XnTSrLE=
-----END CERTIFICATE-----
"""

class Supabase:
    def __init__(self, url: str, public_key: str):
        self.url = url
        self.public_key = public_key
        self.headers = {
            'apikey': self.public_key,
            'Content-Type': 'application/json'
        }
        self.access_token = None

        pool = socketpool.SocketPool(wifi.radio)
        context = ssl.create_default_context()
        # This is a workaround for the SSL issue (should be fixed with updated root.pem in newer versions of CircuitPython)
        print("Loading custom certificates")
        context.load_verify_locations(cadata=cadata)

        self.requests = adafruit_requests.Session(pool, context)

    class Auth:
        def __init__(self, parent):
            self.parent = parent
            self.requests = parent.requests

        def login(self, email: str, password: str) -> Session:
            data = {
                'email': email,
                'password': password,
            }
            try:
                response = self.requests.post(f'{self.parent.url}/auth/v1/token?grant_type=password', headers=self.parent.headers, json=data)
            except Exception as err:
                print(f'HTTP error occurred: {err}')
                return None
            
            session: Session = response.json()
            self.parent.access_token = session.get('access_token')
            self.parent.headers['Authorization'] = f'Bearer {self.parent.access_token}'
            return session

        def sign_out(self):
            self.parent.access_token = None
            if 'Authorization' in self.parent.headers:
                del self.parent.headers['Authorization']

        def me(self) -> User:
            try:
                response = self.parent.requests.get(f'{self.url}/auth/v1/user', headers=self.parent.headers)
            except Exception as err:
                print(f'HTTP error occurred: {err}')
                return None

            user: User = response.json()
            return user

    class Storage:
        def __init__(self, parent):
            self.parent = parent
            self.base_url = f'{self.parent.url}/storage/v1'

        def get_object(self, bucket_name: str, filename: str):
            try:
                response = self.parent.requests.get(
                    f'{self.base_url}/object/authenticated/{bucket_name}/{filename}',
                    headers=self.parent.headers  # Use parent headers
                )
                if response.status_code == 404:
                    raise Exception(f'Object not found: {filename}')
                return response.content
            except Exception as err:
                print(f'HTTP error occurred: {err}')
                raise Exception(f'Failed to fetch object: {err}')
        
        def get_public_object(self, bucket_name: str, filename: str, params: Dict[str, Any] = None):
            url = f'{self.base_url}/object/public/{bucket_name}/{filename}'
            if params:
                    url += "?"
                    for key, value in params.items():
                        url += f"{key}={value}&"
                    url = url[:-1]
            try:
                response = self.parent.requests.get(
                    url,
                    headers=self.parent.headers  # Use parent headers
                )
                if response.status_code == 404:
                    raise Exception(f'Object not found: {filename}')
                return response.content
            except Exception as err:
                print(f'HTTP error occurred: {err}')
                raise Exception(f'Failed to fetch object: {err}')
        
        def get_object_info(self, bucket_name: str, wildcard: str):
            try:
                response = self.parent.requests.get(
                    f'{self.base_url}/object/info/authenticated/{bucket_name}/{wildcard}',
                    headers=self.parent.headers
                )
                if response.status_code == 404:
                    raise Exception(f'Object not found: {wildcard}')
                return response.headers
            except Exception as err:
                print(f'HTTP error occurred: {err}')
                raise Exception(f'Failed to fetch public object info: {err}')
        
        def get_public_object_info(self, bucket_name: str, wildcard: str, params: Dict[str, Any] = None):
            try:
                url = f'{self.base_url}/object/info/public/{bucket_name}/{wildcard}'
                if params:
                    url += "?"
                    for key, value in params.items():
                        url += f"{key}={value}&"
                    url = url[:-1]
                response = self.parent.requests.get(
                    url,
                    headers=self.parent.headers
                )
                if response.status_code == 404:
                    raise Exception(f'Object not found: {wildcard}')
                return response.headers
            except Exception as err:
                print(f'HTTP error occurred: {err}')
                raise Exception(f'Failed to fetch public object info: {err}')
    
    @property
    def auth(self):
        return self.Auth(self)

    @property
    def storage(self):
        return self.Storage(self)

def createClient(url: str, public_key: str) -> Supabase:
        return Supabase(url, public_key)