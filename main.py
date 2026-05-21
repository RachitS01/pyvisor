"""
Shadow OS Bootloader
Entry point for the hypervisor. Initializes the hardware environment and launches the UI.
"""
import multiprocessing
from dotenv import load_dotenv
from ui.terminal import TerminalInterface

def boot():
    load_dotenv()

    # Instantiate and run the terminal interface
    app = TerminalInterface()
    app.mainloop()

if __name__ == "__main__":
    # Required for multiprocessing to safely spawn hardware threads on Windows architecture
    multiprocessing.freeze_support()
    boot()