"""
Virtual Network Interface (vNIC)
Handles TCP socket connections, firewall routing, and payload downloads.
"""
import socket
import urllib.request


class VirtualNetworkInterface:
    def __init__(self):
        self.firewall = {"OUTBOUND": True, "INBOUND": False}
        self.active_connections = 0

    def send_tcp_probe(self, target_host, target_port=80):
        """Initiates a standard TCP/IP HEAD request to external servers."""
        if not self.firewall["OUTBOUND"]:
            return False, "[FIREWALL] OUTBOUND TRAFFIC BLOCKED. Packet dropped."

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(2.0)
                self.active_connections += 1
                s.connect((target_host, target_port))

                request = f"HEAD / HTTP/1.1\r\nHost: {target_host}\r\n\r\n".encode('utf-8')
                s.sendall(request)
                response = s.recv(512)
                self.active_connections -= 1

                status_line = response.decode('utf-8').split('\n')[0].strip()
                return True, f"[vNIC] Connection established. Host replied: {status_line}"

        except socket.gaierror:
            self.active_connections = max(0, self.active_connections - 1)
            return False, f"[vNIC] DNS Resolution failed for '{target_host}'."
        except socket.timeout:
            self.active_connections = max(0, self.active_connections - 1)
            return False, f"[vNIC] Connection timed out to '{target_host}'."
        except Exception as e:
            self.active_connections = max(0, self.active_connections - 1)
            return False, f"[vNIC] Network error: {str(e)}"

    def download_payload(self, url):
        """Bypasses local storage to buffer remote HTTP payloads."""
        if not self.firewall["OUTBOUND"]:
            return None, "[FIREWALL] OUTBOUND TRAFFIC BLOCKED."

        try:
            self.active_connections += 1
            req = urllib.request.Request(url, headers={'User-Agent': 'ShadowOS/1.0'})

            with urllib.request.urlopen(req, timeout=5) as response:
                data = response.read().decode('utf-8')

            self.active_connections -= 1
            return data, "SUCCESS"
        except Exception as e:
            self.active_connections = max(0, self.active_connections - 1)
            return None, f"[vNIC] Exfiltration failed: {str(e)}"