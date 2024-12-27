from mips_simulator import MIPS_Simulator
import tkinter as tk
from tkinter import messagebox

class MIPS_Simulator_GUI:
    def __init__(self, master):
        self.master = master
        self.master.title("MIPS Simulator")

        # Create instance of the MIPS simulator
        self.simulator = MIPS_Simulator()

        # State variables
        self.instructions = []  # List of instructions
        self.machine_codes = []  # List of machine codes for each instruction
        self.current_instruction_index = 0  # Index for step-by-step execution

        # Create the GUI elements
        self.create_widgets()

    def create_widgets(self):
        # Register Display Section
        self.registers_label = tk.Label(self.master, text="Registers:")
        self.registers_label.grid(row=0, column=0, columnspan=2)

        self.registers_display = tk.Text(self.master, height=15, width=50)
        self.registers_display.grid(row=1, column=0, columnspan=2)
        self.update_registers_display()

        # Instruction Memory Display Section
        self.instruction_memory_label = tk.Label(self.master, text="Instruction Memory:")
        self.instruction_memory_label.grid(row=0, column=2, columnspan=2)

        self.instruction_memory_display = tk.Text(self.master, height=15, width=50)
        self.instruction_memory_display.grid(row=1, column=2, columnspan=2)
        self.update_instruction_memory_display()

        # Data Memory Display Section
        self.data_memory_label = tk.Label(self.master, text="Data Memory:")
        self.data_memory_label.grid(row=0, column=4, columnspan=2)

        self.data_memory_display = tk.Text(self.master, height=15, width=50)
        self.data_memory_display.grid(row=1, column=4, columnspan=2)
        self.update_data_memory_display()

        # Instruction Entry Section
        self.instruction_label = tk.Label(self.master, text="Enter Instructions (one per line):")
        self.instruction_label.grid(row=2, column=0, columnspan=2)

        self.instruction_entry = tk.Text(self.master, height=5, width=50)
        self.instruction_entry.grid(row=3, column=0, columnspan=2)

        # Run Program Button
        self.run_button = tk.Button(self.master, text="Run Program", command=self.run_program)
        self.run_button.grid(row=4, column=2, columnspan=2)

        # Step Button
        self.step_button = tk.Button(self.master, text="Step", command=self.step_instruction)
        self.step_button.grid(row=4, column=0, columnspan=2)

        # Program Counter Section
        self.pc_label = tk.Label(self.master, text="Program Counter:")
        self.pc_label.grid(row=5, column=0, columnspan=2)

        self.pc_display = tk.Label(self.master, text="0")
        self.pc_display.grid(row=6, column=0, columnspan=2)

        # Machine Code Display Section
        self.machine_code_label = tk.Label(self.master, text="Machine Code:")
        self.machine_code_label.grid(row=7, column=0, columnspan=2)

        self.machine_code_display = tk.Text(self.master, height=5, width=50)
        self.machine_code_display.grid(row=8, column=0, columnspan=2)

    def update_registers_display(self):
        """Update the display of registers."""
        register_table = self.simulator.display_registers()
        self.registers_display.delete(1.0, tk.END)
        self.registers_display.insert(tk.END, register_table)

    def update_instruction_memory_display(self):
        """Update the display of instruction memory."""
        instruction_memory = "\n".join(self.instructions) if self.instructions else "No instructions loaded."
        self.instruction_memory_display.delete(1.0, tk.END)
        self.instruction_memory_display.insert(tk.END, instruction_memory)

    def update_data_memory_display(self):
        """Update the display of data memory."""
        data_memory = self.simulator.display_data_memory()
        self.data_memory_display.delete(1.0, tk.END)
        self.data_memory_display.insert(tk.END, data_memory)

    def update_machine_code_display(self):
        """Update the display of all machine codes."""
        machine_codes_display = "\n".join(self.machine_codes)
        self.machine_code_display.delete(1.0, tk.END)
        self.machine_code_display.insert(tk.END, machine_codes_display)

    def update_pc_display(self):
        """Update the program counter display."""
        self.pc_display.config(text=str(self.simulator.pc))

    def execute_single_instruction(self, instruction):
        """Execute a single instruction and update all displays."""
        try:
            self.simulator.execute_instruction(instruction)
            machine_code = self.simulator.machine_code(instruction)
            self.machine_codes.append(machine_code)  # Store machine code
            self.update_machine_code_display()
            self.update_registers_display()
            self.update_instruction_memory_display()
            self.update_data_memory_display()
            self.update_pc_display()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def run_program(self):
        """Run all instructions entered by the user."""
        instructions = self.instruction_entry.get("1.0", tk.END).strip().split('\n')
        self.instructions = [instr.strip() for instr in instructions if instr.strip()]
        self.machine_codes = []  # Clear previous machine codes
        self.current_instruction_index = 0

        max_instructions = 10  # Limit to 10 instructions
        for i, instruction in enumerate(self.instructions):
            if i >= max_instructions:
                messagebox.showinfo("Info", f"Maximum of {max_instructions} instructions executed.")
                break
            self.execute_single_instruction(instruction)

    def step_instruction(self):
        """Execute one instruction at a time."""
        if not self.instructions:
            instructions = self.instruction_entry.get("1.0", tk.END).strip().split('\n')
            self.instructions = [instr.strip() for instr in instructions if instr.strip()]
            self.machine_codes = []  # Clear previous machine codes
            self.current_instruction_index = 0

        max_instructions = 10  # Limit to 10 instructions

        if self.current_instruction_index < len(self.instructions) and self.current_instruction_index < max_instructions:
            instruction = self.instructions[self.current_instruction_index]
            self.execute_single_instruction(instruction)
            self.current_instruction_index += 1
        else:
            if self.current_instruction_index >= max_instructions:
                messagebox.showinfo("Info", f"Maximum of {max_instructions} instructions executed.")
            else:
                messagebox.showinfo("Info", "All instructions have been executed.")

if __name__ == "__main__":
    root = tk.Tk()
    app = MIPS_Simulator_GUI(root)
    root.mainloop()