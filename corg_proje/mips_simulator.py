import tkinter as tk

# 32 Register tanımı ve başlangıç değerleri
register_names = [
    "$zero", "$at", "$v0", "$v1", "$a0", "$a1", "$a2", "$a3",
    "$t0", "$t1", "$t2", "$t3", "$t4", "$t5", "$t6", "$t7",
    "$s0", "$s1", "$s2", "$s3", "$s4", "$s5", "$s6", "$s7",
    "$t8", "$t9", "$k0", "$k1", "$gp", "$sp", "$fp", "$ra"
]
registers = {name: 0 for name in register_names}
memory = [0] * 512  # 512 byte'lık bellek
instruction_memory = [""] * 512  # 512 byte'lık Instruction Memory
labels = {}  # Label'ların satır numaralarını tutar
pc = 0  # Program Counter (Global olarak tanımlandı)
realistic_pc = 0  # Donanımsal PC
commands = []  # Komut listesi


# Machine Code alanını güncelleyen fonksiyon
def update_machine_code_display():
    machine_code_text.delete("1.0", tk.END)
    for i, instruction in enumerate(instruction_memory):
        if instruction.strip():
            binary_code = convert_to_machine_code(instruction)
            machine_code_text.insert(tk.END, f"{i:03}: {binary_code}\n")  # Ok eklenmedi


def convert_to_machine_code(instruction):
    try:
        parts = instruction.strip().split()
        if not parts:
            return "0000000000000000"  # Boş satırı varsayılan kod

        opcode_map = {
            "add": "000000",
            "sub": "000001",
            "and": "000010",
            "or": "000011",
            "slt": "000100",
            "sll": "000101",
            "srl": "000110",
            "addi": "001000",
            "sw": "001001",
            "lw": "001010",
            "beq": "001011",
            "bne": "001100",
            "j": "001101",
            "jal": "001110",
            "jr": "001111",
        }

        opcode = opcode_map.get(parts[0], "??????")
        if opcode == "??????":
            return f"INVALID ({parts[0]})"  # Geçersiz komut

        if parts[0] in ["add", "sub", "and", "or", "slt", "sll", "srl"]:
            rd, rs, rt = parts[1].rstrip(","), parts[2].rstrip(","), parts[3]
            return f"{opcode}{register_names.index(rs):05b}{register_names.index(rt):05b}{register_names.index(rd):05b}00000"
        elif parts[0] in ["addi"]:
            rt, rs, imm = parts[1].rstrip(","), parts[2].rstrip(","), int(parts[3])
            return f"{opcode}{register_names.index(rs):05b}{register_names.index(rt):05b}{imm & 0xFFFF:016b}"
        elif parts[0] in {"lw", "sw"}:  # I-Type lw ve sw
            try:
                rt = format(register_names.index(parts[1].rstrip(",")), "05b")
                offset, rs = parts[2].split("(")
                rs = rs.rstrip(")")
                rs = format(register_names.index(rs), "05b")
                imm = format(int(offset), "016b")
                return f"{opcode}{rs}{rt}{imm}"
            except (ValueError, IndexError, KeyError):
                return f"ERROR ({instruction}): Invalid memory access or format"

        elif parts[0] in ["beq", "bne"]:
            rs, rt, label = parts[1].rstrip(","), parts[2].rstrip(","), parts[3]
            address = labels.get(label, 0)
            return f"{opcode}{register_names.index(rs):05b}{register_names.index(rt):05b}{address:016b}"
        elif parts[0] in ["j", "jal"]:
            label = parts[1]
            address = labels.get(label, 0)
            return f"{opcode}{address:026b}"
        elif parts[0] == "jr":
            rs = parts[1]
            return f"{opcode}{register_names.index(rs):05b}0000000000000000"

        return "INVALID"  # Geçersiz komutlar için
    except (ValueError, IndexError, KeyError) as e:
        return f"ERROR ({instruction}): {e}"


# Komutları yükleyen fonksiyon
def load_commands():
    global commands, labels, pc, realistic_pc
    commands = input_text.get("1.0", tk.END).strip().split("\n")  # Çok satırlı input
    labels = {}
    pc = 0
    realistic_pc = 0
    cleaned_commands = []

    for i, command in enumerate(commands):
        command = command.strip()
        if ":" in command:  # Etiket var mı kontrol et
            parts = command.split(":")
            label = parts[0].strip()
            labels[label] = len(cleaned_commands)  # Etiketi geçerli komut satırına bağla
            # Eğer ":" sonrası komut varsa, bunu da komut olarak ekle
            if len(parts) > 1 and parts[1].strip():
                cleaned_commands.append(parts[1].strip())
        else:
            cleaned_commands.append(command)

    commands = cleaned_commands
    result_label.config(text="Komutlar yüklendi! Step veya Run ile çalıştırabilirsiniz.", fg="blue")


