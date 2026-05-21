"""
Memory Management Unit (MMU)
Handles physical RAM allocation, paging, and memory isolation.
"""
import mmap


class MemoryManagementUnit:
    def __init__(self, total_ram_mb=128):
        self.total_ram = total_ram_mb * 1024 * 1024
        self.available_ram = self.total_ram

        # Anonymous memory map (Direct physical RAM allocation)
        self.ram = mmap.mmap(-1, self.total_ram)
        self.page_table = {}
        self.current_offset = 0

    def allocate(self, pid, size_mb):
        """Allocates physical memory to a given process ID."""
        amount_bytes = size_mb * 1024 * 1024
        if amount_bytes > self.available_ram:
            return False, "OOM_ERROR: Insufficient Physical RAM"

        start_addr = self.current_offset
        self.page_table[pid] = (start_addr, amount_bytes)

        self.current_offset += amount_bytes
        self.available_ram -= amount_bytes

        # Inject memory signature
        signature = f"PID_{pid}_ALLOCATED".encode('utf-8')
        self.ram.seek(start_addr)
        self.ram.write(signature.ljust(amount_bytes, b'\x00')[:amount_bytes])

        return True, "SUCCESS"

    def free(self, pid):
        """Releases and zeroes out physical memory for a terminated process."""
        if pid in self.page_table:
            start_addr, amount_bytes = self.page_table[pid]

            # Secure memory wipe
            self.ram.seek(start_addr)
            self.ram.write(b'\x00' * amount_bytes)

            self.available_ram += amount_bytes
            del self.page_table[pid]

            if not self.page_table:
                self.current_offset = 0
            return True
        return False

    def get_status(self):
        """Returns physical memory consumption metrics."""
        used_bytes = self.total_ram - self.available_ram
        used_mb = used_bytes // (1024 * 1024)
        total_mb = self.total_ram // (1024 * 1024)
        avail_mb = self.available_ram // (1024 * 1024)
        return f"PHYSICAL RAM: {used_mb}MB / {total_mb}MB USED | Available: {avail_mb}MB"

    def read_memory(self, pid):
        """Provides a hex dump of the first 30 bytes of a process's memory space."""
        if pid in self.page_table:
            start, size = self.page_table[pid]
            self.ram.seek(start)
            raw_data = self.ram.read(30)
            clean_data = raw_data.decode('utf-8', errors='ignore').strip('\x00')
            return f"Address 0x{start:08X} -> [{clean_data}]"
        return f"PID {pid} not found in physical memory."