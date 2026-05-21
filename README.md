# Shadow OS: Type-2 Hypervisor Simulator

Shadow OS is a lightweight, Python-based Type-2 Hypervisor built to simulate bare-metal operating system architecture. It features hardware-bound multiprocessing, direct memory mapping, a virtualized block storage filesystem, and an integrated autonomous AI subsystem.

## Core Features
* **Hardware-Bound Threading:** Bypasses the Python GIL using `multiprocessing` to execute simulated CPU ticks across physical host cores.
* **True Memory Mapping:** Utilizes `mmap` to allocate and isolate real physical volatile memory for simulated processes.
* **Virtual Block Storage:** Implements a custom File Allocation Table (FAT) on a binary `.img` file with multi-sector spanning and fragmentation support.
* **Autonomous Cognitive Subsystem:** Routes kernel telemetry through Google's Gemini architecture, granting an LLM root-access to dynamically monitor and terminate anomalous processes.
* **Ring-3 Execution Sandbox:** Compiles and executes dynamic Python bytecode securely within the simulated environment.

## Installation
1. Clone the repository.
2. Install dependencies: `pip install -r requirements.txt`
3. Create a `.env` file in the root directory and add your Google Gemini API key:
   `GEMINI_API_KEY=your_key_here`
4. Run the bootloader: `python main.py`