def process_labels():
    global labels
    for i, command in enumerate(commands):
        command = command.strip()
        if command and command[-1] == ":":  # Etiket satırı
            label = command[:-1]  # ":" işaretini kaldır
            labels[label] = i  # Etiketi labels sözlüğüne ekle


# Tek bir komutu işleyen fonksiyon
def step_command():
    global pc, realistic_pc
    instruction = fetch_instruction(pc)  # Instruction Memory'den komut al
    if instruction is None or instruction.strip() == "":
        result_label.config(text="Program sonlandı.", fg="green")
        return

    parts = instruction.strip().split()  # Komut parçalarını ayır

    if not parts:  # Eğer boş bir satırsa, bir sonraki komuta geç
        pc += 1
        realistic_pc += 4
        update_pc_display()
        return

    update_machine_code_display()

    try:
        if parts[0] == "add":  # R-Type add
            rd, rs, rt = parts[1].rstrip(","), parts[2].rstrip(","), parts[3]
            registers[rd] = registers[rs] + registers[rt]
        elif parts[0] == "sub":  # R-Type sub
            rd, rs, rt = parts[1].rstrip(","), parts[2].rstrip(","), parts[3]
            registers[rd] = registers[rs] - registers[rt]
        elif parts[0] == "and":  # R-Type and
            rd, rs, rt = parts[1].rstrip(","), parts[2].rstrip(","), parts[3]
            registers[rd] = registers[rs] & registers[rt]
        elif parts[0] == "or":  # R-Type or
            rd, rs, rt = parts[1].rstrip(","), parts[2].rstrip(","), parts[3]
            registers[rd] = registers[rs] | registers[rt]
        elif parts[0] == "slt":  # R-Type slt
            rd, rs, rt = parts[1].rstrip(","), parts[2].rstrip(","), parts[3]
            registers[rd] = 1 if registers[rs] < registers[rt] else 0
        elif parts[0] == "sll":  # R-Type sll
            rd, rt, shamt = parts[1].rstrip(","), parts[2].rstrip(","), int(parts[3])
            registers[rd] = registers[rt] << shamt
        elif parts[0] == "srl":  # R-Type srl
            rd, rt, shamt = parts[1].rstrip(","), parts[2].rstrip(","), int(parts[3])
            registers[rd] = registers[rt] >> shamt
        elif parts[0] == "addi":  # I-Type addi
            if len(parts) != 4:
                result_label.config(text=f"Geçersiz addi komutu: {instruction}", fg="red")
                return
            try:
                rt, rs, imm = parts[1].rstrip(","), parts[2].rstrip(","), int(parts[3])
                if rt not in registers or rs not in registers:
                    result_label.config(text=f"Geçersiz register: {rt} veya {rs}", fg="red")
                    return
                registers[rt] = registers[rs] + imm
            except ValueError:
                result_label.config(text=f"Geçersiz immediate değer: {parts[3]}", fg="red")
                return
        elif parts[0] == "sw":  # I-Type sw
            rt, offset_rs = parts[1].rstrip(","), parts[2]
            offset, rs = offset_rs.split("(")
            rs = rs.rstrip(")")
            address = registers[rs] + int(offset)
            if 0 <= address < len(memory):  # Bellek sınırı kontrolü
                memory[address] = registers[rt]
                update_memory_display()  # Belleği güncelle
            else:
                result_label.config(text=f"Geçersiz bellek adresi: {address}", fg="red")
                return

        elif parts[0] == "lw":  # I-Type lw
            rt, offset_rs = parts[1].rstrip(","), parts[2]
            offset, rs = offset_rs.split("(")
            rs = rs.rstrip(")")
            address = registers[rs] + int(offset)
            if 0 <= address < len(memory):  # Bellek sınırı kontrolü
                registers[rt] = memory[address]
            else:
                result_label.config(text=f"Geçersiz bellek adresi: {address}", fg="red")
                return

        elif parts[0] == "beq":  # I-Type beq
            rs, rt, label = parts[1].rstrip(","), parts[2].rstrip(","), parts[3]
            if registers[rs] == registers[rt]:
                if label in labels:
                    pc = labels[label]  # Etiketle yönlendir
                    realistic_pc = pc * 4  # Realistic PC'yi güncelle
                    update_pc_display()
                    update_instruction_memory_display()  # Dinamik olarak Instruction Memory'yi güncelle
                    update_register_display()
                    update_machine_code_display()  # Machine Code alanını güncelle
                    return
                else:
                    result_label.config(text=f"Etiket bulunamadı: {label}", fg="red")
                    return
            else:
                pc += 1
                realistic_pc += 4
                update_pc_display()
                return

        elif parts[0] == "bne":  # I-Type bne
            rs, rt, label = parts[1].rstrip(","), parts[2].rstrip(","), parts[3]
            if registers[rs] != registers[rt]:
                if label in labels:
                    pc = labels[label]  # Etiketle yönlendir
                    realistic_pc = pc * 4  # Realistic PC'yi güncelle
                    update_pc_display()
                    update_instruction_memory_display()  # Instruction Memory'yi güncelle
                    update_register_display()
                    update_machine_code_display()  # Machine Code alanını güncelle
                    return
                else:
                    result_label.config(text=f"Etiket bulunamadı: {label}", fg="red")
                    return
            pc += 1
            realistic_pc += 1
            update_memory_display()

        elif parts[0] == "j":  # J-Type j
            label = parts[1]
            if label in labels:
                pc = labels[label]
                realistic_pc = pc * 4  # Realistic PC'yi güncelle
                update_pc_display()
                update_register_display()
                update_machine_code_display()  # Machine Code alanını güncelle
                return
            else:
                result_label.config(text=f"Etiket bulunamadı: {label}", fg="red")
                return

        elif parts[0] == "jal":  # J-Type jal
            label = parts[1]
            if label in labels:
                registers["$ra"] = pc + 1  # Return Address
                pc = labels[label]
                realistic_pc = pc * 4  # Realistic PC'yi güncelle
                update_pc_display()
                update_register_display()
                update_machine_code_display()  # Machine Code alanını güncelle
                return
            else:
                result_label.config(text=f"Etiket bulunamadı: {label}", fg="red")
                return

        elif parts[0] == "jr":  # J-Type jr
            rs = parts[1]
            pc = registers[rs]
            realistic_pc = pc * 4  # Realistic PC'yi güncelle
            update_pc_display()
            update_instruction_memory_display()
            update_register_display()
            update_machine_code_display()  # Machine Code alanını güncelle
            result_label.config(text=f"Komut işlendi: jr {rs} (Realistic PC: {realistic_pc})",
                                fg="blue")  # Doğru değeri yazdır
            return

        else:
            result_label.config(text=f"Geçersiz komut: {instruction}", fg="red")
            return
    except KeyError:
        result_label.config(text=f"Register hatası: {instruction}", fg="red")
        return
    except ValueError:
        result_label.config(text=f"Geçersiz değer: {instruction}", fg="red")
        return

    pc += 1  # Bir sonraki komuta geç
    realistic_pc += 4
    update_pc_display()
    update_register_display()
    update_machine_code_display()  # Machine Code alanını güncelle
    result_label.config(text=f"Komut işlendi: {instruction}", fg="blue")


