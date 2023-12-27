import sys
from array import array
assert sys.version_info >= (3, 10)

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
			return (s, c1 | c2)

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
			if 0 < v2 < 16:		 # 16 bits
				return v1 << v2
			return v1
	
		def Shiftr(self, v1, v2):
			if 0 < v2 < 16:		 # 16 bits
				return v1 >> v2
			return v1
	
	class Registers:
		REGISTERS_NUM = 16
		def __init__(self):
			self.image = [0 for i in range(self.REGISTERS_NUM)]   # 16 16-bit cells

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
			self.image = [0 for i in range(self.MEMORY_SIZE)]   # 255 16-bit cells

		def read(self, addr):
			return self.image[addr]

		def write(self, addr, v):
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

	class Operations:
		OP_HALT		= 0x0
		OP_ADD		= 0x1
		OP_SUB		= 0x2
		OP_AND		= 0x3
		OP_XOR		= 0x4
		OP_SHL		= 0x5
		OP_SHR		= 0x6
		OP_LOADA	= 0x7
		OP_LOAD		= 0x8
		OP_STOR		= 0x9
		OP_LOADI	= 0xA
		OP_STORI	= 0xB
		OP_BZERO	= 0xC
		OP_BPOSI	= 0xD
		OP_JMPR		= 0xE
		OP_JMPL		= 0xF

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
			for addr in range(len(file_contents)):
				self.memory.write(addr, file_contents[addr])
		
	def instruction_fetch(self, pc):
		if pc < self.memory.MEMORY_SIZE:
			opcode = self.memory.read(pc)
			op   = (opcode & 0xF000) >> 12
			d    = (opcode & 0x0F00) >> 8
			s    = (opcode & 0x00F0) >> 4
			t    = (opcode & 0x000F)
			addr = (opcode & 0x00FF)
			return op, d, s, t, addr
		self.halt()

	def start(self):
		pc = 0x10
		while pc < self.memory.MEMORY_SIZE:
			op, d, s, t, addr = self.instruction_fetch(pc)

			print("op " + hex(op) + ", d " + hex(d) + ", s " + hex(s) + ", t " + hex(t) + ", addr " + hex(addr))

			pc_t = pc
			pc_t += 1

			match op:
				case self.Operations.OP_HALT:
					self.halt()

				case self.Operations.OP_ADD:
					self.registers.write(d, self.alu.Add( self.registers.read(s), self.registers.read(t)) )

				case self.Operations.OP_SUB:
					self.registers.write(d, self.alu.Sub(self.registers.read(s), self.registers.read(t)))
					
				case self.Operations.OP_AND:
					self.registers.write(d, self.alu.And(self.registers.read(s), self.registers.read(t)))
					
				case self.Operations.OP_XOR:
					self.registers.write(d, self.alu.Xor(self.registers.read(s), self.registers.read(t)))
					
				case self.Operations.OP_SHL:
					self.registers.write(d, self.alu.Shiftl(self.registers.read(s), self.registers.read(t)))
					
				case self.Operations.OP_SHR:
					self.registers.write(d, self.alu.Shiftr(self.registers.read(s), self.registers.read(t)))
					
				case self.Operations.OP_LOADA:
					self.registers.write(d, addr)
					
				case self.Operations.OP_LOAD:
					self.registers.write(d, self.read(addr))
					
				case self.Operations.OP_STOR:
					self.write(addr, self.registers.read(d))
					
				case self.Operations.OP_LOADI:
					self.registers.write(d, self.read(self.registers.read(t)))
					
				case self.Operations.OP_STORI:
					self.write(self.registers.read(t), self.registers.read(d))
					
				case self.Operations.OP_BZERO:
					if self.registers.read(d) == 0:
						pc_t = addr
					
				case self.Operations.OP_BPOSI:
					if self.registers.read(d) > 0:
						pc_t = addr
					
				case self.Operations.OP_JMPR:
					pc_t = self.registers.read(t)
					
				case self.Operations.OP_JMPL:
					self.registers.write(d, pc_t)
					pc_t = addr
					
			pc = pc_t

	def halt(self):
		print('HALT')
		exit()

computer = Computer()
# test add
computer.memory.write(0x10, 0x81FF)
computer.memory.write(0x11, 0x82FF)
computer.memory.write(0x12, 0x1312)
computer.memory.write(0x13, 0x93FF)

# test sub
computer.memory.write(0x14, 0x81FF)
computer.memory.write(0x15, 0x82FF)
computer.memory.write(0x16, 0x2312)
computer.memory.write(0x17, 0x93FF)
computer.start()
#computer.write(255, 123)
