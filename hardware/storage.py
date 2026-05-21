"""
Storage Architecture
Handles raw block device I/O and the Virtual File System (VFS).
"""
import os
import json

class BlockStorageDevice:
    """Provides raw sector-level read/write access to a binary image file."""
    def __init__(self, disk_file="shadow_drive.img", size_mb=1):
        # Ensure the drive is created in the root directory, not inside the hardware folder
        self.disk_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), disk_file)
        self.sector_size = 512
        self.total_size = size_mb * 1024 * 1024
        self.mount_drive()

    def mount_drive(self):
        if not os.path.exists(self.disk_file):
            with open(self.disk_file, "wb") as f:
                f.write(b'\x00' * self.total_size)

    def write_sector(self, sector_index, data_string):
        data_bytes = data_string.encode('utf-8')
        if len(data_bytes) > self.sector_size:
            return False, "IO_ERROR: Data exceeds 512-byte hardware sector limit."

        padded_data = data_bytes.ljust(self.sector_size, b'\x00')
        with open(self.disk_file, "r+b") as f:
            f.seek(sector_index * self.sector_size)
            f.write(padded_data)
        return True, "SUCCESS"

    def read_sector(self, sector_index):
        with open(self.disk_file, "rb") as f:
            f.seek(sector_index * self.sector_size)
            raw_data = f.read(self.sector_size)
        return raw_data.rstrip(b'\x00').decode('utf-8', errors='ignore')

class VirtualFileSystem:
    """Manages file allocation, fragmentation, and multi-sector spanning."""
    def __init__(self):
        self.drive = BlockStorageDevice()
        self.fat = {}
        self.load_fat()

    def load_fat(self):
        """Reconstructs the file map from the Master Boot Record (Sector 0)."""
        raw_fat = self.drive.read_sector(0)
        if raw_fat and raw_fat.strip():
            try:
                self.fat = json.loads(raw_fat)
                for key, val in self.fat.items():
                    if isinstance(val, int):
                        self.fat[key] = [val]
            except json.JSONDecodeError:
                self.fat = {}

    def save_fat(self):
        """Serializes and writes the file map to Sector 0."""
        fat_data = json.dumps(self.fat)
        self.drive.write_sector(0, fat_data)

    def write_file(self, filename, content):
        self.delete_file(filename)
        chunk_size = 500
        chunks = [content[i:i + chunk_size] for i in range(0, max(1, len(content)), chunk_size)]

        used_sectors = {0}
        for sectors in self.fat.values():
            used_sectors.update(sectors)

        max_sectors = self.drive.total_size // self.drive.sector_size
        allocated_sectors = []
        current_sector = 1

        while len(allocated_sectors) < len(chunks):
            if current_sector >= max_sectors:
                return False
            if current_sector not in used_sectors:
                allocated_sectors.append(current_sector)
            current_sector += 1

        for i, sector in enumerate(allocated_sectors):
            self.drive.write_sector(sector, chunks[i])

        self.fat[filename] = allocated_sectors
        self.save_fat()
        return True

    def read_file(self, filename):
        if filename in self.fat:
            return "".join(self.drive.read_sector(sector) for sector in self.fat[filename])
        return None

    def list_files(self):
        return list(self.fat.keys())

    def delete_file(self, filename):
        if filename in self.fat:
            for sector in self.fat[filename]:
                self.drive.write_sector(sector, "")
            del self.fat[filename]
            self.save_fat()
            return True
        return False