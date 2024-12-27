class MIPS_Simulator:
    def __init__(self):
        # 32 adet register (0'dan 31'e kadar)
        self.registers = [0] * 32
        self.pc = 0  # Program Counter (PC)
        self.instruction_memory = bytearray(512)  # Instruction memory (512 baytlık)
        self.data_memory = bytearray(512)  # Data memory (512 baytlık)
        self.register_map = {
            "$zero": 0, "$at": 1, "$v0": 2, "$v1": 3,
            "$a0": 4, "$a1": 5, "$a2": 6, "$a3": 7,
            "$t0": 8, "$t1": 9, "$t2": 10, "$t3": 11,
            "$t4": 12, "$t5": 13, "$t6": 14, "$t7": 15,
            "$s0": 16, "$s1": 17, "$s2": 18, "$s3": 19,
            "$s4": 20, "$s5": 21, "$s6": 22, "$s7": 23,
            "$t8": 24, "$t9": 25, "$k0": 26, "$k1": 27,
            "$gp": 28, "$sp": 29, "$fp": 30, "$ra": 31
        }

    def display_registers(self):
        """Registers' durumunu ve Program Counter'ı gösteren fonksiyon."""
        register_table = ""
        register_table += "+-------+------------------+\n"
        register_table += "| Reg # | Value (Decimal) |\n"
        register_table += "+-------+------------------+\n"
        for i in range(32):
            register_table += f"|  ${i:<2}  | {self.registers[i]:<16}|\n"
        register_table += "+-------+------------------+\n"
        register_table += f"PC: {self.pc}\n"
        return register_table

    def display_instruction_memory(self):
        """Instruction memory'nin içeriğini gösterir."""
        instruction_memory = "\nInstruction Memory:\n"
        for i in range(0, len(self.instruction_memory), 4):
            instruction = self.instruction_memory[i:i + 4]
            instruction_memory += f"Address {i:03d}: {instruction.hex().upper()}\n"
        return instruction_memory

    def display_data_memory(self):
        """Data memory'nin içeriğini gösterir."""
        data_memory = "\nData Memory:\n"
        for i in range(0, len(self.data_memory), 4):
            data = self.data_memory[i:i + 4]
            data_memory += f"Address {i:03d}: {data.hex().upper()}\n"
        return data_memory

    def execute_instruction(self, instruction):
        """Verilen talimatı işler, Program Counter'ı günceller ve belleği değiştirir."""
        parts = instruction.split()
        opcode = parts[0]

        # Talimatı instruction memory'e kaydet
        machine_code = self.machine_code(instruction)
        self.instruction_memory[self.pc:self.pc + 4] = machine_code.encode('utf-8')

        # Talimatı çalıştır
        if opcode == "add":
            rd, rs, rt = map(self.parse_register, parts[1:])
            self.registers[rd] = self.registers[rs] + self.registers[rt]
        elif opcode == "sub":
            rd, rs, rt = map(self.parse_register, parts[1:])
            self.registers[rd] = self.registers[rs] - self.registers[rt]
        elif opcode == "and":
            rd, rs, rt = map(self.parse_register, parts[1:])
            self.registers[rd] = self.registers[rs] & self.registers[rt]
        elif opcode == "or":
            rd, rs, rt = map(self.parse_register, parts[1:])
            self.registers[rd] = self.registers[rs] | self.registers[rt]
        elif opcode == "slt":
            rd, rs, rt = map(self.parse_register, parts[1:])
            self.registers[rd] = 1 if self.registers[rs] < self.registers[rt] else 0
        elif opcode == "addi":
            rt, rs, imm = parts[1], parts[2], int(parts[3])  # Düzeltme: imm, int'e dönüştürülmeli
            rs = self.parse_register(rs)
            rt = self.parse_register(rt)
            self.registers[rt] = self.registers[rs] + imm
        elif opcode == "lw":
            rt = self.parse_register(parts[1])
            offset, base = parts[2].split('(')
            offset = int(offset)
            base = self.parse_register(base[:-1])  # Parantezi kaldır
            address = self.registers[base] + offset
            self.registers[rt] = self.load_word(address)
        elif opcode == "sw":
            rt = self.parse_register(parts[1])
            offset, base = parts[2].split('(')
            offset = int(offset)
            base = self.parse_register(base[:-1])  # Parantezi kaldır
            address = self.registers[base] + offset
            self.store_word(address, self.registers[rt])
        elif opcode == "j":
            target_address = int(parts[1])
            self.pc = target_address
        elif opcode == "jal":
            target_address = int(parts[1])
            self.registers[31] = self.pc + 4  # $ra (return address) kaydet
            self.pc = target_address
        elif opcode == "jr":
            register = self.parse_register(parts[1])
            self.pc = self.registers[register]
        elif opcode == "sll":
            rd = self.parse_register(parts[1])
            rt = self.parse_register(parts[2])
            shamt = int(parts[3])
            self.registers[rd] = self.registers[rt] << shamt
        elif opcode == "srl":
            rd = self.parse_register(parts[1])
            rt = self.parse_register(parts[2])
            shamt = int(parts[3])
            self.registers[rd] = self.registers[rt] >> shamt

        elif opcode == "beq":
            rs, rt, offset = parts[1], parts[2], int(parts[3])
            rs = self.parse_register(rs)
            rt = self.parse_register(rt)
            if self.registers[rs] == self.registers[rt]:
                target_address = self.pc + ((offset + 1) * 4)
                self.pc = target_address  # Update program counter to branch target
                return  # Skip the rest of the code and jump to the target

        elif opcode == "bne":
            rs, rt, offset = parts[1], parts[2], int(parts[3])
            rs = self.parse_register(rs)
            rt = self.parse_register(rt)

            # Eğer register'lar eşit değilse, dallan
            if self.registers[rs] != self.registers[rt]:
                # Hedef adresi hesapla
                target_address = self.pc + ((offset + 1) * 4)
                self.pc = target_address  # PC'yi dallanma adresine ayarla
                return  # Daha fazla işlem yapma

        self.pc += 4  # Program Counter'ı bir sonraki talimata taşı

    def parse_register(self, reg):
        """Register adını, karşılık gelen register numarasına dönüştürür."""
        reg = reg.strip(",")  # Virgül ve boşlukları temizle
        if reg in self.register_map:
            return self.register_map[reg]
        else:
            raise ValueError(f"Geçersiz register adı: {reg}.")

    def machine_code(self, instruction):
        """Verilen talimat için makine kodu simülasyonu yapar."""
        parts = instruction.split()
        opcode = parts[0]

        if opcode == "add" or opcode == "sub" or opcode == "and" or opcode == "or" or opcode == "slt":
            # R-type komutları
            rd, rs, rt = map(self.parse_register, parts[1:])
            if opcode == "add":
                func = 32  # add
            elif opcode == "sub":
                func = 34  # sub
            elif opcode == "and":
                func = 36  # and
            elif opcode == "or":
                func = 37  # or
            elif opcode == "slt":
                func = 42  # slt

            # Makine kodunu 32-bitlik integer olarak oluştur
            instruction = (0 << 26) | (rs << 21) | (rt << 16) | (rd << 11) | (0 << 6) | func
            return format(instruction, '032b')

        elif opcode == "addi":
            # I-type komutları (addi)
            rt, rs, imm = parts[1], parts[2], int(parts[3])
            rs = self.parse_register(rs)
            rt = self.parse_register(rt)

            # Makine kodunu 32-bitlik integer olarak oluştur
            instruction = (8 << 26) | (rs << 21) | (rt << 16) | imm
            return format(instruction, '032b')

        elif opcode == "lw" or opcode == "sw":
            # I-type komutları (lw, sw)
            rt = self.parse_register(parts[1])
            offset, base = parts[2].split('(')
            base = self.parse_register(base[:-1])
            offset = int(offset)

            if opcode == "lw":
                opcode_value = 35  # lw
            elif opcode == "sw":
                opcode_value = 43  # sw

            instruction = (opcode_value << 26) | (base << 21) | (rt << 16) | offset
            return format(instruction, '032b')

        elif opcode == "j":
            # J-type komutları (j)
            target_address = int(parts[1])
            instruction = (2 << 26) | (target_address & 0x03FFFFFF)  # Mask for 26 bits
            return format(instruction, '032b')

        elif opcode == "jal":
            # J-type komutları (jal)
            target_address = int(parts[1])
            instruction = (3 << 26) | (target_address & 0x03FFFFFF)  # Mask for 26 bits
            return format(instruction, '032b')

        elif opcode == "jr":
            # R-type komutları (jr)
            rs = self.parse_register(parts[1])
            instruction = (0 << 26) | (rs << 21) | (0 << 16) | (0 << 11) | (0 << 6) | 8  # func = 8 for jr
            return format(instruction, '032b')

        elif opcode == "sll":
            # R-type komutları (sll)
            rd = self.parse_register(parts[1])
            rt = self.parse_register(parts[2])
            shamt = int(parts[3])
            instruction = (0 << 26) | (0 << 21) | (rt << 16) | (rd << 11) | (shamt << 6) | 0
            return format(instruction, '032b')

        elif opcode == "srl":
            # R-type komutları (srl)
            rd = self.parse_register(parts[1])
            rt = self.parse_register(parts[2])
            shamt = int(parts[3])
            instruction = (0 << 26) | (0 << 21) | (rt << 16) | (rd << 11) | (shamt << 6) | 2
            return format(instruction, '032b')

        elif opcode == "beq":
            # I-type komutları (beq)
            rs, rt, offset = parts[1], parts[2], int(parts[3])
            rs = self.parse_register(rs)
            rt = self.parse_register(rt)

            # Makine kodunu 32-bitlik integer olarak oluştur
            instruction = (4 << 26) | (rs << 21) | (rt << 16) | offset
            return format(instruction, '032b')

        elif opcode == "bne":
            # I-type komutları (bne)
            rs, rt, offset = parts[1], parts[2], int(parts[3])
            rs = self.parse_register(rs)
            rt = self.parse_register(rt)

            # Makine kodunu 32-bitlik integer olarak oluştur
            instruction = (5 << 26) | (rs << 21) | (rt << 16) | offset
            return format(instruction, '032b')

        else:
            raise ValueError(f"Geçersiz opcode: {opcode}.")

    def load_word(self, address):
        """Data memory'den 4 byte'lık veri yükler."""
        if address % 4 != 0:
            raise ValueError(f"Unaligned memory access at address {address}. Address must be word-aligned (4 bytes).")
        if address < 0 or address + 4 > len(self.data_memory):
            raise ValueError(f"Memory access out of bounds at address {address}.")
        data = self.data_memory[address:address + 4]
        return int.from_bytes(data, byteorder='big')

    def store_word(self, address, value):
        """Data memory'ye 4 byte'lık veri yazar."""
        if address % 4 != 0:
            raise ValueError(f"Unaligned memory access at address {address}. Address must be word-aligned (4 bytes).")
        if address < 0 or address + 4 > len(self.data_memory):
            raise ValueError(f"Memory access out of bounds at address {address}.")
        self.data_memory[address:address + 4] = value.to_bytes(4, byteorder='big')