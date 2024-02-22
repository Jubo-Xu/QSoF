import math
# Define the class representing the instruction at each timeslice
class timeslice_instruction_node:
    def __init__(self, N_instr_bits):
        self.instructions = {
            "single_gate_no_condition": [],
            "single_gate_condition": [],
            "control_gate_no_condition": [],
            "control_gate_condition": [],
            "decoherence": [],
            "measurement": [],
            "reset": []
        } # For now the instruction for special algorithms are not added
        # The following dictionary is used to indicate whether a new instruction of a certain type is needed
        self.new_instruction_need = {
            "single_gate_no_condition": True,
            "single_gate_condition": True,
            "control_gate_no_condition": True,
            "control_gate_condition": True,
            "decoherence": True,
            "measurement": True,
            "reset": True
        }
        # The following dictionary is used to indicate the index of the instruction that can be modified
        # not using the last index of the list to avoid the case where the parameter is following
        self.instruction_index = {
            "single_gate_no_condition": -1,
            "single_gate_condition": -1,
            "control_gate_no_condition": -1,
            "control_gate_condition": -1,
            "decoherence": -1,
            "measurement": -1,
            "reset": -1
        }
        # The following dictionary is used to indicate the bit position of the current instruction
        self.bit_position = {
            "single_gate_no_condition": N_instr_bits,
            "single_gate_condition": N_instr_bits,
            "control_gate_no_condition": N_instr_bits,
            "control_gate_condition": N_instr_bits,
            "decoherence": N_instr_bits,
            "measurement": N_instr_bits,
            "reset": N_instr_bits
        }