def run_command():
    global pc, realistic_pc
    while pc < len(instruction_memory):  # Program Counter, komut belleğinin sınırları içinde
        instruction = fetch_instruction(pc)  # Komutu al
        if instruction is None or instruction.strip() == "":  # Eğer komut yoksa programı sonlandır
            break

        parts = instruction.strip().split()  # Komut parçalarına ayır
        if not parts:  # Eğer boş bir komutsa bir sonraki komuta geç
            pc += 1
            realistic_pc += 4
            update_pc_display()
            continue

        try:
            if parts[0] == "add":  # R-Type add
                rd, rs, rt = parts[1].rstrip(","), parts[2].rstrip(","), parts[3]
                registers[rd] = registers[rs] + registers[rt]
            elif parts[0] == "sub":  # R-Type sub
                rd, rs, rt = parts[1].rstrip(","), parts[2].rstrip(","), parts[3]
                registers[rd] = registers[rs] - registers[rt]

            elif parts[0] == "and":  # R-Type and
                rd, rs, rt = parts[1].rstrip(","), parts[2].rstrip(","), parts[3]
                registers[rd] = registers[rs] & registers[rt]
            elif parts[0] == "or":  # R-Type or
                rd, rs, rt = parts[1].rstrip(","), parts[2].rstrip(","), parts[3]
                registers[rd] = registers[rs] | registers[rt]
            elif parts[0] == "slt":  # R-Type slt
                rd, rs, rt = parts[1].rstrip(","), parts[2].rstrip(","), parts[3]
                registers[rd] = 1 if registers[rs] < registers[rt] else 0
            elif parts[0] == "sll":  # R-Type sll
                rd, rt, shamt = parts[1].rstrip(","), parts[2].rstrip(","), int(parts[3])
                registers[rd] = registers[rt] << shamt
            elif parts[0] == "srl":  # R-Type srl
                rd, rt, shamt = parts[1].rstrip(","), parts[2].rstrip(","), int(parts[3])
                registers[rd] = registers[rt] >> shamt

            elif parts[0] == "addi":  # I-Type addi
                rt, rs, imm = parts[1].rstrip(","), parts[2].rstrip(","), int(parts[3])
                if rt in registers and rs in registers:
                    registers[rt] = registers[rs] + imm
                else:
                    result_label.config(text=f"Geçersiz register: {rt} veya {rs}", fg="red")
                    return

            elif parts[0] == "sw":  # I-Type sw
                rt, offset_rs = parts[1].rstrip(","), parts[2]
                offset, rs = offset_rs.split("(")
                rs = rs.rstrip(")")
                address = registers[rs] + int(offset)
                if 0 <= address < len(memory):  # Bellek sınırı kontrolü
                    memory[address] = registers[rt]
                    update_memory_display()  # Belleği güncelle
                else:
                    result_label.config(text=f"Geçersiz bellek adresi: {address}", fg="red")
                    return

            elif parts[0] == "lw":  # I-Type lw
                rt, offset_rs = parts[1].rstrip(","), parts[2]
                offset, rs = offset_rs.split("(")
                rs = rs.rstrip(")")
                address = registers[rs] + int(offset)
                if 0 <= address < len(memory):  # Bellek sınırı kontrolü
                    registers[rt] = memory[address]
                else:
                    result_label.config(text=f"Geçersiz bellek adresi: {address}", fg="red")
                    return

            elif parts[0] == "beq":  # I-Type beq
                rs, rt, label = parts[1].rstrip(","), parts[2].rstrip(","), parts[3]
                if rs in registers and rt in registers:
                    if registers[rs] == registers[rt]:  # Dallanma
                        if label in labels:
                            pc = labels[label]
                            realistic_pc = pc * 4
                            update_instruction_memory_display()  # Dallanma sonrası komutları göster
                            continue
                        else:
                            result_label.config(text=f"Etiket bulunamadı: {label}", fg="red")
                            return
            elif parts[0] == "bne":  # I-Type bne
                rs, rt, label = parts[1].rstrip(","), parts[2].rstrip(","), parts[3]
                if rs in registers and rt in registers:
                    if registers[rs] != registers[rt]:  # Dallanma
                        if label in labels:
                            pc = labels[label]
                            realistic_pc = pc * 4
                            update_instruction_memory_display()  # Dallanma sonrası komutları göster
                            continue
                        else:
                            result_label.config(text=f"Etiket bulunamadı: {label}", fg="red")
                            return

            elif parts[0] == "j":  # J-Type j
                label = parts[1]
                if label in labels:
                    pc = labels[label]
                    realistic_pc = pc * 4
                    update_register_display()
                    update_machine_code_display()  # Machine Code alanını güncelle
                    return
                else:
                    result_label.config(text=f"Etiket bulunamadı: {label}", fg="red")
                    return

            elif parts[0] == "jal":  # J-Type jal
                label = parts[1]
                if label in labels:
                    registers["$ra"] = pc + 1  # Return Address
                    pc = labels[label]
                    realistic_pc = pc * 4
                    update_register_display()
                    update_machine_code_display()  # Machine Code alanını güncelle
                    return
                else:
                    result_label.config(text=f"Etiket bulunamadı: {label}", fg="red")
                    return

            elif parts[0] == "jr":  # J-Type jr
                rs = parts[1]
                pc = registers[rs]
                realistic_pc = pc * 4
                update_instruction_memory_display()
                update_register_display()
                update_machine_code_display()  # Machine Code alanını güncelle
                return

            elif parts[0] == "halt":  # Halt komutu
                result_label.config(text="Program sonlandı.", fg="green")
                break
            else:
                result_label.config(text=f"Geçersiz komut: {instruction}", fg="red")
                return
        except KeyError:
            result_label.config(text=f"Register hatası: {instruction}", fg="red")
            return
        except ValueError:
            result_label.config(text=f"Geçersiz değer: {instruction}", fg="red")
            return

        pc += 1  # Bir sonraki komuta geç
        realistic_pc += 4
        update_pc_display()

    # İşlem tamamlandıktan sonra tüm ekranları güncelle
    update_register_display()  # Register'ları güncelle
    update_memory_display()  # Belleği güncelle
    update_machine_code_display()
    result_label.config(text="Program sonlandı.", fg="green")


