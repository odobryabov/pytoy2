import sys

class Toy:
	SOFT_START_ADDRESS = 0x10

	def __init__(self):
		self.registers = self.Registers()
		self.memory = self.Memory()
		self.alu = self.ALU()
		self.pc = self.SOFT_START_ADDRESS
		
	class ALU:
		__DATA_RESOLUTION = 16
		__CTRL_ADD_SUB	= 0b000
		__CTRL_AND		= 0b001
		__CTRL_XOR		= 0b010
		__CTRL_SHIFT	= 0b011
		__CTRL_INPUT2	= 0b100

		__SUBSTRACT_RESET = 0b0
		__SUBSTRACT_SET   = 0b1

		__SHIFT_RIGHT = 0b0
		__SHIFT_LEFT  = 0b1
	
		def __full_adder(self, a, b, carry_in):
			half_adder = lambda a, b: (a ^ b, a & b)
			s1, c1 = half_adder(a, b)
			sum, c2 = half_adder(carry_in, s1)
			return sum, c1 | c2
	
		def __adder_substractor(self, a, b, cr, sub):
			return self.__full_adder(a, b ^ sub, cr)
		
		def __alu(self, input1, input2, substract, shift_dir, ctrl):
			result_byte = 0
			if ctrl == self.__CTRL_ADD_SUB:
				carry = substract
				bit_from_byte = lambda byte, position: (byte & (1 << position)) >> position
				for position in range(self.__DATA_RESOLUTION):
					bit1 = bit_from_byte(input1, position)
					bit2 = bit_from_byte(input2, position)
					result_bit, carry = self.__adder_substractor(bit1, bit2, carry, substract)
					result_byte |= (result_bit << position)
			elif ctrl == self.__CTRL_AND:
				result_byte = input1 & input2
			elif ctrl == self.__CTRL_XOR:
				result_byte = input1 ^ input2
			elif ctrl == self.__CTRL_SHIFT:
				if shift_dir == self.__SHIFT_LEFT:
					result_byte = input1 << (input2 & 0b1111) # 16 steps max, only 4 bits in use
				else:
					result_byte = input1 >> (input2 & 0b1111) # 16 steps max, only 4 bits in use
			elif ctrl == self.__CTRL_INPUT2:
				result_byte = input2
	
			return result_byte
	
		def Add(self, input1, input2):
			return self.__alu(input1, input2, self.__SUBSTRACT_RESET, self.__SHIFT_RIGHT, self.__CTRL_ADD_SUB)
	
		def Sub(self, input1, input2):
			return self.__alu(input1, input2, self.__SUBSTRACT_SET,   self.__SHIFT_RIGHT, self.__CTRL_ADD_SUB)
	
		def And(self, input1, input2):
			return self.__alu(input1, input2, self.__SUBSTRACT_RESET, self.__SHIFT_RIGHT, self.__CTRL_AND)
	
		def Xor(self, input1, input2):
			return self.__alu(input1, input2, self.__SUBSTRACT_RESET, self.__SHIFT_RIGHT, self.__CTRL_XOR)
	
		def Shiftl(self, input1, input2):
			return self.__alu(input1, input2, self.__SUBSTRACT_RESET, self.__SHIFT_LEFT,  self.__CTRL_SHIFT)
	
		def Shiftr(self, input1, input2):
			return self.__alu(input1, input2, self.__SUBSTRACT_RESET, self.__SHIFT_RIGHT, self.__CTRL_SHIFT)
		
		def Input2(self, input1, input2):
			return self.__alu(input1, input2, self.__SUBSTRACT_RESET, self.__SHIFT_RIGHT, self.__CTRL_INPUT2)
	
	class Registers:
		def __init__(self):
			REGISTERS_NUM = 16
			self.image = [0 for i in range(REGISTERS_NUM)]

		def read(self, a_addr, b_addr):
			return self.image[a_addr], self.image[b_addr]

		def write(self, w_data, w_addr):
			if w_addr != 0:
				self.image[w_addr] = w_data

	class Memory:
		MEMORY_MAP_SIZE = 256
		__MEMORY_SIZE = 255
		__IO_ADDRESS = 255

		def __init__(self):
			self.image = [0 for i in range(self.__MEMORY_SIZE)]

		def read(self, addr):
			if 0 <= addr < self.__MEMORY_SIZE:
				return self.image[addr]
			elif addr == self.__IO_ADDRESS:
				data = int(input("Enter a value > "))
				if data < 0:
					data = 0x10000 + data	# two's-complement
				return data
			else:
				self.halt()

		def write(self, addr, w_data):
			if 0 <= addr < self.__MEMORY_SIZE:
				self.image[addr] = w_data
			elif addr == self.__IO_ADDRESS:
				if w_data > 0x7FFF:
					w_data =  w_data - 0x10000	# two's-complement
				print("Output > ", w_data)
			else:
				self.halt()

	def load_app(self, filename):
		with open(filename, 'rb') as file:
			file_contents = file.read()
			file_length = len(file_contents) // 2
			for addr in range(file_length):
				# change DE to LE
				self.memory.write(self.SOFT_START_ADDRESS + addr, 
					  (int(file_contents[addr * 2]) << 8) | 
					  int(file_contents[(addr * 2) + 1]))
		
	def fetch(self):
		instruction = self.memory.read(self.pc)
		opcode	= (instruction & 0xF000) >> 12
		d    	= (instruction & 0x0F00) >> 8
		s    	= (instruction & 0x00F0) >> 4
		t    	= (instruction & 0x000F)
		addr 	= (instruction & 0x00FF)
		self.pc = self.pc + 1
		return opcode, d, s, t, addr

	def start(self):
		def op_halt(self, d, s, t, addr):
			self.halt()
			return 0

		def op_add(self, d, s, t, addr): # R[d] = R[s] + R[t]
			a_data, b_data = self.registers.read(s, t)
			w_data = self.alu.Add(a_data, b_data)
			self.registers.write(w_data, d)

		def op_sub(self, d, s, t, addr): # R[d] = R[s] - R[t]
			a_data, b_data = self.registers.read(s, t)
			w_data = self.alu.Sub(a_data, b_data)
			self.registers.write(w_data, d)
			
		def op_and(self, d, s, t, addr): # R[d] = R[s] & R[t]
			a_data, b_data = self.registers.read(s, t)
			w_data = self.alu.And(a_data, b_data)
			self.registers.write(w_data, d)
			
		def op_xor(self, d, s, t, addr): # R[d] = R[s] ^ R[t]
			a_data, b_data = self.registers.read(s, t)
			w_data = self.alu.Xor(a_data, b_data)
			self.registers.write(w_data, d)
			
		def op_shl(self, d, s, t, addr): # R[d] = R[s] << R[t]
			a_data, b_data = self.registers.read(s, t)
			w_data = self.alu.Shiftl(a_data, b_data)
			self.registers.write(w_data, d)
			
		def op_shr(self, d, s, t, addr): # R[d] = R[s] >> R[t]
			a_data, b_data = self.registers.read(s, t)
			w_data = self.alu.Shiftr(a_data, b_data)
			self.registers.write(w_data, d)
			
		def op_loada(self, d, s, t, addr): # R[d] = addr
			self.registers.write(addr, d)
			
		def op_load(self, d, s, t, addr): # R[d] = M[addr]
			r_data = self.memory.read(addr)
			self.registers.write(r_data, d)
			
		def op_stor(self, d, s, t, addr): # M[addr] = R[d]
			a_data, b_data = self.registers.read(d, 0)
			self.memory.write(addr, a_data)
			
		def op_loadi(self, d, s, t, addr): # R[d] = M[R[t]]
			a_data, b_data = self.registers.read(t, 0)
			r_data = self.memory.read(a_data)
			self.registers.write(r_data, d)
			
		def op_stori(self, d, s, t, addr): # M[R[t]] = R[d]
			a_data, b_data = self.registers.read(t, d)
			self.memory.write(self.registers.read(a_data, b_data))
			
		def op_bzero(self, d, s, t, addr): # if (R[d] == 0) PC = addr
			a_data, b_data = self.registers.read(d, 0)
			if a_data == 0:
				self.pc = addr
			
		def op_bposi(self, d, s, t, addr): # if (R[d] > 0) PC = addr
			a_data, b_data = self.registers.read(d, 0)
			if a_data > 0:
				self.pc = addr
			
		def op_jmpr(self, d, s, t, addr): # PC = R[d]
			data1, data2 = self.registers.read(d, 0)
			self.pc = data1
			
		def op_jmpl(self, d, s, t, addr): # R[d] = PC; PC = addr
			self.registers.write(self.pc, d)
			self.pc = addr
		
		execute = {
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

		while True:
			op, d, s, t, addr = self.fetch()
			# print("op ", hex(op), ", d ", hex(d), ", s ", hex(s), ", t ", hex(t), ", addr ", hex(addr))
			execute[op](self, d, s, t, addr)

	def halt(self):
		print('HALT')
		exit()

if __name__ == "__main__":
	computer = Toy()

	for a in sys.argv[1:]:
		computer.load_app(a)

	computer.start()
