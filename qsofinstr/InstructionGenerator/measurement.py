'''
The format of the instruction for measurement is as follows:
    |64|63|62|61|---A---|..............................|
    1. bit 64 is used to indicate whether the current instruction is the last instruction in the timeslice
    2. bit |63|63|62| is the quantum operation operand for the measurement, which should be 101
    3. A represents which qubit is under the measurement, which needs ceil(log2(N)) bits
    There's an optimization for adding the instruction of measurement, which is mainly to try to put all the measurement operations into the same instruction
    There are two cases for measurement: 1. measurement that will be used by classical conditional quantum operation 2. measurement at the end
    Since after the measurement, the quantum state will be collapsed into classical state, there's no following quantum operation after the measurement,
    then the measurement that is not used by classical conditional quantum operations can be put into any timeslice after the last quantum operation on this qubit.
    Therefore the basic procedure is following:
    1. if the current quantum operation is measurement, encode the corresponding qubit into an instruction without adding into the timeslice_instruction_node
    2. there should be a dictionary to indicate which qubit has already been measured and the maximum timeslice of the existing measurements should also be recorded.
    3. if the current operation is classical conditioned, then the timeslice of current instruction would be the maximum timeslice of the existing measurements plus 1
       and the measurement instruction would be put into the maximum timeslice of the existing measurements. 
    4. if the current timeslice is the last one, and it's also the end of timeslice, then the measurement instruction would be put into current timeslice.

This file contains the class to represent the temporary measurement instruction,
which is used to store the measurement instruction before the classical conditioned
quantum operation as well as the last timeslice.
'''
class Measurement:
    def __init__(self, N_instr_bits, N_qubit_bits, operand, operand_length, timeslice_length):
        self.instruction_temp = [[]]
        self.N_instr_bits = N_instr_bits # The number of bits to represent the instruction
        self.N_qubit_bits = N_qubit_bits # The number of bits to represent the qubit
        self.operand = operand # The operand of the measurement
        self.operand_length = operand_length # The length of the measurement operand
        self.timeslice_length = timeslice_length # The length of bits to represent the timeslice, which is 1 in current instruction format
        self.new_instruction_need = True # The flag to indicate if the new instruction is needed
        self.bit_position = N_instr_bits 
        self.measured_qubits = {}
        self.max_measured_timeslice = 0
        self.instruction_idx = 0 # The index of the instructions that should be added into the timeslice_instruction_node later
        # self.qubits_additional_timeslice = {} # The dictionary to store the values that should be added on the timeslice of each qubit
        
    def set_measured_qubit(self, qubit, timeslice):
        self.measured_qubits[qubit] = timeslice
        self.max_measured_timeslice = max(self.max_measured_timeslice, timeslice)
    
    # This function is used to check whether the last measurement instruction has already been added into the timeslice_instruction_node
    def check_last_instruction_added(self):
        if len(self.instruction_temp[-1]) == 0:
            return True
        else:
            return False
    
    # This function is used to get the last measurement instruction
    def get_instruction(self):
        # Set the new instruction flag to True
        self.new_instruction_need = True
        # Add a new list to store the new instruction
        self.instruction_temp.append([])
        return self.instruction_temp[len(self.instruction_temp)-2]
           
    # This function is used to set the remaining bits of current temporary measurement instruction to 1 and add a new instruction list
    # This function is called for the classical conditioned quantum operation
    def set_remaining_bits(self):
        self.instruction_temp[-1][-1] += (1 << self.bit_position) - 1
    
    def add_instruction(self, qubit):
        instruction = 0
        if self.new_instruction_need:
            # Flip the flag
            self.new_instruction_need = False
            # Set the bit position
            self.bit_position = self.N_instr_bits-self.timeslice_length-self.operand_length
            # Add the instruction
            self.instruction_temp[-1].append(self.operand << (self.N_instr_bits-self.timeslice_length-self.operand_length))
        # Add the qubit
        self.bit_position -= self.N_qubit_bits
        instruction += qubit << self.bit_position
        # Check whether the are enough remaining bits to add a new qubit
        if self.bit_position < self.N_qubit_bits:
            # Set the remaining bits to 1
            instruction += (1 << self.bit_position) - 1
            # Set the new instruction flag to True
            self.new_instruction_need = True
        # Update the instruction
        self.instruction_temp[-1][-1] += instruction
        