# Register ekranını güncelleyen fonksiyon
def update_register_display():
    for i, name in enumerate(register_names):
        register_labels[i][1].config(text=str(registers[name]))


# Register ekranını güncelleyen fonksiyon
def update_memory_display():
    memory_text.delete("1.0", tk.END)
    for i in range(0, len(memory), 4):  # 4 byte'lık bloklar halinde göster
        values = " ".join(f"{val:03}" for val in memory[i:i + 4])
        memory_text.insert(tk.END, f"{i:03}: {values}\n")


def load_instruction_memory():
    global instruction_memory
    commands = input_text.get("1.0", tk.END).strip().split("\n")
    for i, command in enumerate(commands):
        if i < len(instruction_memory):
            instruction_memory[i] = command.strip()
        else:
            result_label.config(text="Instruction Memory kapasitesini aştınız!", fg="red")
            return
    result_label.config(text="Instruction Memory yüklendi!", fg="blue")
    update_instruction_memory_display()


def fetch_instruction(pc):
    if 0 <= pc < len(instruction_memory):
        return instruction_memory[pc]
    else:
        result_label.config(text="Instruction Memory sınırını aştınız!", fg="red")
        return None


def update_pc_display():
    realistic_pc_value_label.config(text=f"Realistic PC: {realistic_pc:03}")  # Realistic PC'yi göster


