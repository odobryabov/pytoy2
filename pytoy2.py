import sys

class Computer:
	def __init__(self):
		self.registers = self.Registers()
		self.memory = self.Memory()
		self.alu = self.ALU()
		self.io = self.IO() # input output device
		self.pc = 0x10  # program counter
		
	class ALU:
		RESOLUTION = 16

		half_adder = lambda self, a, b: (a ^ b, a & b)
		
		def full_adder(self, a, b, cr): 
			s1, c1 = self.half_adder(a, b)
			s, c2 = self.half_adder(cr, s1)
			return s, c1 | c2

		def adder_substractor(self, a, b, cr, sub):
			return self.full_adder(a, b ^ sub, cr)

		def Add(self, v1, v2):
			result = 0
			carry = 0
			for x in range(self.RESOLUTION):
				b1 = (v1 & (1 << x)) >> x
				b2 = (v2 & (1 << x)) >> x
				r, carry = self.adder_substractor(b1, b2, carry, 0)
				result = result | (r << x)
			return result

		def Sub(self, v1, v2):
			result = 0
			carry = 1
			for x in range(self.RESOLUTION):
				b1 = (v1 & (1 << x)) >> x
				b2 = (v2 & (1 << x)) >> x
				r, carry = self.adder_substractor(b1, b2, carry, 1)
				result = result | (r << x)
			return result

		def And(self, v1, v2):
			return v1 & v2

		def Xor(self, v1, v2):
			return v1 ^ v2

		def Shiftl(self, v1, v2):
			return v1 << (v2 % self.RESOLUTION)
	
		def Shiftr(self, v1, v2):
			return v1 >> (v2 % self.RESOLUTION)
	
	class Registers:
		REGISTERS_NUM = 16
		def __init__(self):
			self.image = [0 for i in range(self.REGISTERS_NUM)]

		def read(self, addr):
			if 0 <= addr <= self.REGISTERS_NUM:
				return self.image[addr]
			return 0

		def write(self, addr, v):
			if 1 <= addr <= self.REGISTERS_NUM:  # first register is read-only
				self.image[addr] = v
			return 0

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
				self.memory.write(self.pc + addr, int(file_contents[addr * 2]) << 8 | int(file_contents[(addr * 2) + 1]))
		
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
			self.registers.write(d, self.alu.Add( self.registers.read(s), self.registers.read(t)))
			return self.pc + 1

		def op_sub(self, d, s, t, addr):
			self.registers.write(d, self.alu.Sub(self.registers.read(s), self.registers.read(t)))
			return self.pc + 1
			
		def op_and(self, d, s, t, addr):
			self.registers.write(d, self.alu.And(self.registers.read(s), self.registers.read(t)))
			return self.pc + 1
			
		def op_xor(self, d, s, t, addr):
			self.registers.write(d, self.alu.Xor(self.registers.read(s), self.registers.read(t)))
			return self.pc + 1
			
		def op_shl(self, d, s, t, addr):
			self.registers.write(d, self.alu.Shiftl(self.registers.read(s), self.registers.read(t)))
			return self.pc + 1
			
		def op_shr(self, d, s, t, addr):
			self.registers.write(d, self.alu.Shiftr(self.registers.read(s), self.registers.read(t)))
			return self.pc + 1
			
		def op_loada(self, d, s, t, addr):
			self.registers.write(d, addr)
			return self.pc + 1
			
		def op_load(self, d, s, t, addr):
			self.registers.write(d, self.read(addr))
			return self.pc + 1
			
		def op_stor(self, d, s, t, addr):
			self.write(addr, self.registers.read(d))
			return self.pc + 1
			
		def op_loadi(self, d, s, t, addr):
			self.registers.write(d, self.read(self.registers.read(t)))
			return self.pc + 1
			
		def op_stori(self, d, s, t, addr):
			self.write(self.registers.read(t), self.registers.read(d))
			return self.pc + 1
			
		def op_bzero(self, d, s, t, addr):
			if self.registers.read(d) == 0:
				return addr
			else:
				return self.pc
			
		def op_bposi(self, d, s, t, addr):
			if self.registers.read(d) > 0:
				return addr
			else:
				return self.pc
			
		def op_jmpr(self, d, s, t, addr):
			return self.registers.read(t)
			
		def op_jmpl(self, d, s, t, addr):
			self.registers.write(d, self.pc)
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
