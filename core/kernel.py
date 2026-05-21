"""
Hypervisor Kernel
The central nervous system. Mounts hardware modules, manages processes,
and handles ring-0 syscall routing.
"""
import os
import re
import io
import contextlib
import multiprocessing

# Cross-Module Imports
from hardware.cpu import hardware_worker
from hardware.memory import MemoryManagementUnit
from hardware.storage import VirtualFileSystem
from hardware.network import VirtualNetworkInterface
from core.telemetry import TelemetryBus
from core.cognitive import CognitiveSubsystem

class HypervisorKernel:
    def __init__(self):
        self.session_history = []

        # Mount Hardware Subsystems
        self.memory = MemoryManagementUnit(total_ram_mb=128)
        self.vfs = VirtualFileSystem()
        self.nic = VirtualNetworkInterface()

        # Mount Core Services
        self.telemetry = TelemetryBus()
        self.cortex = CognitiveSubsystem()

        # Process Management State
        self.active_processes = {}
        self.next_pid = 1000
        self.process_queue = []
        self.resources = {"DATA_CORE": None, "NETWORK_PORT": None}

        # Dynamic Multi-Core Allocation
        self.host_cores = os.cpu_count() or 1
        self.virtual_cores = max(1, self.host_cores - 1)
        self.core_pool = multiprocessing.Pool(processes=self.virtual_cores)

        # UNIX-Standard Syscall Registry
        self.commands = {
            "memstat": self.cmd_memstat,
            "history": self.cmd_history,
            "panic": self.cmd_panic,
            "spawn": self.cmd_spawn,
            "ps": self.cmd_ps,
            "kill": self.cmd_kill,
            "step": self.cmd_step,
            "lock": self.cmd_lock,
            "unlock": self.cmd_unlock,
            "locks": self.cmd_locks,
            "ls": self.cmd_ls,
            "write": self.cmd_write,
            "cat": self.cmd_cat,
            "hexdump": self.cmd_hexdump,
            "cpuinfo": self.cmd_cpuinfo,
            "ping": self.cmd_ping,
            "fw": self.cmd_fw,
            "dmesg": self.cmd_dmesg,
            "wget": self.cmd_wget,
            "ctx": self.cmd_ctx,
            "agent-set": self.cmd_agent_set,
            "ask": self.cmd_ask,
            "run": self.cmd_run,
            "help": self.cmd_help
        }

    def handle_call(self, command_string):
        self.session_history.append(command_string)
        parts = command_string.strip().split()
        if not parts: return ""

        base_cmd = parts[0].lower()
        args = parts[1:]

        if base_cmd in self.commands:
            return self.commands[base_cmd](args)
        else:
            return self.trigger_interrupt(f"ILLEGAL_OPCODE: '{base_cmd}'")

    def trigger_interrupt(self, reason):
        return f"[INTERRUPT] 0xDEADBEEF - {reason}\n[SYSTEM] Suspending user thread. Logging anomaly..."

    # --- System Information ---
    def cmd_memstat(self, args):
        status = self.memory.get_status()
        active_processes = len(self.memory.page_table)
        return f"[KERNEL] {status}\n[KERNEL] Active Paged Processes: {active_processes}"

    def cmd_history(self, args):
        return f"[KERNEL] Trace History: {', '.join(self.session_history[-3:])}"

    def cmd_help(self, args):
        return f"[SYSTEM] Available utilities: {', '.join(self.commands.keys())}, clear"

    def cmd_panic(self, args):
        return self.trigger_interrupt("USER_INITIATED_KERNEL_PANIC")

    def cmd_cpuinfo(self, args):
        return f"[KERNEL] CPU Architecture:\n -> Host Physical Cores: {self.host_cores}\n -> Virtual Cores Allocated: {self.virtual_cores}"

    # --- Process & Thread Management ---
    def cmd_spawn(self, args):
        if len(args) < 3: return "[ERROR] Syntax: spawn <process_name> <ram_required> <cpu_cycles>"
        name = args[0]
        try:
            ram_req, cycles = int(args[1]), int(args[2])
        except ValueError:
            return "[ERROR] RAM and CPU cycles must be integers."

        success, msg = self.memory.allocate(self.next_pid, ram_req)
        if success:
            self.active_processes[self.next_pid] = {
                "name": name, "ram": ram_req, "state": "READY",
                "time_left": cycles, "holding": [], "waiting_for": None
            }
            self.process_queue.append(self.next_pid)
            assigned_pid = self.next_pid
            self.next_pid += 1

            self.telemetry.log("PROCESS_SPAWN", f"PID:{assigned_pid} NAME:{name} RAM:{ram_req}MB CYCLES:{cycles}")
            return f"[SYSTEM] Process '{name}' spawned. PID: {assigned_pid} | RAM: {ram_req}MB"
        return f"[SYSTEM FATAL] Failed to spawn '{name}'. {msg}"

    def cmd_ps(self, args):
        if not self.active_processes: return "[KERNEL] No active processes."
        output = "[KERNEL] ACTIVE PROCESS LIST:\n"
        output += f"{'PID':<6} | {'NAME':<15} | {'RAM':<8} | {'CYCLES':<8} | {'STATE'}\n"
        output += "-" * 55 + "\n"
        for pid, pcb in self.active_processes.items():
            output += f"{pid:<6} | {pcb['name']:<15} | {pcb['ram']}MB    | {pcb['time_left']:<8} | {pcb['state']}\n"
        return output.strip()

    def cmd_kill(self, args):
        if not args: return "[ERROR] Syntax: kill <pid>"
        try: target_pid = int(args[0])
        except ValueError: return "[ERROR] PID must be a number."

        if target_pid in self.active_processes:
            pcb = self.active_processes[target_pid]
            for res in list(pcb.get("holding", [])):
                self.cmd_unlock([str(target_pid), res])

            self.memory.free(target_pid)
            name = pcb["name"]
            if target_pid in self.process_queue: self.process_queue.remove(target_pid)
            del self.active_processes[target_pid]
            return f"[SYSTEM] Process {target_pid} ('{name}') terminated. Resources freed."
        return f"[ERROR] Process ID {target_pid} not found."

    def cmd_step(self, args):
        silent = "--silent" in args
        if not self.process_queue: return "" if silent else "[CPU] System idle."

        ready_processes = [pid for pid in self.process_queue if self.active_processes[pid]["state"] != "BLOCKED"]
        if not ready_processes and self.process_queue:
            return "[SYSTEM FATAL] CPU STALLED! All active processes BLOCKED. Deadlock detected."

        batch_to_run = ready_processes[:self.virtual_cores]
        output = "" if silent else f"[CPU] Multi-Core Dispatch. Firing {len(batch_to_run)} hardware threads...\n"

        workload = [(pid, 2) for pid in batch_to_run]
        completed_pids = self.core_pool.starmap(hardware_worker, workload)

        for pid in completed_pids:
            self.process_queue.remove(pid)
            pcb = self.active_processes[pid]
            pcb["state"] = "RUNNING"
            pcb["time_left"] -= 1

            if not silent: output += f"  -> [Hardware Core] PID {pid} processed successfully.\n"

            if pcb["time_left"] > 0:
                pcb["state"] = "READY"
                self.process_queue.append(pid)
            else:
                for res in list(pcb["holding"]):
                    self.cmd_unlock([str(pid), res])
                name = pcb["name"]
                self.memory.free(pid)
                del self.active_processes[pid]

                msg = f"[SYSTEM] Process {pid} ('{name}') completed. RAM freed."
                output += (msg + "\n") if silent else f"\n{msg}"
        return output.strip()

    # --- Resource Management (Mutex Locks) ---
    def cmd_locks(self, args):
        output = "[KERNEL] SYSTEM RESOURCES:\n"
        for res, owner in self.resources.items():
            status = "FREE" if owner is None else f"LOCKED BY PID {owner}"
            output += f"  -> {res}: {status}\n"
        return output.strip()

    def cmd_lock(self, args):
        if len(args) < 2: return "[ERROR] Syntax: lock <pid> <resource_name>"
        pid, res = int(args[0]), args[1].upper()

        if pid not in self.active_processes: return f"[ERROR] PID {pid} not found."
        if res not in self.resources: return f"[ERROR] Resource '{res}' does not exist."

        if self.resources[res] is None:
            self.resources[res] = pid
            self.active_processes[pid]["holding"].append(res)
            return f"[MUTEX] Resource '{res}' successfully locked by PID {pid}."

        owner = self.resources[res]
        if owner == pid: return f"[MUTEX] PID {pid} already owns '{res}'."

        self.active_processes[pid]["state"] = "BLOCKED"
        self.active_processes[pid]["waiting_for"] = res
        return f"[WARNING] '{res}' is locked by PID {owner}. PID {pid} is now BLOCKED."

    def cmd_unlock(self, args):
        if len(args) < 2: return "[ERROR] Syntax: unlock <pid> <resource_name>"
        pid, res = int(args[0]), args[1].upper()

        if self.resources.get(res) == pid:
            self.resources[res] = None
            self.active_processes[pid]["holding"].remove(res)
            for p_id, pcb in self.active_processes.items():
                if pcb["state"] == "BLOCKED" and pcb["waiting_for"] == res:
                    pcb["state"] = "READY"
                    pcb["waiting_for"] = None
                    return f"[MUTEX] '{res}' unlocked. Waking up PID {p_id}..."
            return f"[MUTEX] '{res}' unlocked by PID {pid}."
        return f"[ERROR] PID {pid} does not own '{res}'."

    # --- Virtual File System (VFS) Commands ---
    def cmd_ls(self, args):
        files = self.vfs.list_files()
        if not files: return "[VFS] The block drive is currently empty."
        output = "[VFS] Encrypted Files on Disk:\n"
        for f in files: output += f"  -> {f}\n"
        return output.strip()

    def cmd_write(self, args):
        if len(args) < 2: return "[ERROR] Syntax: write <filename> <content...>"
        filename = args[0]
        content = " ".join(args[1:])
        self.vfs.write_file(filename, content)
        self.telemetry.log("VFS_WRITE", f"FILE:{filename} LENGTH:{len(content)}bytes")
        return f"[VFS] File '{filename}' successfully written to disk."

    def cmd_cat(self, args):
        if not args: return "[ERROR] Syntax: cat <filename>"
        content = self.vfs.read_file(args[0])
        if content is None: return f"[ERROR] File '{args[0]}' does not exist."
        return f"[VFS] Reading '{args[0]}':\n>> {content}"

    def cmd_hexdump(self, args):
        if not args: return "[ERROR] Syntax: hexdump <pid>"
        try: return f"[MMU] Hex Dump: {self.memory.read_memory(int(args[0]))}"
        except ValueError: return "[ERROR] PID must be a number."

    # --- Networking Commands ---
    def cmd_ping(self, args):
        if not args: return "[ERROR] Syntax: ping <hostname_or_ip>"
        success, msg = self.nic.send_tcp_probe(args[0])
        return msg

    def cmd_fw(self, args):
        if not args or args[0].upper() not in ["ON", "OFF"]: return "[ERROR] Syntax: fw <ON/OFF>"
        state = args[0].upper() == "ON"
        self.nic.firewall["OUTBOUND"] = not state
        status = "ENABLED (Traffic Blocked)" if state else "DISABLED (Traffic Allowed)"
        return f"[FIREWALL] System Firewall is now {status}."

    def cmd_wget(self, args):
        if len(args) < 2: return "[ERROR] Syntax: wget <url> <filename>"
        url, filename = args[0], args[1]
        if not url.startswith("http"): url = "https://" + url
        payload, msg = self.nic.download_payload(url)
        if payload is None: return msg
        self.telemetry.log("NET_EXFILTRATION", f"SOURCE:{url} SIZE:{len(payload)}bytes")
        if self.vfs.write_file(filename, payload):
            return f"[vNIC] Payload secured. {len(payload)} bytes written to '{filename}'."
        return "[SYSTEM FATAL] Disk write failed."

    # --- Telemetry & Cognitive Commands ---
    def cmd_dmesg(self, args):
        lines = int(args[0]) if args and args[0].isdigit() else 10
        return self.telemetry.read_stream(lines)

    def cmd_ctx(self, args):
        memory_dump = self.telemetry.get_ai_context()
        return f"[AGENT-CONTEXT] Volatile Memory Buffer:\n{('-' * 40)}\n{memory_dump}\n{('-' * 40)}"

    def cmd_agent_set(self, args):
        if not args: return "[ERROR] Syntax: agent-set <OLLAMA/OPENROUTER/API/DORMANT> [model_name] [api_key]"
        provider = args[0]
        model = args[1] if len(args) > 1 else None
        api_key = args[2] if len(args) > 2 else None
        success, msg = self.cortex.set_provider(provider, api_key, model)
        return msg

    def cmd_ask(self, args):
        if not args: return "[ERROR] Syntax: ask <your message>"
        user_message = " ".join(args)
        system_context = self.telemetry.get_ai_context()

        response = self.cortex.query(system_context, user_message)
        self.telemetry.log("AGENT_COMM", f"PROMPT:'{user_message[:20]}...'")

        match = re.search(r'<EXEC>(.*?)</EXEC>', response)
        if match:
            raw_command = match.group(1).strip()
            parts = raw_command.split()
            base_cmd, cmd_args = parts[0], parts[1:]
            clean_response = re.sub(r'<EXEC>.*?</EXEC>', '', response).strip()

            if base_cmd in self.commands:
                cmd_result = self.commands[base_cmd](cmd_args)
                self.telemetry.log("AUTONOMIC_ACTION", raw_command)
                return f"[AGENT] {clean_response}\n\n[SYSTEM EXECUTOR] -> {raw_command}\n[RESULT] {cmd_result}"
            return f"[AGENT] {clean_response}\n\n[SYSTEM EXECUTOR ERROR] Unknown command '{base_cmd}'."

        return f"[AGENT] {response}"

    # --- Application Sandbox ---
    def cmd_run(self, args):
        if not args: return "[ERROR] Syntax: run <filename>"
        filename = args[0]
        script_code = self.vfs.read_file(filename)

        if not script_code: return f"[ERROR] File '{filename}' not found or is empty."
        self.telemetry.log("SYS_EXEC", f"Running script: {filename}")

        sandbox_globals = {"__builtins__": __builtins__, "kernel": self}
        output_buffer = io.StringIO()

        try:
            with contextlib.redirect_stdout(output_buffer):
                exec(script_code, sandbox_globals)
            output = output_buffer.getvalue().strip()
            result_msg = f"[SYSTEM] Program '{filename}' executed successfully."
            if output: result_msg += f"\n{('-' * 40)}\n{output}\n{('-' * 40)}"
            return result_msg
        except Exception as e:
            return f"[SYSTEM FATAL] Segmentation Fault in '{filename}': {str(e)}"