def update_instruction_memory_display():
    instruction_memory_text.delete("1.0", tk.END)
    for i in range(pc, len(instruction_memory)):  # Yalnızca PC sonrası komutları göster
        instruction = instruction_memory[i]
        if instruction.strip():
            instruction_memory_text.insert(tk.END, f"{i:03}: {instruction}\n")


def load_all():
    global labels, instruction_memory, pc
    # Komutları çok satırlı girişten alın
    instructions = input_text.get("1.0", tk.END).strip().split("\n")  # Input alanından komutlar
    labels = {}  # Etiketleri sıfırla
    pc = 0  # Program Counter'ı sıfırla
    realistic_pc = 0
    instruction_memory = [""] * 512  # Instruction Memory'yi sıfırla

    # Komutları Instruction Memory'ye yükle
    for i, instruction in enumerate(instructions):
        instruction = instruction.strip()
        if i < len(instruction_memory):
            if ":" in instruction:  # Eğer bir etiket varsa
                parts = instruction.split(":")
                label = parts[0].strip()  # Etiket ismini al
                labels[label] = i  # Etiketin bulunduğu satırı kaydet
                if len(parts) > 1 and parts[1].strip():  # Etiket sonrası komut varsa
                    instruction_memory[i] = parts[1].strip()  # Komut kısmını yükle
                else:
                    instruction_memory[i] = ""  # Sadece etiket varsa komut boş
            else:
                instruction_memory[i] = instruction  # Komutu doğrudan yükle
        else:
            result_label.config(text="Instruction Memory kapasitesini aştınız!", fg="red")
            return

    # Yükleme işlemi tamamlandı
    result_label.config(text="Komutlar ve Instruction Memory yüklendi!", fg="blue")
    update_instruction_memory_display()
    update_machine_code_display()

    # Komutları Instruction Memory'ye ve gerekli yapıya yükle
    for i, command in enumerate(commands):
        command = command.strip()
        if i < len(instruction_memory):
            instruction_memory[i] = command  # Instruction Memory'ye ekle
        else:
            result_label.config(text="Instruction Memory kapasitesini aştınız!", fg="red")
            return

        # Etiketleri ayıkla ve komutları işle
        if ":" in command:  # Label kontrolü
            parts = command.split(":")
            label = parts[0].strip()
            labels[label] = i  # Etiketin bulunduğu satırı kaydet
            if len(parts) > 1 and parts[1].strip():  # Etiket sonrası komut varsa
                commands[i] = parts[1].strip()
            else:
                commands[i] = ""  # Etiketi temizle
        else:
            commands[i] = command

    result_label.config(text="Komutlar ve Instruction Memory yüklendi!", fg="blue")
    update_instruction_memory_display()


