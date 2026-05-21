"""
Telemetry Bus
Tracks system state mutations and maintains a volatile memory buffer for the Cognitive Subsystem.
"""
import os
import time
import logging
from collections import deque


class TelemetryBus:
    def __init__(self, log_file="system_telemetry.log"):
        # Save the log in the root project directory
        self.log_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), log_file)

        # Volatile Short-Term Memory Buffer
        self.context_buffer = deque(maxlen=50)

        self.logger = logging.getLogger("HypervisorTelemetry")
        self.logger.setLevel(logging.INFO)

        if self.logger.hasHandlers():
            self.logger.handlers.clear()

        formatter = logging.Formatter('[%(asctime)s.%(msecs)03d] -> %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        fh = logging.FileHandler(self.log_file)
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)

        self.log("SYS_BOOT", "Telemetry Pipeline Initialized. Sensors online.")

    def log(self, event_type, details):
        """Injects a physical system event into the logging pipeline."""
        self.logger.info(f"EVENT:{event_type} | DATA:{details}")

        timestamp = time.strftime('%H:%M:%S')
        memory_string = f"[{timestamp}] {event_type} -> {details}"
        self.context_buffer.append(memory_string)

    def read_stream(self, lines=10):
        """Pulls raw events from the physical disk log."""
        if not os.path.exists(self.log_file):
            return "[TELEMETRY] No data stream found."

        with open(self.log_file, "r") as f:
            content = f.readlines()

        if not content:
            return "[TELEMETRY] Stream is empty."

        output = "[TELEMETRY] Recent System Events:\n"
        for line in content[-lines:]:
            output += line.strip() + "\n"
        return output.strip()

    def get_ai_context(self):
        """Serializes the volatile memory buffer for LLM consumption."""
        if not self.context_buffer:
            return "SYSTEM_STATE: IDLE. No recent events."

        context = "RECENT_SYSTEM_EVENTS:\n"
        for memory in self.context_buffer:
            context += memory + "\n"
        return context.strip()