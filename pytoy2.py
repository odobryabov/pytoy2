import sys

class Computer:
	def __init__(self):
		self.registers = self.Registers()
		self.memory = self.Memory()
		self.alu = self.ALU()
		self.io = self.IO() # input output device
		self.pc = 0x10  # program counter
		
	class ALU:
		DATA_RESOLUTION = 16

		ALU_CTRL_ADD_SUB	= 0b000
		ALU_CTRL_AND		= 0b001
		ALU_CTRL_XOR		= 0b010
		ALU_CTRL_SHIFT		= 0b011
		ALU_CTRL_INPUT2		= 0b100

		half_adder = lambda self, a, b: (a ^ b, a & b)

		def full_adder(self, a, b, cr): 
			s1, c1 = self.half_adder(a, b)
			s, c2 = self.half_adder(cr, s1)
			return s, c1 | c2

		def adder_substractor(self, a, b, cr, sub):
			return self.full_adder(a, b ^ sub, cr)
		
		def alu(self, input1, input2, substract, shift_dir, ctrl):
			result = 0
			if ctrl == self.ALU_CTRL_ADD_SUB:
				carry = substract
				for position in range(self.DATA_RESOLUTION):
					bit1 = (input1 & (1 << position)) >> position
					bit2 = (input2 & (1 << position)) >> position
					result_bit, carry = self.adder_substractor(bit1, bit2, carry, substract)
					result = result | (result_bit << position)
			elif ctrl == self.ALU_CTRL_AND:
				result = input1 & input2
			elif ctrl == self.ALU_CTRL_XOR:
				result = input1 ^ input2
			elif ctrl == self.ALU_CTRL_SHIFT:
				if shift_dir == 0:
					result = input1 << (input2 % self.DATA_RESOLUTION)
				else:
					result = input1 >> (input2 % self.DATA_RESOLUTION)
			elif ctrl == self.ALU_CTRL_INPUT2:
				result = input2

			return result

		def Add(self, input1, input2):
			return self.alu(input1, input2, 0, 0, self.ALU_CTRL_ADD_SUB)

		def Sub(self, input1, input2):
			return self.alu(input1, input2, 1, 0, self.ALU_CTRL_ADD_SUB)

		def And(self, input1, input2):
			return self.alu(input1, input2, 0, 0, self.ALU_CTRL_AND)

		def Xor(self, input1, input2):
			return self.alu(input1, input2, 0, 0, self.ALU_CTRL_XOR)

		def Shiftl(self, input1, input2):
			return self.alu(input1, input2, 0, 0, self.ALU_CTRL_SHIFT)
	
		def Shiftr(self, input1, input2):
			return self.alu(input1, input2, 0, 1, self.ALU_CTRL_SHIFT)
		
		def Input2(self, input1, input2):
			return self.alu(input1, input2, 0, 0, self.ALU_CTRL_INPUT2)
	
	class Registers:
		REGISTERS_NUM = 16
		def __init__(self):
			self.image = [0 for i in range(self.REGISTERS_NUM)]

		def read(self, a_addr, b_addr):
			return self.image[a_addr], self.image[b_addr]

		def write(self, w_data, w_addr):
			self.image[w_addr] = w_data

	class Memory:
		MEMORY_SIZE = 255
		def __init__(self):
			self.image = [0 for i in range(self.MEMORY_SIZE)]

		def read(self, addr):
			return self.image[addr]

		def write(self, addr, v):
			print("memory addr " + hex(addr) + " write " + hex(v))
			self.image[addr] = v
				
	class IO:
		IO_ADDRESS = 255
		def read(self):
			v = int(input("Enter a value > "))
			if v > 0x7FFF:
				v = 0x7FFF
			if v < 0x8000 * (-1):
				v = 0x8000 * (-1)
			if v < 0:
				v = 0x10000 - (v * (-1))
			print("IO read ", hex(v))
			return v

		def write(self, v):
			print("IO write ", hex(v))
			if v >= 0x8000:
				v =  v - 0x10000
			print("Output > ", v)

	def read(self, addr):
		if 0 <= addr < self.memory.MEMORY_SIZE:
			return self.memory.read(addr)
		elif addr == self.io.IO_ADDRESS:
			return self.io.read()
		self.halt()

	def write(self, addr, val):
		if 0 <= addr < self.memory.MEMORY_SIZE:
			self.memory.write(addr, val)
		elif addr == self.io.IO_ADDRESS:
			self.io.write(val)
		else:
			self.halt()

	def load_app(self, filename):
		with open(filename, 'rb') as file:
			file_contents = file.read()
			file_length = len(file_contents) // 2
			for addr in range(file_length):
				self.memory.write(self.pc + addr, (int(file_contents[addr * 2]) << 8) | int(file_contents[(addr * 2) + 1]))
		
	def instruction_fetch(self, pc):
		if pc < self.memory.MEMORY_SIZE:
			opcode = self.memory.read(pc)
			op   = (opcode & 0xF000) >> 12
			d    = (opcode & 0x0F00) >> 8
			s    = (opcode & 0x00F0) >> 4
			t    = (opcode & 0x000F)
			addr = (opcode & 0x00FF)
			return op, d, s, t, addr
		else:
			return 0, 0, 0, 0, 0

	def start(self):
		def op_halt(self, d, s, t, addr):
			self.halt()
			return 0

		def op_add(self, d, s, t, addr):
			a_data, b_data = self.registers.read(s, t)
			alu_output = self.alu.Add(a_data, b_data)
			self.registers.write(alu_output, d)
			return self.pc + 1

		def op_sub(self, d, s, t, addr):
			a_data, b_data = self.registers.read(s, t)
			alu_output = self.alu.Sub(a_data, b_data)
			self.registers.write(alu_output, d)
			return self.pc + 1
			
		def op_and(self, d, s, t, addr):
			a_data, b_data = self.registers.read(s, t)
			alu_output = self.alu.And(a_data, b_data)
			self.registers.write(alu_output, d)
			return self.pc + 1
			
		def op_xor(self, d, s, t, addr):
			a_data, b_data = self.registers.read(s, t)
			alu_output = self.alu.Xor(a_data, b_data)
			self.registers.write(alu_output, d)
			return self.pc + 1
			
		def op_shl(self, d, s, t, addr):
			a_data, b_data = self.registers.read(s, t)
			alu_output = self.alu.Shiftl(a_data, b_data)
			self.registers.write(alu_output, d)
			return self.pc + 1
			
		def op_shr(self, d, s, t, addr):
			a_data, b_data = self.registers.read(s, t)
			alu_output = self.alu.Shiftr(a_data, b_data)
			self.registers.write(alu_output, d)
			return self.pc + 1
			
		def op_loada(self, d, s, t, addr):
			self.registers.write(addr, d)
			return self.pc + 1
			
		def op_load(self, d, s, t, addr):
			self.registers.write(self.read(addr), d)
			return self.pc + 1
			
		def op_stor(self, d, s, t, addr):
			a_data, b_data = self.registers.read(d, 0)
			self.write(addr, a_data)
			return self.pc + 1
			
		def op_loadi(self, d, s, t, addr):
			a_data, b_data = self.registers.read(t, 0)
			self.registers.write(a_data, d)
			return self.pc + 1
			
		def op_stori(self, d, s, t, addr):
			a_data, b_data = self.registers.read(t, d)
			self.write(self.registers.read(a_data, b_data))
			return self.pc + 1
			
		def op_bzero(self, d, s, t, addr):
			a_data, b_data = self.registers.read(d, 0)
			if a_data == 0:
				return addr
			else:
				return self.pc
			
		def op_bposi(self, d, s, t, addr):
			a_data, b_data = self.registers.read(d, 0)
			if a_data > 0:
				return addr
			else:
				return self.pc
			
		def op_jmpr(self, d, s, t, addr):
			data1, data2 = self.registers.read(t, 0)
			return data1
			
		def op_jmpl(self, d, s, t, addr):
			self.registers.write(self.pc, d)
			return addr
		
		instruction_exec_map = {
			0x0: op_halt,
			0x1: op_add,
			0x2: op_sub,
			0x3: op_and,
			0x4: op_xor,
			0x5: op_shl,
			0x6: op_shr,
			0x7: op_loada,
			0x8: op_load,
			0x9: op_stor,
			0xA: op_loadi,
			0xB: op_stori,
			0xC: op_bzero,
			0xD: op_bposi,
			0xE: op_jmpr,
			0xF: op_jmpl
		}

		while self.pc < self.memory.MEMORY_SIZE:
			op, d, s, t, addr = self.instruction_fetch(self.pc)

			print("op " + hex(op) + ", d " + hex(d) + ", s " + hex(s) + ", t " + hex(t) + ", addr " + hex(addr))

			self.pc = instruction_exec_map[op](self, d, s, t, addr)

	def halt(self):
		print('HALT')
		exit()

computer = Computer()
# test add
# computer.memory.write(0x10, 0x81FF)
# computer.memory.write(0x11, 0x82FF)
# computer.memory.write(0x12, 0x1312)
# computer.memory.write(0x13, 0x93FF)

# # test sub
# computer.memory.write(0x14, 0x81FF)
# computer.memory.write(0x15, 0x82FF)
# computer.memory.write(0x16, 0x2312)
# computer.memory.write(0x17, 0x93FF)
# computer.start()
#computer.write(255, 123)

for a in sys.argv[1:]:
	computer.load_app(a)

computer.start()
