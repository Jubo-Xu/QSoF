import math
from InstructionGenerator.measurement import Measurement
# Define the class representing the instruction at each timeslice
class timeslice_instruction_node:
    def __init__(self, N_instr_bits):
        self.instructions = {
            "single_gate_no_condition": [],
            "single_gate_condition": [[], []], # The first list is for single classical bit, and the second list is for multiple classical bits
            "control_gate_no_condition": [[], []], # The first list is for single control qubit, and the second list is for multiple control qubits
            "control_gate_condition": [[], [], [], []],
            "decoherence": [],
            "measurement": [],
            "reset": []
        } # For now the instruction for special algorithms are not added
        # The following dictionary is used to indicate whether a new instruction of a certain type is needed
        self.new_instruction_need = {
            "single_gate_no_condition": True,
            "single_gate_condition": [True, True], # The first element is for single classical bit, and the second element is for multiple classical bits
            "control_gate_no_condition": [True, True], # The first element is for single control qubit, and the second element is for multiple control qubits
            "control_gate_condition": [True, True, True, True], 
            "decoherence": True, 
            "measurement": True,
            "reset": True
        }
        # The following dictionary is used to indicate the index of the instruction that can be modified
        # not using the last index of the list to avoid the case where the parameter is following
        self.instruction_index = {
            "single_gate_no_condition": -1,
            "single_gate_condition": [-1, -1], # The first element is for single classical bit, and the second element is for multiple classical bits
            "control_gate_no_condition": [-1, -1], # The first element is for single control qubit, and the second element is for multiple control qubits
            "control_gate_condition": [-1, -1, -1, -1], 
            "decoherence": [-1, -1], # The first element is for decoherence instruction, and the second is for the parameter
            "measurement": -1,
            "reset": -1
        }
        # The following dictionary is used to indicate the bit position of the current instruction
        self.bit_position = {
            "single_gate_no_condition": N_instr_bits,
            "single_gate_condition": [N_instr_bits, N_instr_bits], # The first element is for single classical bit, and the second element is for multiple classical bits
            "control_gate_no_condition": [N_instr_bits, N_instr_bits], # The first element is for single control qubit, and the second element is for multiple control qubits
            "control_gate_condition": [N_instr_bits, N_instr_bits, N_instr_bits, N_instr_bits], 
            "decoherence": [N_instr_bits, 0], # The first element is for decoherence instruction, and the second is for the parameter
            "measurement": N_instr_bits,
            "reset": N_instr_bits
        }
        # This flag is used to indicate which operation has just been added, 
        # which is for the case where there's no operation for the last qubit at the end of timeslice
        self.Operation_last = ""