class Instructions:
    # The integer bits and floating bits of parameters, which can be changed through command line
    Bits_Int = 2
    Bits_Float = 30
    N_instr_bits = 64
    def __init__(self, N_qubits):
        self.N_qubit_bits = max(1, math.ceil(math.log2(N_qubits))) # The number of bits needed to represent the number of qubits
        # The dictionary of the instructions for all the timeslices
        self.instructions = {}
        # The quantum operation operands table
        self.quantum_operation_operands = {
            "single_gate_no_condition": 0,
            "single_gate_condition": 2,
            "control_gate_no_condition": 1,
            "control_gate_condition": 3,
            "decoherence": 4,
            "measurement": 5,
            "reset": 6
        }
        # The table of the single qubit gates
        self.single_qubit_gates = {
            "u": 0,
            "x": 1,
            "y": 2,
            "z": 3,
            "h": 4,
            "s": 5,
            "t": 6,
            "rx": 7,
            "ry": 8,
            "rz": 9,
            "rtheta": 10
        }
        self.operand_length = 3 # The number of bits for each operand
        self.gate_length = 4 # The number of bits needed to represent the gate
    
    @staticmethod
    def float_to_fixed_point(value, bits_float):
        # The integer part of the value
        value_int = int(value)
        # The floating part of the value
        value_float = int((value - value_int) * (2**bits_float))
        return (value_int << bits_float) + value_float
    
    @staticmethod
    def GetBinary(val_bv, bv_size):
        if val_bv < 0:
            val_bv_new = abs(val_bv)
            length_bv = len(bin(val_bv_new))-2
            val_bv_new = (val_bv_new ^ ((1 << len(bin(val_bv_new)[2:])) - 1)) + 1
            val_bv_bin = "0"*(length_bv-len(bin(val_bv_new)[2:]))+bin(val_bv_new)[2:]
        else:
            val_bv_bin = bin(val_bv)[2:]
        size_zero = (bv_size - len(val_bv_bin)) if len(val_bv_bin) < bv_size else 0
        if size_zero > 0:
            val_bv_bin = "1"+"1"*(size_zero-1)+val_bv_bin if val_bv < 0 else ("0"+"0"*(size_zero-1)+val_bv_bin if val_bv > 0 else "0")
        return val_bv_bin
    
    def add_instruction_single_gate_no_condition(self, timeslice, gate, qubit, end_of_timeslice = False, parameter = None):
        if end_of_timeslice and (qubit is None) and (gate is None):
            self.instructions[timeslice].instructions["single_gate_no_condition"][self.instructions[timeslice].instruction_index["single_gate_no_condition"]] += (1 << self.instructions[timeslice].bit_position["single_gate_no_condition"]) - 1
            self.instructions[timeslice].instructions["single_gate_no_condition"][self.instructions[timeslice].instruction_index["single_gate_no_condition"]] += (1 << (self.N_instr_bits-1))
            self.instructions[timeslice].new_instruction_need["single_gate_no_condition"] = True
            return
        instruction = 0
        # Check whether a new instruction should be generated for the current timeslice
        if self.instructions[timeslice].new_instruction_need["single_gate_no_condition"]:
            self.instructions[timeslice].new_instruction_need["single_gate_no_condition"] = False
            self.instructions[timeslice].instruction_index["single_gate_no_condition"] += 1
            self.instructions[timeslice].bit_position["single_gate_no_condition"] = self.N_instr_bits-1-self.operand_length
            self.instructions[timeslice].instructions["single_gate_no_condition"].append(instruction)
        # Add the gate qubit pair to the current instruction
        # The qubit is added to the instruction
        self.instructions[timeslice].bit_position["single_gate_no_condition"] -= self.N_qubit_bits
        instruction += (qubit << self.instructions[timeslice].bit_position["single_gate_no_condition"])
        # The gate is added to the instruction
        self.instructions[timeslice].bit_position["single_gate_no_condition"] -= self.gate_length
        instruction += (self.single_qubit_gates[gate] << self.instructions[timeslice].bit_position["single_gate_no_condition"])
        # Check whether the parameters are needed
        if gate == "rtheta":
            cos_theta = Instructions.float_to_fixed_point(math.cos(parameter[0]), self.Bits_Float)
            sin_theta = Instructions.float_to_fixed_point(math.sin(parameter[0]), self.Bits_Float)
            self.instructions[timeslice].instructions["single_gate_no_condition"].append((cos_theta << (self.Bits_Int+self.Bits_Float))+sin_theta)
        elif gate == "rx" or gate == "ry" or gate == "rz":
            cos_theta = Instructions.float_to_fixed_point(math.cos(parameter[0]/2), self.Bits_Float)
            sin_theta = Instructions.float_to_fixed_point(math.sin(parameter[0]/2), self.Bits_Float)
            self.instructions[timeslice].instructions["single_gate_no_condition"].append((cos_theta << (self.Bits_Int+self.Bits_Float))+sin_theta)
        
        # Check whether the remaining bits is not enough for another qubit gate pair
        if self.instructions[timeslice].bit_position["single_gate_no_condition"] < (self.N_qubit_bits+self.gate_length):
            self.instructions[timeslice].new_instruction_need["single_gate_no_condition"] = True
            self.instructions[timeslice].bit_position["single_gate_no_condition"] = self.N_instr_bits
            # Invert the remaining bits to 1
            instruction += (1 << self.instructions[timeslice].bit_position["single_gate_no_condition"]) - 1
        # If the current gate is last operation in current timeslice, then set the most significant bit to 1 and set the remaining bits to 1
        if end_of_timeslice:
            instruction += (1 << self.instructions[timeslice].bit_position["single_gate_no_condition"]) - 1
            instruction += (1 << (self.N_instr_bits-1))
            self.instructions[timeslice].new_instruction_need["single_gate_no_condition"] = True
        # Update the instruction
        self.instructions[timeslice].instructions["single_gate_no_condition"][self.instructions[timeslice].instruction_index["single_gate_no_condition"]] += instruction

    def add_instruction_single_gate_condition(self, timeslice, gate, qubit, classical_bit, val, end_of_timeslice = False, parameter = None):
        instruction = 0
        # Check whether a new instruction should be generated for the current timeslice
        if self.instructions[timeslice].new_instruction_need["single_gate_condition"]:
            self.instructions[timeslice].new_instruction_need["single_gate_condition"] = False
            self.instructions[timeslice].instruction_index["single_gate_condition"] += 1
            self.instructions[timeslice].bit_position["single_gate_condition"] = self.N_instr_bits-1-self.operand_length
            self.instructions[timeslice].instructions["single_gate_condition"].append(instruction)
            
    def instruction_gen_timeslice(self, timeslice, qubit, timeslice_node, end_of_timeslice = False):
        # Check whether the instruction node exists for the current timeslice
        if timeslice not in self.instructions:
            self.instructions[timeslice] = timeslice_instruction_node(self.N_instr_bits)
        # Check whether the current gate operation is a single qubit gate without condition
        if (timeslice_node.gate_operation in self.single_qubit_gates) and (not timeslice_node.if_flag):
            self.add_instruction_single_gate_no_condition(timeslice, timeslice_node.gate_operation, qubit, end_of_timeslice, timeslice_node.parameters)
    
    @staticmethod
    def generate_instruction(quantumcircuit):
        # Find the number of qubits
        N_qubits = len(quantumcircuit.qubits)
        # Create the instruction object
        instruction = Instructions(N_qubits)
        # Loop through the quantum circuit to generate the instructions
        for timeslice_idx in range(1, quantumcircuit.max_time_slice+1):
            qubit_idx = 0
            for qubit in quantumcircuit.qubits:
                end_of_timeslice = True if qubit_idx == len(quantumcircuit.qubits)-1 else False
                if (f"timeslice_{timeslice_idx}" not in quantumcircuit.qubits[qubit]) and (end_of_timeslice):
                    instruction.add_instruction_single_gate_no_condition(timeslice_idx, None, None, end_of_timeslice, None)
                    continue
                if f"timeslice_{timeslice_idx}" in quantumcircuit.qubits[qubit]:
                    instruction.instruction_gen_timeslice(timeslice_idx, qubit_idx, quantumcircuit.qubits[qubit][f"timeslice_{timeslice_idx}"], end_of_timeslice)
                qubit_idx += 1
        return instruction
# a = Instructions.float_to_fixed_point(0.5, 30)
# b = Instructions.float_to_fixed_point(0.75, 30)
# print(Instructions.GetBinary((a<<32)+b, 64))