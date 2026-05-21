"""
Terminal Interface
The graphical front-end for PyVisor, built with CustomTkinter.
"""
import customtkinter as ctk
from core.kernel import HypervisorKernel

ctk.set_appearance_mode("dark")

class TerminalInterface(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.kernel = HypervisorKernel()
        self.title("PyVisor - Type-2 Hypervisor")
        self.geometry("1000x600")
        self.configure(fg_color="#0a0a0a")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.console_display = ctk.CTkTextbox(
            self, fg_color="#050505", text_color="#00FF41", font=("Courier New", 15),
            border_width=2, border_color="#1a1a1a"
        )
        self.console_display.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="nsew")

        self.input_field = ctk.CTkEntry(
            self, placeholder_text="Enter System Command...", fg_color="#0f0f0f",
            text_color="#00FF41", font=("Courier New", 14), height=40, border_color="#1a1a1a"
        )
        self.input_field.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="ew")

        self.input_field.bind("<Return>", self.process_command)
        self.input_field.bind("<Up>", self.history_up)
        self.input_field.bind("<Down>", self.history_down)

        self.cmd_index = 0
        self.boot_sequence()
        self.start_system_clock()

    def start_system_clock(self):
        self.hardware_tick()

    def hardware_tick(self):
        output = self.kernel.cmd_step(["--silent"])

        if "[SYSTEM]" in output or "FATAL" in output:
            self.console_display.configure(state="normal")
            self.console_display.insert("end", f"\n{output}\n>> ")
            self.console_display.configure(state="disabled")
            self.console_display.see("end")

        self.after(2000, self.hardware_tick)

    def boot_sequence(self):
        msg = "[SYSTEM] PyVisor Microkernel v1.0 Online...\n[SYSTEM] Cognitive Subsystem: Initialized\n>> "
        self.console_display.insert("end", msg)
        self.console_display.configure(state="disabled")

    def history_up(self, event):
        history = self.kernel.session_history
        if history and self.cmd_index < len(history):
            self.cmd_index += 1
            self.input_field.delete(0, 'end')
            self.input_field.insert(0, history[-self.cmd_index])

    def history_down(self, event):
        history = self.kernel.session_history
        if history and self.cmd_index > 1:
            self.cmd_index -= 1
            self.input_field.delete(0, 'end')
            self.input_field.insert(0, history[-self.cmd_index])
        elif self.cmd_index == 1:
            self.cmd_index = 0
            self.input_field.delete(0, 'end')

    def process_command(self, event):
        self.cmd_index = 0
        cmd = self.input_field.get()
        if not cmd: return

        self.console_display.configure(state="normal")
        self.console_display.insert("end", f"\nroot@pyvisor:~$ {cmd}\n")

        if cmd.lower() == "clear":
            self.console_display.delete("1.0", "end")
            response = "[SYSTEM] Console cleared."
        else:
            response = self.kernel.handle_call(cmd)

        self.console_display.insert("end", f"{response}\n>> ")
        self.console_display.configure(state="disabled")

        self.input_field.delete(0, 'end')
        self.console_display.see("end")