class Instructions:
    # The integer bits and floating bits of parameters, which can be changed through command line
    Bits_Int = 2
    Bits_Float = 30
    N_instr_bits = 64
    def __init__(self, N_qubits):
        self.N = N_qubits # The number of qubits
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
        # The table of the controlled gates
        self.controlled_gates = {
            "cu": 0,
            "cx": 1,
            "cy": 2,
            "cz": 3,
            "ch": 4,
            "cs": 5,
            "ct": 6,
            "crx": 7,
            "cry": 8,
            "crz": 9,
            "crtheta": 10
        }
        # The table of the decoherence operations
        self.decoherence = {
            "mixamp": 0,
            "mixphase":1
        }
        self.operand_length = 3 # The number of bits for each operand
        self.gate_length = 4 # The number of bits needed to represent the gate
        self.decoherence_length = 1 # The number of bits needed to represent the decoherence
        # N_instr_bits, N_qubit_bits, operand, operand_length, timeslice_length
        self.measurement = Measurement(self.N_instr_bits, self.N_qubit_bits, self.quantum_operation_operands["measurement"], self.operand_length, 1)
        # This variable is used to indicate the last valid timeslice, this is used for adding the measurement instruction into the Instruction 
        # during the conditional operations. This variable is used because it's possible that the valid timeslices in Instructions dictionary is 
        # not continuous if the quantum circuit is under the hardware specification mode 1
        self.last_valid_timeslice = 0 
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
    
    ## Define the instruction generation function for single qubit gates without condition
    def add_instruction_single_gate_no_condition(self, timeslice, gate, qubit, end_of_timeslice = False, parameter = None):
        # Check whether the instruction should be ended
        if end_of_timeslice and (qubit is None) and (gate is None):
            if (len(self.instructions[timeslice].instructions["single_gate_no_condition"]) > 0):
                # Set the remaining bits to 1 if they haven't been inverted
                if not self.instructions[timeslice].new_instruction_need["single_gate_no_condition"]:
                    self.instructions[timeslice].instructions["single_gate_no_condition"][self.instructions[timeslice].instruction_index["single_gate_no_condition"]] += (1 << self.instructions[timeslice].bit_position["single_gate_no_condition"]) - 1
                # Set the most significant bit to 1 if the last instruction being added is single qubit gate without condition
                if self.instructions[timeslice].Operation_last == "single_gate_no_condition":
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
            # Invert the remaining bits to 1
            instruction += (1 << self.instructions[timeslice].bit_position["single_gate_no_condition"]) - 1
            self.instructions[timeslice].bit_position["single_gate_no_condition"] = self.N_instr_bits
        # If the current gate is last operation in current timeslice, then set the most significant bit to 1 and set the remaining bits to 1
        if end_of_timeslice:
            # Invert the remaining bits to 1 if they haven't been inverted
            if not self.instructions[timeslice].new_instruction_need["single_gate_no_condition"]:
                instruction += (1 << self.instructions[timeslice].bit_position["single_gate_no_condition"]) - 1
            instruction += (1 << (self.N_instr_bits-1))
            self.instructions[timeslice].new_instruction_need["single_gate_no_condition"] = True
        # Update the instruction
        self.instructions[timeslice].instructions["single_gate_no_condition"][self.instructions[timeslice].instruction_index["single_gate_no_condition"]] += instruction
        # Set the last operation to the current operation
        self.instructions[timeslice].Operation_last = "single_gate_no_condition"

    ## Define the instruction generation function for single qubit gates with condition
    
    # There are two kinds of conditions, one is like if(a == 1 or 0), where a is a single classical bit,
    # and the other is like if(a == b), where a is the multiple bits classical register and b is a value,
    # for example, creg c[4]; if(c == 3) qop;
    # Therefore there are two kinds of format for single qubit gates with condition, for the first case, the format is as follows:
    # |64|63|62|61|60|---A---|  |  |  |  |---C---|  |...........................|
    # 1. bit 64 is used to indicate whether the current instruction is the last instruction in the timeslice
    # 2. bit |63|62|61| is the quantum operation operand for the single qubit gate with condition, which should be 010
    # 3. bit 60 is used to indicate whether the condition is a single classical bit or multiple classical bits, it's 0 here
    # 4. A represents the qubit, which needs ceil(log2(N)) bits
    # 5. following A is the gate operand, which needs 4 bits
    # 6. C represents the classical bit, which needs ceil(log2(N)) bits
    # 7. following C is the value of the classical bit, which needs 1 bit
    # for the second case, the format is as follows:
    # |64|63|62|61|60|---A---|  |  |  |  |---C---|---D---|----E----|............|
    # 1. bit 64 is used to indicate whether the current instruction is the last instruction in the timeslice
    # 2. bit |63|62|61| is the quantum operation operand for the single qubit gate with condition, which should be 010
    # 3. bit 60 is used to indicate whether the condition is a single classical bit or multiple classical bits, it's 1 here
    # 4. A represents the qubit, which needs ceil(log2(N)) bits
    # 5. following A is the gate operand, which needs 4 bits
    # 6. C has ceil(log2(N)) bits, which represents the lower bound of range of the considered classical bits. For example, there's a case like:
    #    creg c[4]; creg c2[2]; if(c2 == 3) qop; In this case, the total number of classical bits is 6, but the condition is c2 == 3, which
    #    means the classical bits 4 and 5 are considered, the value of other bits are not important, so if we assume c[4] and c2[2] in together
    #    forms Creg[6], then c2 == 3 means Creg[4] == 1 and Creg[5] == 1, other bits can be either 0 or 1, in this case, C is 4
    # 7. D represents the upper bound of the range of the considered classical bits, which needs ceil(log2(N)) bits, for the above example, D is 5
    # 8. E represents the value of the classical bits, which needs N bits, for the above example, E is 110000
    def add_instruction_single_gate_condition(self, timeslice, gate, qubit, classical_bit_l, classical_bit_h, val, kind, end_of_timeslice = False, parameter = None):
        # Check whether the instruction should be ended
        if end_of_timeslice and (qubit is None) and (gate is None):
            # If instructions for both kinds exist
            if (len(self.instructions[timeslice].instructions["single_gate_condition"][0]) > 0) or (len(self.instructions[timeslice].instructions["single_gate_condition"][1]) > 0):
                # Set the parameters for the first kind
                if len(self.instructions[timeslice].instructions["single_gate_condition"][0]) > 0:
                    # Set the remaining bits to 1 for the first kind if they haven't been inverted
                    if not self.instructions[timeslice].new_instruction_need["single_gate_condition"][0]:
                        self.instructions[timeslice].instructions["single_gate_condition"][0][self.instructions[timeslice].instruction_index["single_gate_condition"][0]] += (1 << self.instructions[timeslice].bit_position["single_gate_condition"][0]) - 1
                    # Set the new instruction need of the first kind to True
                    self.instructions[timeslice].new_instruction_need["single_gate_condition"][0] = True
                # Set the parameters for the second kind
                if len(self.instructions[timeslice].instructions["single_gate_condition"][1]) > 0:
                    # Set the remaining bits to 1 for the second kind if they haven't been inverted
                    if not self.instructions[timeslice].new_instruction_need["single_gate_condition"][1]:
                        self.instructions[timeslice].instructions["single_gate_condition"][1][self.instructions[timeslice].instruction_index["single_gate_condition"][1]] += (1 << self.instructions[timeslice].bit_position["single_gate_condition"][1]) - 1
                    # Set the new instruction need of the second kind to True
                    self.instructions[timeslice].new_instruction_need["single_gate_condition"][1] = True
                # Set the most significant bit to 1 based on whether the last instruction is for the first or the second kind
                if self.instructions[timeslice].Operation_last == "single_gate_condition":
                    idx = 0 if self.instructions[timeslice].instruction_index["single_gate_condition"][0] > self.instructions[timeslice].instruction_index["single_gate_condition"][1] else 1
                    self.instructions[timeslice].instructions["single_gate_condition"][idx][self.instructions[timeslice].instruction_index["single_gate_condition"][idx]] += (1 << (self.N_instr_bits-1))
            return
        # Check whether a new instruction should be generated for the current timeslice
        if self.instructions[timeslice].new_instruction_need["single_gate_condition"][kind]:
            self.instructions[timeslice].new_instruction_need["single_gate_condition"][kind] = False
            self.instructions[timeslice].instruction_index["single_gate_condition"][kind] += 1
            self.instructions[timeslice].bit_position["single_gate_condition"][kind] = self.N_instr_bits-1-self.operand_length
            self.instructions[timeslice].instructions["single_gate_condition"][kind].append(self.quantum_operation_operands["single_gate_condition"]<<(self.N_instr_bits-1-self.operand_length))
            self.instructions[timeslice].bit_position["single_gate_condition"][kind] -= 1
            # Set the bit 60 to 1 if the kind is the second kind
            if kind == 1:
                self.instructions[timeslice].instructions["single_gate_condition"][1][self.instructions[timeslice].instruction_index["single_gate_condition"][1]] += (1 << self.instructions[timeslice].bit_position["single_gate_condition"][1])
        instruction = 0
        # Add the gate qubit pair to the current instruction
        # The qubit is added to the instruction
        self.instructions[timeslice].bit_position["single_gate_condition"][kind] -= self.N_qubit_bits
        instruction += (qubit << self.instructions[timeslice].bit_position["single_gate_condition"][kind])
        # The gate is added to the instruction
        self.instructions[timeslice].bit_position["single_gate_condition"][kind] -= self.gate_length
        instruction += (self.single_qubit_gates[gate] << self.instructions[timeslice].bit_position["single_gate_condition"][kind])
        # Add the lower bound of the classical bits to the instruction
        self.instructions[timeslice].bit_position["single_gate_condition"][kind] -= self.N_qubit_bits
        instruction += (classical_bit_l << self.instructions[timeslice].bit_position["single_gate_condition"][kind])
        # For the single classical bit condition
        if kind == 0:
            # Add the value of this classical bit to the instruction
            self.instructions[timeslice].bit_position["single_gate_condition"][kind] -= 1
            instruction += (val << self.instructions[timeslice].bit_position["single_gate_condition"][kind])
        # For the multiple classical bits condition
        else:
            # Add the upper bound of the classical bits to the instruction
            self.instructions[timeslice].bit_position["single_gate_condition"][kind] -= self.N_qubit_bits
            instruction += (classical_bit_h << self.instructions[timeslice].bit_position["single_gate_condition"][kind])
            # Add the value of the classical bits to the instruction
            self.instructions[timeslice].bit_position["single_gate_condition"][kind] -= self.N
            instruction += (val << self.instructions[timeslice].bit_position["single_gate_condition"][kind])
        # Check whether the parameters are needed
        if gate == "rtheta":
            cos_theta = Instructions.float_to_fixed_point(math.cos(parameter[0]), self.Bits_Float)
            sin_theta = Instructions.float_to_fixed_point(math.sin(parameter[0]), self.Bits_Float)
            self.instructions[timeslice].instructions["single_gate_condition"][kind].append((cos_theta << (self.Bits_Int+self.Bits_Float))+sin_theta)
        elif gate == "rx" or gate == "ry" or gate == "rz":
            cos_theta = Instructions.float_to_fixed_point(math.cos(parameter[0]/2), self.Bits_Float)
            sin_theta = Instructions.float_to_fixed_point(math.sin(parameter[0]/2), self.Bits_Float)
            self.instructions[timeslice].instructions["single_gate_condition"][kind].append((cos_theta << (self.Bits_Int+self.Bits_Float))+sin_theta)
        
        # Check whether the remaining bits is not enough for another qubit gate pair plus a classical pair
        condition_bits = (1, self.N_qubit_bits+self.N)
        if self.instructions[timeslice].bit_position["single_gate_condition"][kind] < (self.N_qubit_bits+self.gate_length+self.N_qubit_bits+condition_bits[kind]):
            self.instructions[timeslice].new_instruction_need["single_gate_condition"][kind] = True
            # Invert the remaining bits to 1
            instruction += (1 << self.instructions[timeslice].bit_position["single_gate_condition"][kind]) - 1
            self.instructions[timeslice].bit_position["single_gate_condition"][kind] = self.N_instr_bits
        # If the current gate is last operation in current timeslice, then set the most significant bit to 1 and set the remaining bits to 1
        if end_of_timeslice:
            if not self.instructions[timeslice].new_instruction_need["single_gate_condition"][kind]:
                instruction += (1 << self.instructions[timeslice].bit_position["single_gate_condition"][kind]) - 1
            instruction += (1 << (self.N_instr_bits-1))
            self.instructions[timeslice].new_instruction_need["single_gate_condition"][kind] = True
        # Update the instruction
        self.instructions[timeslice].instructions["single_gate_condition"][kind][self.instructions[timeslice].instruction_index["single_gate_condition"][kind]] += instruction
        # Set the last operation to the current operation
        self.instructions[timeslice].Operation_last = "single_gate_condition"
    
    ## Define the instruction generation function of controlled gates without condition
    
    # For control gate, the format of instruction set is as follows:
    # |64|63|62|61|60|..........................................|
    # 1. bit 64 is used to indicate whether the current instruction is the last instruction in the timeslice
    # 2. bit |63|63|62| is the quantum operation operand for the control gate without condition, which should be 001
    # 3. bit 60 is used to indicate whether there is one control qubit or multiple control qubits, if it is 0, the format is 
    #   | |0|0|1|0|---A---|---B---|a|b|c|d|.....................|
    #   A represents the control qubit, B represents the target qubit, and |a|b|c|d| is the gate operand, assuming N qubtis, both A and B need ceil(log2(N)) bits
    # if it is 1, the format is
    #   | |0|0|1|1|-----A-----|---B---|a|b|c|d|.................|
    #   A is the bitstring representing the control qubits, where 1 means the corresponding qubit is control qubit, for example, if there are 4 qubits and A
    #   is 1010, then the control qubits are qubit 1 and qubit 3. B represents the target qubit, and |a|b|c|d| is the gate operand. Therefore assuming N qubits,
    #   A needs N bits, and B needs ceil(log2(N)) bits
    def add_instruction_control_gate_no_condition(self, timeslice, gate, target_qubit, control_qubits, end_of_timeslice = False, parameter = None):
        # Check whether the instruction should be ended
        if end_of_timeslice and (target_qubit is None) and (gate is None) and (control_qubits is None):
            # If instructions for both single control qubit and multiple control qubits exist
            if (len(self.instructions[timeslice].instructions["control_gate_no_condition"][0]) > 0) or (len(self.instructions[timeslice].instructions["control_gate_no_condition"][1]) > 0):
                # Set the parameters for single control qubit
                if len(self.instructions[timeslice].instructions["control_gate_no_condition"][0]) > 0:
                    # Set the remaining bits to 1 for single control qubit if they haven't been inverted
                    if not self.instructions[timeslice].new_instruction_need["control_gate_no_condition"][0]:
                        self.instructions[timeslice].instructions["control_gate_no_condition"][0][self.instructions[timeslice].instruction_index["control_gate_no_condition"][0]] += (1 << self.instructions[timeslice].bit_position["control_gate_no_condition"][0]) - 1
                    # Set the new instruction need of both single control qubit and multiple control qubits to True
                    self.instructions[timeslice].new_instruction_need["control_gate_no_condition"][0] = True
                # Set the parameters for multiple control qubits
                if len(self.instructions[timeslice].instructions["control_gate_no_condition"][1]) > 0:
                    # Set the remaining bits to 1 for single control qubit if they haven't been inverted
                    if not self.instructions[timeslice].new_instruction_need["control_gate_no_condition"][1]:
                        self.instructions[timeslice].instructions["control_gate_no_condition"][1][self.instructions[timeslice].instruction_index["control_gate_no_condition"][1]] += (1 << self.instructions[timeslice].bit_position["control_gate_no_condition"][1]) - 1
                    # Set the new instruction need of both single control qubit and multiple control qubits to True
                    self.instructions[timeslice].new_instruction_need["control_gate_no_condition"][1] = True
                # Set the most significant bit to 1 based on whether the last instruction is for single control qubit or multiple control qubits if the last instruction being added is control gate without condition
                if self.instructions[timeslice].Operation_last == "control_gate_no_condition":
                    idx = 0 if self.instructions[timeslice].instruction_index["control_gate_no_condition"][0] > self.instructions[timeslice].instruction_index["control_gate_no_condition"][1] else 1
                    self.instructions[timeslice].instructions["control_gate_no_condition"][idx][self.instructions[timeslice].instruction_index["control_gate_no_condition"][idx]] += (1 << (self.N_instr_bits-1))
            return
        instruction = 0
        idx = 0 if len(control_qubits) == 1 else 1
        # Check whether a new instruction should be generated for the current timeslice for single control qubit or multiple control qubits
        if self.instructions[timeslice].new_instruction_need["control_gate_no_condition"][idx]:
            self.instructions[timeslice].new_instruction_need["control_gate_no_condition"][idx] = False
            self.instructions[timeslice].instruction_index["control_gate_no_condition"][idx] += 1
            self.instructions[timeslice].bit_position["control_gate_no_condition"][idx] = self.N_instr_bits-1-self.operand_length
            self.instructions[timeslice].instructions["control_gate_no_condition"][idx].append(instruction+(self.quantum_operation_operands["control_gate_no_condition"]<<(self.N_instr_bits-1-self.operand_length)))
            self.instructions[timeslice].bit_position["control_gate_no_condition"][idx] -= 1
            # Set bit 60 to 1 only for multiple control qubits
            if idx == 1:
                self.instructions[timeslice].instructions["control_gate_no_condition"][1][self.instructions[timeslice].instruction_index["control_gate_no_condition"][1]] += (1 << self.instructions[timeslice].bit_position["control_gate_no_condition"][1])
        
        # Set the control qubits and target qubits operand for both single control qubit and multiple control qubits
        if idx == 0:
            # Add the control qubit to the instruction
            self.instructions[timeslice].bit_position["control_gate_no_condition"][0] -= self.N_qubit_bits
            instruction += (control_qubits[0] << self.instructions[timeslice].bit_position["control_gate_no_condition"][0])
        else:
            # Add the bistring representing control qubits to the instruction
            for i in range(len(control_qubits)):
                instruction += (1 << (self.instructions[timeslice].bit_position["control_gate_no_condition"][1]-self.N+control_qubits[i]))
            # Set the bit position 
            self.instructions[timeslice].bit_position["control_gate_no_condition"][1] -= self.N
        # Add the target qubit to the instruction
        self.instructions[timeslice].bit_position["control_gate_no_condition"][idx] -= self.N_qubit_bits
        instruction += (target_qubit << self.instructions[timeslice].bit_position["control_gate_no_condition"][idx])
        # Add the gate to the instruction
        self.instructions[timeslice].bit_position["control_gate_no_condition"][idx] -= self.gate_length
        instruction += (self.controlled_gates[gate] << self.instructions[timeslice].bit_position["control_gate_no_condition"][idx])
        # Add the parameters to the instruction
        if gate == "crtheta":
            cos_theta = Instructions.float_to_fixed_point(math.cos(parameter[0]), self.Bits_Float)
            sin_theta = Instructions.float_to_fixed_point(math.sin(parameter[0]), self.Bits_Float)
            self.instructions[timeslice].instructions["control_gate_no_condition"][idx].append((cos_theta << (self.Bits_Int+self.Bits_Float))+sin_theta)
        elif gate == "crx" or gate == "cry" or gate == "crz":
            cos_theta = Instructions.float_to_fixed_point(math.cos(parameter[0]/2), self.Bits_Float)
            sin_theta = Instructions.float_to_fixed_point(math.sin(parameter[0]/2), self.Bits_Float)
            self.instructions[timeslice].instructions["control_gate_no_condition"][idx].append((cos_theta << (self.Bits_Int+self.Bits_Float))+sin_theta)
        # Check whether the remaining bits is not enough for another control gate
        Control_bits = [self.N_qubit_bits, self.N]
        if self.instructions[timeslice].bit_position["control_gate_no_condition"][idx] < (Control_bits[idx]+self.N_qubit_bits+self.gate_length):
            self.instructions[timeslice].new_instruction_need["control_gate_no_condition"][idx] = True
            # Invert the remaining bits to 1
            instruction += (1 << self.instructions[timeslice].bit_position["control_gate_no_condition"][idx]) - 1
            self.instructions[timeslice].bit_position["control_gate_no_condition"][idx] = self.N_instr_bits
        # Check whether the current instruction is the last instruction of the timeslice
        if end_of_timeslice:
            if not self.instructions[timeslice].new_instruction_need["control_gate_no_condition"][idx]:
                instruction += (1 << self.instructions[timeslice].bit_position["control_gate_no_condition"][idx]) - 1
            instruction += (1 << (self.N_instr_bits-1))
            self.instructions[timeslice].new_instruction_need["control_gate_no_condition"][idx] = True
        # Update the instruction
        self.instructions[timeslice].instructions["control_gate_no_condition"][idx][self.instructions[timeslice].instruction_index["control_gate_no_condition"][idx]] += instruction
        # Set the last operation to the current operation
        self.instructions[timeslice].Operation_last = "control_gate_no_condition"
    
    ## Define the instruction generation function of controlled gates with condition
    # As described in single qubit gates with condition and control gate without condition, there are two kinds of conditions and two kinds of controlled gates,
    # so there are four kinds of format needed for controlled gates with condition.
    
    # The first kind is for the controlled gate with single control qubit and single classical bit condition, the format is as follows:
    # |64|63|62|61|60|59|---A---|---B---|a|b|c|d|---C---|n|............................|
    # 1. bit 64 is used to indicate whether the current instruction is the last instruction in the timeslice
    # 2. bit |63|62|61| is the quantum operation operand for the controlled gate with condition, which should be 011
    # 3. bit 60 is used to indicate whether there are single control qubit or multiple control qubits, it's 0 here
    # 4. bit 59 is used to indicate whether the condition is a single classical bit or multiple classical bits, it's 0 here
    # 5. A represents the control qubit, which needs ceil(log2(N)) bits
    # 6. B represents the target qubit, which needs ceil(log2(N)) bits
    # 7. |a|b|c|d| is the gate operand, which needs 4 bits
    # 8. C represents the classical bit, which needs ceil(log2(N)) bits
    # 9. n represents the value of the classical bit, which needs 1 bit
    
    # The second kind is for the controlled gate with single control qubit and multiple classical bits condition, the format is as follows:
    # |64|63|62|61|60|59|---A---|---B---|a|b|c|d|---C---|---D---|----E----|............|
    # 1. bit 64 is used to indicate whether the current instruction is the last instruction in the timeslice
    # 2. bit |63|62|61| is the quantum operation operand for the controlled gate with condition, which should be 011
    # 3. bit 60 is used to indicate whether there are single control qubit or multiple control qubits, it's 0 here
    # 4. bit 59 is used to indicate whether the condition is a single classical bit or multiple classical bits, it's 1 here
    # 5. A represents the control qubit, which needs ceil(log2(N)) bits
    # 6. B represents the target qubit, which needs ceil(log2(N)) bits
    # 7. |a|b|c|d| is the gate operand, which needs 4 bits
    # 8. C has ceil(log2(N)) bits, which represents the lower bound of range of the considered classical bits
    # 9. D represents the upper bound of the range of the considered classical bits, which needs ceil(log2(N)) bits
    # 10. E represents the value of the classical bits, which needs N bits
    
    # The third kind and the fourth kind has the same format as above, except bit 60 and 59 needs to be changed correspondingly.
    def add_instruction_control_gate_condition(self, timeslice, gate, target_qubit, control_qubits, classical_bit_l, classical_bit_h, val, kind, end_of_timeslice = False, parameter = None):
        # Check whether the instruction should be ended
        if end_of_timeslice and (target_qubit is None) and (gate is None) and (control_qubits is None):
            idx_max = 0 # The index of the kind with the maximum number of instructions
            max_instr = 0
            # Check whether the instructions for all cases exist
            for i in range(len(self.instructions[timeslice].instructions["control_gate_condition"])):
                # If the instruction of ith kind exists
                if len(self.instructions[timeslice].instructions["control_gate_condition"][i]) > 0:
                    # Set the remaining bits to 1 for this kind
                    if not self.instructions[timeslice].new_instruction_need["control_gate_condition"][i]:
                        self.instructions[timeslice].instructions["control_gate_condition"][i][self.instructions[timeslice].instruction_index["control_gate_condition"][i]] += \
                            (1 << self.instructions[timeslice].bit_position["control_gate_condition"][i]) - 1
                    # Set the new instruction need of this kind to True
                    self.instructions[timeslice].new_instruction_need["control_gate_condition"][i] = True
                # Find the index of the kind with the maximum number of instructions
                if len(self.instructions[timeslice].instructions["control_gate_condition"][i]) > max_instr:
                    idx_max = i
                    max_instr = len(self.instructions[timeslice].instructions["control_gate_condition"][i])
            # Set the most significant bit to 1 based on the kind with the maximum number of instructions
            if self.instructions[timeslice].Operation_last == "control_gate_condition":
                self.instructions[timeslice].instructions["control_gate_condition"][idx_max][self.instructions[timeslice].instruction_index["control_gate_condition"][idx_max]] += (1 << (self.N_instr_bits-1))
            return
        # Find the index of the kind based on if kind and number of control qubits
        control_len = 0 if len(control_qubits) == 1 else 1
        idx = (control_len << 1) + kind
        if self.instructions[timeslice].new_instruction_need["control_gate_condition"][idx]:
            self.instructions[timeslice].new_instruction_need["control_gate_condition"][idx] = False
            self.instructions[timeslice].instruction_index["control_gate_condition"][idx] += 1
            self.instructions[timeslice].bit_position["control_gate_condition"][idx] = self.N_instr_bits-1-self.operand_length
            self.instructions[timeslice].instructions["control_gate_condition"][idx].append(self.quantum_operation_operands["control_gate_condition"]<<(self.N_instr_bits-1-self.operand_length))
            self.instructions[timeslice].bit_position["control_gate_condition"][idx] -= 1
            # Set bit 60 to 1 only for multiple control qubits
            if idx > 1:
                self.instructions[timeslice].instructions["control_gate_condition"][idx][self.instructions[timeslice].instruction_index["control_gate_condition"][idx]] += (1 << self.instructions[timeslice].bit_position["control_gate_condition"][idx])
            # Set bit 59 to 1 only for multiple classical bits
            self.instructions[timeslice].bit_position["control_gate_condition"][idx] -= 1
            if kind == 1:
                self.instructions[timeslice].instructions["control_gate_condition"][idx][self.instructions[timeslice].instruction_index["control_gate_condition"][idx]] += (1 << self.instructions[timeslice].bit_position["control_gate_condition"][idx])
        
        instruction = 0
        # Set the control qubits and target qubits operand for both single control qubit and multiple control qubits
        if idx <= 1:
            # Add the control qubit to the instruction
            self.instructions[timeslice].bit_position["control_gate_condition"][idx] -= self.N_qubit_bits
            instruction += (control_qubits[0] << self.instructions[timeslice].bit_position["control_gate_condition"][idx])
        else:
            # Add the bistring representing control qubits to the instruction
            for i in range(len(control_qubits)):
                instruction += (1 << (self.instructions[timeslice].bit_position["control_gate_condition"][idx]-self.N+control_qubits[i]))
            # Set the bit position 
            self.instructions[timeslice].bit_position["control_gate_condition"][idx] -= self.N
        # Add the target qubit to the instruction
        self.instructions[timeslice].bit_position["control_gate_condition"][idx] -= self.N_qubit_bits
        instruction += (target_qubit << self.instructions[timeslice].bit_position["control_gate_condition"][idx])
        # Add the gate to the instruction
        self.instructions[timeslice].bit_position["control_gate_condition"][idx] -= self.gate_length
        instruction += (self.controlled_gates[gate] << self.instructions[timeslice].bit_position["control_gate_condition"][idx])
        # Add the lower bound of the classical bits to the instruction
        self.instructions[timeslice].bit_position["control_gate_condition"][idx] -= self.N_qubit_bits
        instruction += (classical_bit_l << self.instructions[timeslice].bit_position["control_gate_condition"][idx])
        # For the single classical bit condition
        if kind == 0:
            # Add the value of this classical bit to the instruction
            self.instructions[timeslice].bit_position["control_gate_condition"][idx] -= 1
            instruction += (val << self.instructions[timeslice].bit_position["control_gate_condition"][idx])
        # For the multiple classical bits condition
        else:
            # Add the upper bound of the classical bits to the instruction
            self.instructions[timeslice].bit_position["control_gate_condition"][idx] -= self.N_qubit_bits
            instruction += (classical_bit_h << self.instructions[timeslice].bit_position["control_gate_condition"][idx])
            # Add the value of the classical bits to the instruction
            self.instructions[timeslice].bit_position["control_gate_condition"][idx] -= self.N
            instruction += (val << self.instructions[timeslice].bit_position["control_gate_condition"][idx])
        # Add the parameters to the instruction
        if gate == "crtheta":
            cos_theta = Instructions.float_to_fixed_point(math.cos(parameter[0]), self.Bits_Float)
            sin_theta = Instructions.float_to_fixed_point(math.sin(parameter[0]), self.Bits_Float)
            self.instructions[timeslice].instructions["control_gate_condition"][idx].append((cos_theta << (self.Bits_Int+self.Bits_Float))+sin_theta)
        elif gate == "crx" or gate == "cry" or gate == "crz":
            cos_theta = Instructions.float_to_fixed_point(math.cos(parameter[0]/2), self.Bits_Float)
            sin_theta = Instructions.float_to_fixed_point(math.sin(parameter[0]/2), self.Bits_Float)
            self.instructions[timeslice].instructions["control_gate_condition"][idx].append((cos_theta << (self.Bits_Int+self.Bits_Float))+sin_theta)
        
        # Check whether the remaining bits is not enough for another control gate
        Control_condition_bits = (self.N_qubit_bits+1, self.N+1, 2*self.N_qubit_bits+self.N, 2*self.N+self.N_qubit_bits)
        if self.instructions[timeslice].bit_position["control_gate_condition"][idx] < (self.N_qubit_bits+self.gate_length+self.N_qubit_bits+Control_condition_bits[idx]):
            self.instructions[timeslice].new_instruction_need["control_gate_condition"][idx] = True
            # Invert the remaining bits to 1
            instruction += (1 << self.instructions[timeslice].bit_position["control_gate_condition"][idx]) - 1
            self.instructions[timeslice].bit_position["control_gate_condition"][idx] = self.N_instr_bits
        # Check whether the current instruction is the last instruction of the timeslice
        if end_of_timeslice:
            if not self.instructions[timeslice].new_instruction_need["control_gate_condition"][idx]:
                instruction += (1 << self.instructions[timeslice].bit_position["control_gate_condition"][idx]) - 1
            instruction += (1 << (self.N_instr_bits-1))
            self.instructions[timeslice].new_instruction_need["control_gate_condition"][idx] = True
        # Update the instruction
        self.instructions[timeslice].instructions["control_gate_condition"][idx][self.instructions[timeslice].instruction_index["control_gate_condition"][idx]] += instruction
        # Set the last operation to the current operation
        self.instructions[timeslice].Operation_last = "control_gate_condition"
    
    ## Define the instruction generation function of decoherence
    # The format of the instruction for decoherence is as follows:
    # |64|63|62|61|---A---|a|..............................|
    # 1. bit 64 is used to indicate whether the current instruction is the last instruction in the timeslice
    # 2. bit |63|63|62| is the quantum operation operand for the decoherence, which should be 100
    # 3. A represents which qubit is under the operation, which needs ceil(log2(N)) bits
    # 4. |a| is the operation operand, which needs 1 bit
    # The format of parameters for decoherence is as follows:
    # |-------------A------------|------------B------------|
    # 1. The probabilities need 32 bits to represent, therefore a 64 bits instruction can represent two probabilities
    # 2. The methodology of appending the parameters is as follows:
    #   a. The parameter is appended to the instruction in the same order as the decoherence operation, 
    #      for example, if decoherence operation is first applied on qubit 0, and then on qubit 1, then A 
    #      represents the probability of qubit 0, and B represents the probability of qubit 1
    #   b. The parameters will be appended following the decoherence instruction, for example, if there are 8 decoherences
    #      represented by one instruction, then there should be 4 64-bit parameter instructions following this decoherece instruction
    #   c. There's a case where the total number of decoherence operations is odd, then all the bits of last B will be set to 1
    def add_instruction_decoherence(self, timeslice, qubit, decoherence, prob, end_of_timeslice = False):
        # Check whether the instruction should be ended
        if end_of_timeslice and (qubit is None) and (decoherence is None) and (prob is None):
            if (len(self.instructions[timeslice].instructions["decoherence"]) > 0):
                # Set the remaining bits of decoherence instruction to 1 if they haven't been inverted
                if not self.instructions[timeslice].new_instruction_need["decoherence"]:
                    self.instructions[timeslice].instructions["decoherence"][self.instructions[timeslice].instruction_index["decoherence"][0]] += (1 << self.instructions[timeslice].bit_position["decoherence"][0]) - 1
                # Set the remaining bits of parameter instruction to 1 if there are remaining bits
                if self.instructions[timeslice].bit_position["decoherence"][1] > 0:
                    self.instructions[timeslice].instructions["decoherence"][self.instructions[timeslice].instruction_index["decoherence"][1]] += (1 << self.instructions[timeslice].bit_position["decoherence"][1]) - 1
                # Set the most significant bit to 1 if the last instruction being added is decoherence
                if self.instructions[timeslice].Operation_last == "decoherence":
                    self.instructions[timeslice].instructions["decoherence"][self.instructions[timeslice].instruction_index["decoherence"][0]] += (1 << (self.N_instr_bits-1))
                self.instructions[timeslice].new_instruction_need["decoherence"] = True
            return
        instruction = 0
        # Check whether a new instruction should be generated for the current timeslice
        if self.instructions[timeslice].new_instruction_need["decoherence"]:
            self.instructions[timeslice].new_instruction_need["decoherence"] = False
            # Set the index of decoherence instruction to the next position of the last parameter instruction
            self.instructions[timeslice].instruction_index["decoherence"][0] = self.instructions[timeslice].instruction_index["decoherence"][1]+1
            self.instructions[timeslice].bit_position["decoherence"][0] = self.N_instr_bits-1-self.operand_length
            self.instructions[timeslice].instructions["decoherence"].append(instruction+(self.quantum_operation_operands["decoherence"]<<(self.N_instr_bits-1-self.operand_length)))
            # Set the remaining bits of the last parameter instruction to 1 if there are remaining bits
            if self.instructions[timeslice].bit_position["decoherence"][1] > 0:
                self.instructions[timeslice].instructions["decoherence"][self.instructions[timeslice].instruction_index["decoherence"][1]] += (1 << self.instructions[timeslice].bit_position["decoherence"][1]) - 1
            # Add the new empty parameter instruction
            self.instructions[timeslice].instruction_index["decoherence"][1] += 2
            self.instructions[timeslice].instructions["decoherence"].append(instruction)
            # Set the bit position of the new parameter instruction
            self.instructions[timeslice].bit_position["decoherence"][1] = self.N_instr_bits
            
        # Add the qubit to the instruction
        self.instructions[timeslice].bit_position["decoherence"][0] -= self.N_qubit_bits
        instruction += (qubit << self.instructions[timeslice].bit_position["decoherence"][0])
        # Add the decoherence to the instruction
        self.instructions[timeslice].bit_position["decoherence"][0] -= self.decoherence_length
        instruction += (self.decoherence[decoherence] << self.instructions[timeslice].bit_position["decoherence"][0])
        # Add the probability
        prob_fixed = Instructions.float_to_fixed_point(prob[0], self.Bits_Float)
        if self.instructions[timeslice].bit_position["decoherence"][1] > 0:
            # Add the probability to the existing parameter instruction if there are remaining bits for that instruction
            self.instructions[timeslice].bit_position["decoherence"][1] -= (self.Bits_Int+self.Bits_Float)
            self.instructions[timeslice].instructions["decoherence"][self.instructions[timeslice].instruction_index["decoherence"][1]]\
                += (prob_fixed << (self.instructions[timeslice].bit_position["decoherence"][1]))
        else:
            # Add the probability to a new parameter instruction
            # Set the bit position of the new parameter instruction
            self.instructions[timeslice].bit_position["decoherence"][1] = self.N_instr_bits-(self.Bits_Int+self.Bits_Float)
            # Add the probability to the new parameter instruction
            self.instructions[timeslice].instructions["decoherence"].append(prob_fixed << self.instructions[timeslice].bit_position["decoherence"][1])
            # Set the instruction index of the parameter
            self.instructions[timeslice].instruction_index["decoherence"][1] += 1
        
        # Check whether the remaining bits is not enough for another decoherence
        if self.instructions[timeslice].bit_position["decoherence"][0] < (self.N_qubit_bits+self.decoherence_length):
            self.instructions[timeslice].new_instruction_need["decoherence"] = True
            # Invert the remaining bits to 1
            instruction += (1 << self.instructions[timeslice].bit_position["decoherence"][0]) - 1
            self.instructions[timeslice].bit_position["decoherence"][0] = self.N_instr_bits
        # If the current gate is last operation in current timeslice, then set the most significant bit to 1 and set the remaining bits to 1
        if end_of_timeslice:
            # Invert the remaining bits to 1 if they haven't been inverted
            if not self.instructions[timeslice].new_instruction_need["decoherence"]:
                instruction += (1 << self.instructions[timeslice].bit_position["decoherence"][0]) - 1
            instruction += (1 << (self.N_instr_bits-1))
            self.instructions[timeslice].new_instruction_need["decoherence"] = True
            # Set the remaining bits of parameter instruction to 1 if there are remaining bits
            if self.instructions[timeslice].bit_position["decoherence"][1] > 0:
                self.instructions[timeslice].instructions["decoherence"][self.instructions[timeslice].instruction_index["decoherence"][1]]\
                    += (1 << self.instructions[timeslice].bit_position["decoherence"][1]) - 1
        # Update the instruction
        self.instructions[timeslice].instructions["decoherence"][self.instructions[timeslice].instruction_index["decoherence"][0]] += instruction
        # Set the last operation to the current operation
        self.instructions[timeslice].Operation_last = "decoherence"
    
    ## Define the instruction generation function of measurement
    def add_instruction_measurement(self, timeslice, instructions):
        # Set the most siginificant bit of measurement instruction to 1 if the current timeslice only has the measurement operation
        if self.instructions[timeslice].Operation_last == "":
            instructions[-1] += (1 << (self.N_instr_bits-1))
            self.instructions[timeslice].Operation_last = "measurement"
        # Add the measurement instruction to the current times_slice_instruction node
        self.instructions[timeslice].instructions["measurement"].extend(instructions)
    
    ## Define the instruction generation function of reset
    # The format of the instruction for reset is as follows:
    # |64|63|62|61|---A---|..............................|
    # 1. bit 64 is used to indicate whether the current instruction is the last instruction in the timeslice
    # 2. bit |63|63|62| is the quantum operation operand for the reset, which should be 110
    # 3. A represents which qubit is under the operation, which needs ceil(log2(N)) bits
    # In general, the reset can be think of a special single qubit operation, unlike measurement that can be conditioned later,
    # the reset operation is completely individual, therefore no further logic is needed to add this instruction
    def add_instruction_reset(self, timeslice, qubit, end_of_timeslice = False):
         # Check whether the instruction should be ended
        if end_of_timeslice and (qubit is None):
            if (len(self.instructions[timeslice].instructions["reset"]) > 0):
                # Set the remaining bits to 1 if they haven't been inverted
                if not self.instructions[timeslice].new_instruction_need["reset"]:
                    self.instructions[timeslice].instructions["reset"][self.instructions[timeslice].instruction_index["reset"]] += (1 << self.instructions[timeslice].bit_position["reset"]) - 1
                # Set the most significant bit to 1 if the last instruction being added is single qubit gate without condition
                if self.instructions[timeslice].Operation_last == "reset":
                    self.instructions[timeslice].instructions["reset"][self.instructions[timeslice].instruction_index["reset"]] += (1 << (self.N_instr_bits-1))
                self.instructions[timeslice].new_instruction_need["reset"] = True
            return
        instruction = 0
        # Check whether a new instruction should be generated for the current timeslice
        if self.instructions[timeslice].new_instruction_need["reset"]:
            self.instructions[timeslice].new_instruction_need["reset"] = False
            self.instructions[timeslice].instruction_index["reset"] += 1
            self.instructions[timeslice].bit_position["reset"] = self.N_instr_bits-1-self.operand_length
            self.instructions[timeslice].instructions["reset"].append(self.quantum_operation_operands["reset"]<<(self.N_instr_bits-1-self.operand_length))
        # The qubit is added to the instruction
        self.instructions[timeslice].bit_position["reset"] -= self.N_qubit_bits
        instruction += (qubit << self.instructions[timeslice].bit_position["reset"])
        # Check whether the remaining bits is not enough for another qubit gate pair
        if self.instructions[timeslice].bit_position["reset"] < (self.N_qubit_bits):
            self.instructions[timeslice].new_instruction_need["reset"] = True
            # Invert the remaining bits to 1
            instruction += (1 << self.instructions[timeslice].bit_position["reset"]) - 1
            self.instructions[timeslice].bit_position["reset"] = self.N_instr_bits
        # If the current gate is last operation in current timeslice, then set the most significant bit to 1 and set the remaining bits to 1
        if end_of_timeslice:
            # Invert the remaining bits to 1 if they haven't been inverted
            if not self.instructions[timeslice].new_instruction_need["reset"]:
                instruction += (1 << self.instructions[timeslice].bit_position["reset"]) - 1
            instruction += (1 << (self.N_instr_bits-1))
            self.instructions[timeslice].new_instruction_need["reset"] = True
        # Update the instruction
        self.instructions[timeslice].instructions["reset"][self.instructions[timeslice].instruction_index["reset"]] += instruction
        # Set the last operation to the current operation
        self.instructions[timeslice].Operation_last = "reset"
        
        
    def instruction_gen_timeslice(self, timeslice, qubit, timeslice_node, end_of_timeslice, quantumcircuit):
        # Check whether the instruction node exists for the current timeslice
        if timeslice not in self.instructions:
            self.instructions[timeslice] = timeslice_instruction_node(self.N_instr_bits)
        # Check whether the current gate operation is a single qubit gate without condition
        if (timeslice_node.gate_operation in self.single_qubit_gates) and (not timeslice_node.if_flag):
            self.add_instruction_single_gate_no_condition(timeslice, timeslice_node.gate_operation, qubit, end_of_timeslice, timeslice_node.parameters)
            # If the current qubit is the last qubit, then to make sure the remaining bits of the instructions for all other operations are set to 1
            if end_of_timeslice:
                self.add_instruction_single_gate_condition(timeslice, None, None, None, None, None, None, end_of_timeslice, None)
                self.add_instruction_control_gate_no_condition(timeslice, None, None, None, end_of_timeslice, None)
                self.add_instruction_control_gate_condition(timeslice, None, None, None, None, None, None, None, end_of_timeslice, None)
                self.add_instruction_decoherence(timeslice, None, None, None, end_of_timeslice)
                self.add_instruction_reset(timeslice, None, end_of_timeslice)
            return
        # Check whether the current gate operation is a single qubit gate with condition
        elif (timeslice_node.gate_operation in self.single_qubit_gates) and (timeslice_node.if_flag):
            # Add the measurement instruction the the last timeslice if it haven't been added
            if not self.measurement.check_last_instruction_added():
                # Set the remaining bits of measurement instruction to 1
                self.measurement.set_remaining_bits()
                # Add the measurement instruction to the last timeslice
                self.add_instruction_measurement(self.last_valid_timeslice, self.measurement.get_instruction())
            # Add the single qubit gate with condition to the current timeslice
            # For the first kind
            if timeslice_node.if_kind == 0:
                self.add_instruction_single_gate_condition(timeslice, timeslice_node.gate_operation, qubit, quantumcircuit.cregs_idx[timeslice_node.if_creg], 0,\
                    timeslice_node.if_num, timeslice_node.if_kind, end_of_timeslice, timeslice_node.parameters)
            else:
                # Find the lower bound and upper bound of the classical bits
                bit_l = quantumcircuit.cregs_idx[timeslice_node.if_creg+"[0]"]
                bit_h = bit_l + quantumcircuit.cregs_size[timeslice_node.if_creg] - 1
                self.add_instruction_single_gate_condition(timeslice, timeslice_node.gate_operation, qubit, bit_l, bit_h,\
                    timeslice_node.if_num, timeslice_node.if_kind, end_of_timeslice, timeslice_node.parameters)
            if end_of_timeslice:
                self.add_instruction_single_gate_no_condition(timeslice, None, None, end_of_timeslice, None)
                self.add_instruction_control_gate_no_condition(timeslice, None, None, None, end_of_timeslice, None)
                self.add_instruction_control_gate_condition(timeslice, None, None, None, None, None, None, None, end_of_timeslice, None)
                self.add_instruction_decoherence(timeslice, None, None, None, end_of_timeslice)
                self.add_instruction_reset(timeslice, None, end_of_timeslice)
            return
        # Check whether the current gate operation is a controlled gate without condition
        elif timeslice_node.controlled_operation and (not timeslice_node.if_flag):
            # If the current qubit is target qubit then generate the instruction otherwise skip
            if timeslice_node.target_qubit:
                self.add_instruction_control_gate_no_condition(timeslice, timeslice_node.gate_operation, qubit, \
                    [quantumcircuit.qubits_idx[timeslice_node.connected_qubits[i]] for i in range(len(timeslice_node.connected_qubits))], end_of_timeslice, timeslice_node.parameters)
            if end_of_timeslice:
                self.add_instruction_single_gate_no_condition(timeslice, None, None, end_of_timeslice, None)
                self.add_instruction_single_gate_condition(timeslice, None, None, None, None, None, None, end_of_timeslice, None)
                self.add_instruction_control_gate_condition(timeslice, None, None, None, None, None, None, None, end_of_timeslice, None)
                self.add_instruction_decoherence(timeslice, None, None, None, end_of_timeslice)
                self.add_instruction_reset(timeslice, None, end_of_timeslice)
                # Set the remaining bits of controlled gate without condition instruction to 1 if the control qubit is at the end of the timeslice
                if not timeslice_node.target_qubit:
                    self.add_instruction_control_gate_no_condition(timeslice, None, None, None, end_of_timeslice, None)
            return
        # Check whether the current gate operation is a controlled gate with condition
        elif timeslice_node.controlled_operation and timeslice_node.if_flag:
            # If the current qubit is target qubit then generate the instruction otherwise skip
            if timeslice_node.target_qubit:
                # Add the measurement instruction the the last timeslice if it haven't been added
                if not self.measurement.check_last_instruction_added():
                    # Set the remaining bits of measurement instruction to 1
                    self.measurement.set_remaining_bits()
                    if timeslice_node.gate_operation == "crx":
                        print(self.last_valid_timeslice)
                    # Add the measurement instruction to the last timeslice
                    self.add_instruction_measurement(self.last_valid_timeslice, self.measurement.get_instruction())
                # Add the controlled gate with condition to the current timeslice
                # For the first kind
                if timeslice_node.if_kind == 0:
                    # add_instruction_control_gate_condition(self, timeslice, gate, target_qubit, control_qubits, classical_bit_l, classical_bit_h, val, kind, end_of_timeslice = False, parameter = None)
                    self.add_instruction_control_gate_condition(timeslice, timeslice_node.gate_operation, qubit, \
                        [quantumcircuit.qubits_idx[timeslice_node.connected_qubits[i]] for i in range(len(timeslice_node.connected_qubits))],\
                        quantumcircuit.cregs_idx[timeslice_node.if_creg], 0, timeslice_node.if_num, timeslice_node.if_kind, end_of_timeslice, timeslice_node.parameters)
                else:
                    # Find the lower bound and upper bound of the classical bits
                    bit_l = quantumcircuit.cregs_idx[timeslice_node.if_creg+"[0]"]
                    bit_h = bit_l + quantumcircuit.cregs_size[timeslice_node.if_creg] - 1
                    self.add_instruction_control_gate_condition(timeslice, timeslice_node.gate_operation, qubit, \
                        [quantumcircuit.qubits_idx[timeslice_node.connected_qubits[i]] for i in range(len(timeslice_node.connected_qubits))],\
                        bit_l, bit_h, timeslice_node.if_num, timeslice_node.if_kind, end_of_timeslice, timeslice_node.parameters)
            if end_of_timeslice:
                self.add_instruction_single_gate_no_condition(timeslice, None, None, end_of_timeslice, None)
                self.add_instruction_single_gate_condition(timeslice, None, None, None, None, None, None, end_of_timeslice, None)
                self.add_instruction_control_gate_no_condition(timeslice, None, None, None, end_of_timeslice, None)
                self.add_instruction_decoherence(timeslice, None, None, None, end_of_timeslice)
                self.add_instruction_reset(timeslice, None, end_of_timeslice)
                # Set the remaining bits of controlled gate with condition instruction to 1 if the control qubit is at the end of the timeslice
                if not timeslice_node.target_qubit:
                    self.add_instruction_control_gate_condition(timeslice, None, None, None, None, None, None, None, end_of_timeslice, None)
            return
        # Check whether the current gate operation is a decoherence operation
        elif timeslice_node.gate_operation in self.decoherence:
            # add_instruction_decoherence(self, timeslice, qubit, decoherence, prob, end_of_timeslice = False)
            self.add_instruction_decoherence(timeslice, qubit, timeslice_node.gate_operation, timeslice_node.parameters, end_of_timeslice)
            if end_of_timeslice:
                self.add_instruction_single_gate_no_condition(timeslice, None, None, end_of_timeslice, None)
                self.add_instruction_single_gate_condition(timeslice, None, None, None, None, None, None, end_of_timeslice, None)
                self.add_instruction_control_gate_no_condition(timeslice, None, None, None, end_of_timeslice, None)
                self.add_instruction_control_gate_condition(timeslice, None, None, None, None, None, None, None, end_of_timeslice, None)
                self.add_instruction_reset(timeslice, None, end_of_timeslice)
            return
        # Check whether the current gate operation is a measurement operation
        elif timeslice_node.measurement:
            self.measurement.set_measured_qubit(quantumcircuit.cregs_idx[timeslice_node.connected_cregs[0]], timeslice)
            self.measurement.add_instruction(quantumcircuit.cregs_idx[timeslice_node.connected_cregs[0]])
            if end_of_timeslice:
                self.add_instruction_single_gate_no_condition(timeslice, None, None, end_of_timeslice, None)
                self.add_instruction_single_gate_condition(timeslice, None, None, None, None, None, None, end_of_timeslice, None)
                self.add_instruction_control_gate_no_condition(timeslice, None, None, None, end_of_timeslice, None)
                self.add_instruction_control_gate_condition(timeslice, None, None, None, None, None, None, None, end_of_timeslice, None)
                self.add_instruction_decoherence(timeslice, None, None, None, end_of_timeslice)
                self.add_instruction_reset(timeslice, None, end_of_timeslice)
            return
        # Check whether the current gate operation is a reset operation
        elif timeslice_node.reset:
            # Add the reset instruction to the current timeslice
            self.add_instruction_reset(timeslice, qubit, end_of_timeslice)
            if end_of_timeslice:
                self.add_instruction_single_gate_no_condition(timeslice, None, None, end_of_timeslice, None)
                self.add_instruction_single_gate_condition(timeslice, None, None, None, None, None, None, end_of_timeslice, None)
                self.add_instruction_control_gate_no_condition(timeslice, None, None, None, end_of_timeslice, None)
                self.add_instruction_control_gate_condition(timeslice, None, None, None, None, None, None, None, end_of_timeslice, None)
                self.add_instruction_decoherence(timeslice, None, None, None, end_of_timeslice)
            return
        else:
            return
    
    @staticmethod
    def generate_instruction(quantumcircuit):
        # Find the number of qubits
        N_qubits = len(quantumcircuit.qubits)
        # Create the instruction object
        instruction = Instructions(N_qubits)
        # Loop through the quantum circuit to generate the instructions
        for timeslice_idx in range(1, quantumcircuit.max_time_slice+1):
            qubit_idx = 0
            timeslice_empty = True
            for qubit in quantumcircuit.qubits:
                end_of_timeslice = True if qubit_idx == len(quantumcircuit.qubits)-1 else False
                if ((f"timeslice_{timeslice_idx}" not in quantumcircuit.qubits[qubit]) and (end_of_timeslice)):
                    # Check whether there the whole timeslice is empty
                    if timeslice_idx not in instruction.instructions:
                        continue
                    instruction.add_instruction_single_gate_no_condition(timeslice_idx, None, None, end_of_timeslice, None)
                    instruction.add_instruction_single_gate_condition(timeslice_idx, None, None, None, None, None, None, end_of_timeslice, None)
                    instruction.add_instruction_control_gate_no_condition(timeslice_idx, None, None, None, end_of_timeslice, None)
                    instruction.add_instruction_control_gate_condition(timeslice_idx, None, None, None, None, None, None, None, end_of_timeslice, None)
                    instruction.add_instruction_decoherence(timeslice_idx, None, None, None, end_of_timeslice)
                    instruction.add_instruction_reset(timeslice_idx, None, end_of_timeslice)
                    continue
                if f"timeslice_{timeslice_idx}" in quantumcircuit.qubits[qubit]:
                    # Set the remaining bits of generated instructions to 1 and set the corresponding most significant bit
                    if quantumcircuit.qubits[qubit][f"timeslice_{timeslice_idx}"].barrier and end_of_timeslice:
                        # print("comming into barrier")
                        instruction.add_instruction_single_gate_no_condition(timeslice_idx, None, None, end_of_timeslice, None)
                        instruction.add_instruction_single_gate_condition(timeslice_idx, None, None, None, None, None, None, end_of_timeslice, None)
                        instruction.add_instruction_control_gate_no_condition(timeslice_idx, None, None, None, end_of_timeslice, None)
                        instruction.add_instruction_control_gate_condition(timeslice_idx, None, None, None, None, None, None, None, end_of_timeslice, None)
                        instruction.add_instruction_decoherence(timeslice_idx, None, None, None, end_of_timeslice)
                        instruction.add_instruction_reset(timeslice_idx, None, end_of_timeslice)
                    instruction.instruction_gen_timeslice(timeslice_idx, qubit_idx, quantumcircuit.qubits[qubit][f"timeslice_{timeslice_idx}"], end_of_timeslice, quantumcircuit)
                    timeslice_empty = False
                qubit_idx += 1
            if not timeslice_empty:
                instruction.last_valid_timeslice = timeslice_idx
        # Check whether there's a remaining measurement instruction that is not used by classical conditoned operations and should be added to the last timeslice
        if not instruction.measurement.check_last_instruction_added():
            # Set the remaining bits of measurement instruction to 1
            instruction.measurement.set_remaining_bits()
            # Add the measurement instruction to the last timeslice
            instruction.add_instruction_measurement(quantumcircuit.max_time_slice, instruction.measurement.get_instruction())
        return instruction
    
# a = Instructions.float_to_fixed_point(0.5, 30)
# b = Instructions.float_to_fixed_point(0.75, 30)