# Tkinter ana penceresi
root = tk.Tk()
root.title("MIPS Komut Simülatörü")

# Ana çerçeve
main_frame = tk.Frame(root)
main_frame.pack(padx=10, pady=10)

# Input alanı (çok satırlı)
input_frame = tk.Frame(main_frame)
input_frame.grid(row=0, column=0, padx=10)
tk.Label(input_frame, text="Input:").pack(anchor="w")
input_text = tk.Text(input_frame, width=40, height=20)
input_text.pack()
run_button = tk.Button(input_frame, text="Run", command=run_command)
run_button.pack(pady=5)
step_button = tk.Button(input_frame, text="Step", command=step_command)
step_button.pack(pady=5)
# Tek bir buton tanımlayın
load_button = tk.Button(input_frame, text="Load", command=load_all)
load_button.pack(pady=5)

# Register alanı için kaydırılabilir pencere
register_frame = tk.Frame(main_frame)
register_frame.grid(row=0, column=1, padx=10)

# Canvas ve Scrollbar ekleme
canvas = tk.Canvas(register_frame)
scrollbar = tk.Scrollbar(register_frame, orient="vertical", command=canvas.yview)
scrollable_frame = tk.Frame(canvas)

# Canvas ayarları
canvas.configure(yscrollcommand=scrollbar.set)

# Scrollable Frame içinde register'ları göster
register_labels = []
for i, name in enumerate(register_names):
    reg_label = tk.Label(scrollable_frame, text=name, width=20, anchor="w")
    reg_label.grid(row=i + 1, column=0, padx=5, pady=2)
    value_label = tk.Label(scrollable_frame, text="0", width=10, anchor="w")
    value_label.grid(row=i + 1, column=1, padx=5, pady=2)
    register_labels.append((reg_label, value_label))

# Memory alanı
memory_frame = tk.Frame(main_frame)
memory_frame.grid(row=0, column=2, padx=10)
tk.Label(memory_frame, text=" Data Memory (512 bytes):").pack(anchor="w")
memory_text = tk.Text(memory_frame, width=30, height=20)
memory_text.pack()

# Instruction Memory alanı
instruction_memory_frame = tk.Frame(main_frame)
instruction_memory_frame.grid(row=0, column=3, padx=10)
tk.Label(instruction_memory_frame, text="Instruction Memory (512 bytes):").pack(anchor="w")
instruction_memory_text = tk.Text(instruction_memory_frame, width=30, height=20)
instruction_memory_text.pack()

# Realistic PC alanı (Bellek alanlarının altında)
pc_frame = tk.Frame(main_frame)
pc_frame.grid(row=1, column=2, columnspan=2, pady=10)  # 2 sütuna yayılacak şekilde ayarlandı
tk.Label(pc_frame, text="Realistic Program Counter:").grid(row=0, column=0, sticky="w")
realistic_pc_value_label = tk.Label(pc_frame, text="Realistic PC: 000", width=15, anchor="w")
realistic_pc_value_label.grid(row=0, column=1, sticky="w")

# Machine Code ekranı (input'un altına eklenir)
machine_code_frame = tk.Frame(main_frame)
machine_code_frame.grid(row=1, column=0, padx=10, pady=10)

tk.Label(machine_code_frame, text="Machine Code:").pack(anchor="w")
machine_code_text = tk.Text(machine_code_frame, width=60, height=10)
machine_code_text.pack()

# Canvas ve Scrollbar yerleştir
canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
scrollbar.pack(side="right", fill="y")
canvas.pack(side="left", fill="both", expand=True)

# Scrollable Frame boyutlarını ayarlama
scrollable_frame.update_idletasks()  # Frame boyutlarını güncelle
canvas.config(scrollregion=canvas.bbox("all"))  # Scrollregion'ı ayarla

# Sonuç mesajı
result_label = tk.Label(root, text="", fg="green")
result_label.pack(pady=5)

# Ana döngü
root.mainloop()
