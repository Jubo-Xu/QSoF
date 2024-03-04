'''
This file is mainly used to define the functions that are needed to segment the original quantum circuit
described by QASM file into different time slices, which each time slice contains the maximum number of 
quantum gates that can be executed in parallel. One thing to keep in mind for now is that for all the single
qubit gates that has off-diagonal elements in its matrix representation, if theoretically they could be executed 
in parallel for different qubits, we still need to put them into different time slices. This is because such gates 
would increase the number of new possible states, and there's a limitation in hardware design in FPGA to deal with 
this condition. It can be changed later if the hardware design is improved.

The quantum circuit after the segmentation would be described by a 3D graph
'''
from InstructionGenerator.instruction import Instructions
from hardware_specification import Specification
from timeslice import Time_slice_node
from IR.QASM2.qasm2_parser import Parser
import struct

class Quantum_circuit:
    # Class level attributes to enable the hardware specification and optimization decorators
    hardware_specification_enable = True
    def __init__(self):
        self.name = ""
        self.qubits = {}
        self.cregs = {}
        self.cregs_size = {} # This is used to store the size of each creg, which is used for two kinds of if condition
        # The following two dictionaries are used to store the index of each qubit and creg mainly for instruction generation
        self.qubits_idx = {}
        self.cregs_idx = {}
        self.qubits_idx_idx = 0
        self.cregs_idx_idx = 0
        # This is an intermidiate variable to store the current maximum time slice index for each qubit 
        self.qubit_max_time_slice = {}
        # This is an intermidiate variable to store the current maximum time slice index for the classical bit
        self.creg_max_time_slice = {}
        self.max_time_slice = 0
        self.measured_max_time_slice = 0 # This is used to indicate the maximum time slice index among all the cregs, which is used to put the conditioned operations after all the previous defined measurements
        # Instantiate the specification
        self.spec = Specification()
    
    def __repr__(self):
        return f"Quantum Circuit: {self.name}"
    
    def get_name(self):
        return self.__repr__()
    
    def set_name(self, name):
        self.name = name
    
    # Add a new qubit with the given name and size to the current circuit
    def add_qubit(self, qubit_name, size):
        for i in range(size):
            self.qubits[qubit_name + f"[{i}]"] = {} # the value of each qubit is a dictionary, where key is timeslice and value is the timeslice node
            self.qubits_idx[qubit_name + f"[{i}]"] = self.qubits_idx_idx
            self.qubits_idx_idx += 1
    
    def add_creg(self, creg_name, size):
        self.cregs_size[creg_name] = size
        for i in range(size):
            self.cregs[creg_name + f"[{i}]"] = {}
            self.cregs_idx[creg_name + f"[{i}]"] = self.cregs_idx_idx
            self.cregs_idx_idx += 1
    
    #================================================================================================
    # The following functions are used to add the quantum operations to the circuit
    #================================================================================================
    
    # Add the current maximum time slice index for the qubit 
    def add_qubit_max_time_slice(self, qubit_name, time_slice_index, size=1):
        if qubit_name not in self.qubit_max_time_slice:
            for i in range(size):
                self.qubit_max_time_slice[qubit_name + f"[{i}]"] = 0
        else:
            self.qubit_max_time_slice[qubit_name + f"[{size}]"] = time_slice_index
    
    # Add a new no parameter single qubit gate to the circuit
    def add_single_qubit_gate_no_parameter(self, gate_name, qubit_name, index=-1, if_creg=None, if_num=0, if_flag=False):
        # Check if the gate is conditioned
        if_kind = 0
        creg_time_slice = 0
        if if_flag:
            if (if_creg[1] == -1) and (self.cregs_size[if_creg[0]] > 1):
                if_creg_name = if_creg[0]
                if_kind = 1
            else:
                if_creg_name = if_creg[0] + f"[{if_creg[1]}]" if if_creg[1] != -1 else if_creg[0]+"[0]"
            # creg_time_slice = self.creg_max_time_slice[if_creg_name] + 1
            creg_time_slice = self.measured_max_time_slice + 1
        qubit = qubit_name + f"[{index}]" if index != -1 else qubit_name+"[0]"
        time_slice = self.qubit_max_time_slice[qubit] + 1
        time_slice = max(time_slice, creg_time_slice)
        self.qubit_max_time_slice[qubit] = time_slice
        time_slice_node = Time_slice_node(gate_name)
        time_slice_node.time_slice_index = time_slice
        if if_flag:
            time_slice_node.if_flag = True
            time_slice_node.if_num = int(if_num)
            time_slice_node.if_creg = if_creg_name
            time_slice_node.if_kind = if_kind
        self.qubits[qubit][f"timeslice_{time_slice}"] = time_slice_node
        self.max_time_slice = max(self.max_time_slice, time_slice)  
    
    # Add a new single qubit gate with parameter to the circuit
    def add_single_qubit_gate_with_parameter(self, gate_name, qubit_name, parameter, index = -1, if_creg=None, if_num=0, if_flag=False):
        # Check if the gate is conditioned
        creg_time_slice = 0
        if_kind = 0
        if if_flag:
            if (if_creg[1] == -1) and (self.cregs_size[if_creg[0]] > 1):
                if_creg_name = if_creg[0]
                if_kind = 1
            else:
                if_creg_name = if_creg[0] + f"[{if_creg[1]}]" if if_creg[1] != -1 else if_creg[0]+"[0]"
            # creg_time_slice = self.creg_max_time_slice[if_creg_name] + 1
            creg_time_slice = self.measured_max_time_slice + 1
        qubit = qubit_name + f"[{index}]" if index != -1 else qubit_name+"[0]"
        time_slice = max(self.qubit_max_time_slice[qubit] + 1, creg_time_slice)
        self.qubit_max_time_slice[qubit] = time_slice
        time_slice_node = Time_slice_node(gate_name)
        time_slice_node.with_parameter = True
        time_slice_node.time_slice_index = time_slice
        time_slice_node.add_parameter(parameter)
        if if_flag:
            time_slice_node.if_flag = True
            time_slice_node.if_num = int(if_num)
            time_slice_node.if_creg = if_creg_name
            time_slice_node.if_kind = if_kind
        self.qubits[qubit][f"timeslice_{time_slice}"] = time_slice_node
        self.max_time_slice = max(self.max_time_slice, time_slice)
    
    # Add a new controlled single qubit gate without parameter to the circuit
    def add_controlled_gate_no_parameter(self, gate_name, control_qubit, target_qubit, target_index=-1, if_creg=None, if_num=0, if_flag=False):
        if_creg_name = ""
        if_creg_num = 0
        if_kind = 0
        creg_time_slice = 0
        if if_flag:
            if (if_creg[1] == -1) and (self.cregs_size[if_creg[0]] > 1):
                if_creg_name = if_creg[0]
                if_kind = 1
            else:
                if_creg_name = if_creg[0] + f"[{if_creg[1]}]" if if_creg[1] != -1 else if_creg[0]+"[0]"
            if_creg_num = int(if_num)
            # creg_time_slice = self.creg_max_time_slice[if_creg_name] + 1
            creg_time_slice = self.measured_max_time_slice + 1
        # create a new list that stores all the qubit names, the first element is the target qubit
        qubit_names = [target_qubit + f"[{target_index}]" if target_index != -1 else target_qubit+"[0]"]
        # add the control qubit to the list and find the maximum timeslice index
        max_time_slice = self.qubit_max_time_slice[qubit_names[0]]
        for i in range(len(control_qubit)):
            qubit_name = control_qubit[i][0]+f"[{control_qubit[i][1]}]" if control_qubit[i][1] != -1 else control_qubit[i][0]+"[0]"
            qubit_names.append(qubit_name)
            if self.qubit_max_time_slice[qubit_name] > max_time_slice:
                max_time_slice = self.qubit_max_time_slice[qubit_name]
        # Add 1 to the maximum timeslice index to get the current timeslice index
        max_time_slice += 1
        max_time_slice = max(max_time_slice, creg_time_slice)
        # Loop through all the qubits in the list and add the new timeslice node to the circuit with the current timeslice index
        # First add the target qubit
        self.qubit_max_time_slice[qubit_names[0]] = max_time_slice
        time_slice_node_target = Time_slice_node(gate_name)
        time_slice_node_target.time_slice_index = max_time_slice
        time_slice_node_target.controlled_operation = True # Set the controlled_operation flag to True to indicate this is a controlled gate
        time_slice_node_target.add_connected_qubit(qubit_names[1:])
        # Add the conditioned variables to the target timeslice node
        if if_flag:
            time_slice_node_target.if_flag = True
            time_slice_node_target.if_num = if_creg_num
            time_slice_node_target.if_creg = if_creg_name
            time_slice_node_target.if_kind = if_kind
        # Add the new timeslice node of the target qubit to the circuit
        self.qubits[qubit_names[0]][f"timeslice_{max_time_slice}"] = time_slice_node_target
        # Loop through all the control qubits and add the new timeslice node to the circuit with the current timeslice index
        for i in range(1, len(qubit_names)):
            qubit = qubit_names[i]
            self.qubit_max_time_slice[qubit] = max_time_slice
            time_slice_node_control = Time_slice_node(gate_name)
            time_slice_node_control.time_slice_index = max_time_slice
            time_slice_node_control.target_qubit = False # Set the target_qubit flag to False to indicate this is a control qubit
            time_slice_node_control.controlled_operation = True # Set the controlled_operation flag to True to indicate this is a controlled gate
            time_slice_node_control.add_connected_qubit(qubit_names[0:i])
            time_slice_node_control.add_connected_qubit(qubit_names[i+1:])
            # Add the conditioned variables to the control timeslice node
            if if_flag:
                time_slice_node_control.if_flag = True
                time_slice_node_control.if_num = if_creg_num
                time_slice_node_control.if_creg = if_creg_name
                time_slice_node_control.if_kind = if_kind
            self.qubits[qubit][f"timeslice_{max_time_slice}"] = time_slice_node_control
        # Update the maximum timeslice index of the circuit
        self.max_time_slice = max(self.max_time_slice, max_time_slice)
    
    # Add a new controlled single qubit gate with parameter to the circuit
    def add_controlled_gate_with_parameter(self, gate_name, control_qubit, target_qubit, parameter, target_index=-1, if_creg=None, if_num=0, if_flag=False):
        if_creg_name = ""
        if_creg_num = 0
        if_kind = 0
        creg_time_slice = 0
        if if_flag:
            if (if_creg[1] == -1) and (self.cregs_size[if_creg[0]] > 1):
                if_creg_name = if_creg[0]
                if_kind = 1
            else:
                if_creg_name = if_creg[0] + f"[{if_creg[1]}]" if if_creg[1] != -1 else if_creg[0]+"[0]"
            if_creg_num = int(if_num)
            # creg_time_slice = self.creg_max_time_slice[if_creg_name] + 1
            creg_time_slice = self.measured_max_time_slice + 1
        # create a new list that stores all the qubit names, the first element is the target qubit
        qubit_names = [target_qubit + f"[{target_index}]" if target_index != -1 else target_qubit+"[0]"]
        # add the control qubit to the list and find the maximum timeslice index
        max_time_slice = self.qubit_max_time_slice[qubit_names[0]]
        for i in range(len(control_qubit)):
            qubit_name = control_qubit[i][0]+f"[{control_qubit[i][1]}]" if control_qubit[i][1] != -1 else control_qubit[i][0]+"[0]"
            qubit_names.append(qubit_name)
            if self.qubit_max_time_slice[qubit_name] > max_time_slice:
                max_time_slice = self.qubit_max_time_slice[qubit_name]
        # Add 1 to the maximum timeslice index to get the current timeslice index
        max_time_slice += 1
        max_time_slice = max(max_time_slice, creg_time_slice)
        # Loop through all the qubits in the list and add the new timeslice node to the circuit with the current timeslice index
        # First add the target qubit
        self.qubit_max_time_slice[qubit_names[0]] = max_time_slice
        time_slice_node_target = Time_slice_node(gate_name)
        time_slice_node_target.with_parameter = True
        time_slice_node_target.add_parameter(parameter)
        time_slice_node_target.time_slice_index = max_time_slice
        time_slice_node_target.controlled_operation = True # Set the controlled_operation flag to True to indicate this is a controlled gate
        time_slice_node_target.add_connected_qubit(qubit_names[1:])
        # Add the conditioned variables to the target timeslice node
        if if_flag:
            time_slice_node_target.if_flag = True
            time_slice_node_target.if_num = if_creg_num
            time_slice_node_target.if_creg = if_creg_name
            time_slice_node_target.if_kind = if_kind
        # Add the new timeslice node of the target qubit to the circuit
        self.qubits[qubit_names[0]][f"timeslice_{max_time_slice}"] = time_slice_node_target
        # Loop through all the control qubits and add the new timeslice node to the circuit with the current timeslice index
        for i in range(1, len(qubit_names)):
            qubit = qubit_names[i]
            self.qubit_max_time_slice[qubit] = max_time_slice
            time_slice_node_control = Time_slice_node(gate_name)
            time_slice_node_control.with_parameter = True
            time_slice_node_control.time_slice_index = max_time_slice
            time_slice_node_control.add_parameter(parameter)
            time_slice_node_control.target_qubit = False # Set the target_qubit flag to False to indicate this is a control qubit
            time_slice_node_control.controlled_operation = True # Set the controlled_operation flag to True to indicate this is a controlled gate
            time_slice_node_control.add_connected_qubit(qubit_names[0:i])
            time_slice_node_control.add_connected_qubit(qubit_names[i+1:])
            # Add the conditioned variables to the control timeslice node
            if if_flag:
                time_slice_node_control.if_flag = True
                time_slice_node_control.if_num = if_creg_num
                time_slice_node_control.if_creg = if_creg_name
                time_slice_node_control.if_kind = if_kind
            self.qubits[qubit][f"timeslice_{max_time_slice}"] = time_slice_node_control
        # Update the maximum timeslice index of the circuit
        self.max_time_slice = max(self.max_time_slice, max_time_slice)
    
    # Add the measurement operation to the circuit
    def add_measurement(self, qubit, creg, if_creg=None, if_num=0, if_flag=False):
        max_time_slice = 0
        qubit_names = []
        creg_names = []
        creg_time_slice = 0
        if_creg_name = ""
        if_creg_num = 0
        if_kind = 0
        if if_flag:
            if (if_creg[1] == -1) and (self.cregs_size[if_creg[0]] > 1):
                if_creg_name = if_creg[0]
                if_kind = 1
            else:
                if_creg_name = if_creg[0] + f"[{if_creg[1]}]" if if_creg[1] != -1 else if_creg[0]+"[0]"
            if_creg_num = int(if_num)
            # creg_time_slice = self.creg_max_time_slice[if_creg_name] + 1
            creg_time_slice = self.measured_max_time_slice + 1
        for i in range(len(qubit)):
            # Get the qubit name and the creg name
            qubit_name = qubit[i][0] + f"[{qubit[i][1]}]" if qubit[i][1] != -1 else qubit[i][0]+"[0]"
            creg_name = creg[i][0] + f"[{creg[i][1]}]" if creg[i][1] != -1 else creg[i][0]+"[0]"
            qubit_names.append(qubit_name)
            creg_names.append(creg_name)
            # Set the maximum timeslice index for the current qubit
            time_slice = self.qubit_max_time_slice[qubit_name] + 1
            max_time_slice = time_slice if time_slice > max_time_slice else max_time_slice
        max_time_slice = max(max_time_slice, creg_time_slice)
        # Set the measured maximum timeslice index
        self.measured_max_time_slice = max(self.measured_max_time_slice, max_time_slice)
        # Set the maximum timeslice index for all the cregs, this is for the later operations conditioned under this measurement
        for i in range(len(creg_names)):
            self.creg_max_time_slice[creg_names[i]] = max_time_slice
        # Loop through all the qubits in the list and add the new timeslice node to the circuit with the current timeslice index
        for i in range(len(qubit_names)):
            self.qubit_max_time_slice[qubit_names[i]] = max_time_slice
            # Create a new timeslice node for the current qubit
            time_slice_node = Time_slice_node("M")
            time_slice_node.time_slice_index = max_time_slice
            time_slice_node.connected_cregs.append(creg_names[i])
            time_slice_node.measurement = True
            # Add the conditioned variables to the measurement timeslice node
            if if_flag:
                time_slice_node.if_flag = True
                time_slice_node.if_num = if_creg_num
                time_slice_node.if_creg = if_creg_name
                time_slice_node.if_kind = if_kind
            # Add the new timeslice node to the circuit
            self.qubits[qubit_names[i]][f"timeslice_{max_time_slice}"] = time_slice_node
            # Add the qubit of current timeslice index to the creg
            self.cregs[creg_names[i]][f"timeslice_{max_time_slice}"] = qubit_names[i]
            # Set the maximum timeslice index for the circuit
        self.max_time_slice = max(self.max_time_slice, max_time_slice)
    
    # Add the reset operation to the circuit
    def add_reset(self, qubit, if_creg=None, if_num=0, if_flag=False):
        max_time_slice = 0
        qubit_names = []
        if_creg_name = ""
        if_creg_num = 0
        if_kind = 0
        if if_flag:
            if (if_creg[1] == -1) and (self.cregs_size[if_creg[0]] > 1):
                if_creg_name = if_creg[0]
                if_kind = 1
            else:
                if_creg_name = if_creg[0] + f"[{if_creg[1]}]" if if_creg[1] != -1 else if_creg[0]+"[0]"
            if_creg_num = int(if_num)
        for i in range(len(qubit)):
            # Get the qubit name
            qubit_name = qubit[i][0] + f"[{qubit[i][1]}]" if qubit[i][1] != -1 else qubit[i][0]+"[0]"
            qubit_names.append(qubit_name)
            # Set the maximum timeslice index for the current qubit
            time_slice = self.qubit_max_time_slice[qubit_name] + 1
            max_time_slice = time_slice if time_slice > max_time_slice else max_time_slice
        for i in range(len(qubit_names)):
            self.qubit_max_time_slice[qubit_names[i]] = max_time_slice
            # Create a new timeslice node for the current qubit
            time_slice_node = Time_slice_node("reset")
            time_slice_node.time_slice_index = max_time_slice
            time_slice_node.reset = True
            # Add the conditioned variables to the reset timeslice node
            if if_flag:
                time_slice_node.if_flag = True
                time_slice_node.if_num = if_creg_num
                time_slice_node.if_creg = if_creg_name
                time_slice_node.if_kind = if_kind
            # Add the new timeslice node to the circuit
            self.qubits[qubit_names[i]][f"timeslice_{max_time_slice}"] = time_slice_node
            # Set the maximum timeslice index for the circuit
        self.max_time_slice = max(self.max_time_slice, max_time_slice)
    
    # Add the barrier operation to the circuit
    def add_barrier(self, qubit):
        max_time_slice = 0
        qubit_names = []
        for i in range(len(qubit)):
            # Get the qubit name
            qubit_name = qubit[i][0] + f"[{qubit[i][1]}]" if qubit[i][1] != -1 else qubit[i][0]+"[0]"
            qubit_names.append(qubit_name)
            # Set the maximum timeslice index for the current qubit
            time_slice = self.qubit_max_time_slice[qubit_name] + 1
            max_time_slice = time_slice if time_slice > max_time_slice else max_time_slice
        for i in range(len(qubit_names)):
            self.qubit_max_time_slice[qubit_names[i]] = max_time_slice
            # Create a new timeslice node for the current qubit
            time_slice_node = Time_slice_node("BARRIER")
            time_slice_node.time_slice_index = max_time_slice
            # Set the barrier flag to True to indicate this is a barrier operation
            time_slice_node.barrier = True
            # Add the new timeslice node to the circuit
            self.qubits[qubit_names[i]][f"timeslice_{max_time_slice}"] = time_slice_node
            # Set the maximum timeslice index for the circuit
        self.max_time_slice = max(self.max_time_slice, max_time_slice)
    
    # Add the opaque operation to the circuit  
    def add_opaque(self, opaque_name, qubits, parameter, if_creg=None, if_num=0, if_flag=False):
        # Set up the condition variables
        if_creg_name = ""
        if_creg_num = 0
        if_kind = 0
        if if_flag:
            if (if_creg[1] == -1) and (self.cregs_size[if_creg[0]] > 1):
                if_creg_name = if_creg[0]
                if_kind = 1
            else:
                if_creg_name = if_creg[0] + f"[{if_creg[1]}]" if if_creg[1] != -1 else if_creg[0]+"[0]"
            if_creg_num = int(if_num)
        qubit_names = [qubits[0][0] + f"[{qubits[0][1]}]" if qubits[0][1] != -1 else qubits[0][0]+"[0]"]
        # add the control qubit to the list and find the maximum timeslice index
        max_time_slice = self.qubit_max_time_slice[qubit_names[0]]
        for i in range(1, len(qubits)):
            qubit_name = qubits[i][0]+f"[{qubits[i][1]}]" if qubits[i][1] != -1 else qubits[i][0]+"[0]"
            qubit_names.append(qubit_name)
            if self.qubit_max_time_slice[qubit_name] > max_time_slice:
                max_time_slice = self.qubit_max_time_slice[qubit_name]
        # Add 1 to the maximum timeslice index to get the current timeslice index
        max_time_slice += 1
        # Loop through all the qubits in the list and add the new timeslice node to the circuit with the current timeslice index
        for i in range(len(qubit_names)):
            qubit = qubit_names[i]
            self.qubit_max_time_slice[qubit] = max_time_slice
            time_slice_node_opaque = Time_slice_node(opaque_name)
            if parameter:
                time_slice_node_opaque.with_parameter = True
                time_slice_node_opaque.add_parameter(parameter) 
            time_slice_node_opaque.time_slice_index = max_time_slice
            time_slice_node_opaque.add_connected_qubit(qubit_names[0:i])
            time_slice_node_opaque.add_connected_qubit(qubit_names[i+1:])
            # Add the conditioned variables to the control timeslice node
            if if_flag:
                time_slice_node_opaque.if_flag = True
                time_slice_node_opaque.if_num = if_creg_num
                time_slice_node_opaque.if_creg = if_creg_name
                time_slice_node_opaque.if_kind = if_kind
            self.qubits[qubit][f"timeslice_{max_time_slice}"] = time_slice_node_opaque
        # Update the maximum timeslice index of the circuit
        self.max_time_slice = max(self.max_time_slice, max_time_slice)
    
    #================================================================================================
    # The following functions are the decorators for hardware specification and optimization
    #================================================================================================
    # # Define the decorator for hardware specifications
    def HardwareSpecification(func):
        def wrapper(*args, **kwargs):
            quantumcircuit_orig = func(*args, **kwargs)
            quantumcircuit_new = Quantum_circuit()
            if Specification.Need:
                Specification.create_specified_quantumcircuit(quantumcircuit_orig, quantumcircuit_new, quantumcircuit_new.spec)
                return quantumcircuit_new
            else:
                return quantumcircuit_orig
        return wrapper
    
    #================================================================================================
    # The following functions are used to generate the quantum circuit from the different sources
    #================================================================================================
    # Generate the quantum circuit from the OpenQASM 2.0 file
    @staticmethod
    @HardwareSpecification
    def from_qasm2(qasmfile):
        QC = Quantum_circuit()
        Parser.compile(qasmfile, QC)
        return QC
    
    #================================================================================================
    # The following functions are used to generate the instruction
    #================================================================================================
    # Generate the instruction for the quantum circuit and store the binary representation into the .txt file
    def to_binary_text(self):
        Instruction = Instructions.generate_instruction(self)
        instruction_text = ""
        # Loop through all the timeslices and put the instruction with the most significant bit set to 1 be the last operation instruction
        for timeslice in Instruction.instructions:
            if Instruction.instructions[timeslice].Operation_last != "":
                for gate in Instruction.instructions[timeslice].instructions:
                    # Skip the last operation instruction
                    if gate == Instruction.instructions[timeslice].Operation_last:
                        continue
                    for i in range(len(Instruction.instructions[timeslice].instructions[gate])):
                        if gate == "control_gate_no_condition" or gate == "control_gate_condition" or gate == "single_gate_condition":
                            for j in range(len(Instruction.instructions[timeslice].instructions[gate][i])): 
                                instr = Instructions.GetBinary(Instruction.instructions[timeslice].instructions[gate][i][j], Instructions.N_instr_bits)
                                instruction_text += instr + "\n"
                        else:
                            instr = Instructions.GetBinary(Instruction.instructions[timeslice].instructions[gate][i], Instructions.N_instr_bits)
                            instruction_text += instr + "\n"
                # Add the last operation instruction
                # for the gate operation that has multiple kinds of instructions, add the last kind at the end
                if Instruction.instructions[timeslice].Operation_last in {"control_gate_no_condition", "control_gate_condition", "single_gate_condition"}:
                    for j in range(len(Instruction.instructions[timeslice].instructions[Instruction.instructions[timeslice].Operation_last])):
                        # Skip the last operation kind 
                        if j == Instruction.instructions[timeslice].Operation_last_kind:
                            continue
                        for k in range(len(Instruction.instructions[timeslice].instructions[Instruction.instructions[timeslice].Operation_last][j])): 
                                instr = Instructions.GetBinary(Instruction.instructions[timeslice].instructions[Instruction.instructions[timeslice].Operation_last][j][k], Instructions.N_instr_bits)
                                instruction_text += instr + "\n"
                    # Add the last operation kind
                    for k in range(len(Instruction.instructions[timeslice].instructions[Instruction.instructions[timeslice].Operation_last][Instruction.instructions[timeslice].Operation_last_kind])):
                        instr = Instructions.GetBinary(Instruction.instructions[timeslice].instructions[Instruction.instructions[timeslice].Operation_last]\
                            [Instruction.instructions[timeslice].Operation_last_kind][k], Instructions.N_instr_bits)
                        instruction_text += instr + "\n"
                else:
                    for j in range(len(Instruction.instructions[timeslice].instructions[Instruction.instructions[timeslice].Operation_last])):
                        instr = Instructions.GetBinary(Instruction.instructions[timeslice].instructions[Instruction.instructions[timeslice].Operation_last][j], Instructions.N_instr_bits)
                        instruction_text += instr + "\n"
        # Get the name of the file from quantum circuit
        file_name = self.name+"_instr_bin.txt"
        with open(file_name, 'w') as file:
            file.write(instruction_text)
            
    # Generate the instruction for the quantum circuit and store the binary representation into the .bin file
    def to_binary_bin(self):
        Instruction = Instructions.generate_instruction(self)
        with open(self.name+'_instr_bin.bin', 'wb') as file:
            # Loop through all the timeslices and put the instruction with the most significant bit set to 1 be the last operation instruction
            for timeslice in Instruction.instructions:
                if Instruction.instructions[timeslice].Operation_last != "":
                    for gate in Instruction.instructions[timeslice].instructions:
                        # Skip the last operation instruction
                        if gate == Instruction.instructions[timeslice].Operation_last:
                            continue
                        for i in range(len(Instruction.instructions[timeslice].instructions[gate])):
                            if gate == "control_gate_no_condition" or gate == "control_gate_condition" or gate == "single_gate_condition":
                                for j in range(len(Instruction.instructions[timeslice].instructions[gate][i])): 
                                    file.write(struct.pack('<q', Instruction.instructions[timeslice].instructions[gate][i][j]))
                            else:
                                # For negative value(parameters), using signed long long type
                                format_str = '<q' if Instruction.instructions[timeslice].instructions[gate][i] <0 else '<Q'
                                file.write(struct.pack(format_str, Instruction.instructions[timeslice].instructions[gate][i]))
                    # Add the last operation instruction
                    # for the gate operation that has multiple kinds of instructions, add the last kind at the end
                    if Instruction.instructions[timeslice].Operation_last in {"control_gate_no_condition", "control_gate_condition", "single_gate_condition"}:
                        for j in range(len(Instruction.instructions[timeslice].instructions[Instruction.instructions[timeslice].Operation_last])):
                            # Skip the last operation kind 
                            if j == Instruction.instructions[timeslice].Operation_last_kind:
                                continue
                            for k in range(len(Instruction.instructions[timeslice].instructions[Instruction.instructions[timeslice].Operation_last][j])): 
                                format_str = '<q' if Instruction.instructions[timeslice].instructions[Instruction.instructions[timeslice].Operation_last][j][k] <0 else '<Q'
                                file.write(struct.pack(format_str, Instruction.instructions[timeslice].instructions[Instruction.instructions[timeslice].Operation_last][j][k]))
                        # Add the last operation kind
                        for k in range(len(Instruction.instructions[timeslice].instructions[Instruction.instructions[timeslice].Operation_last][Instruction.instructions[timeslice].Operation_last_kind])):
                            format_str = '<q' if Instruction.instructions[timeslice].instructions[Instruction.instructions[timeslice].Operation_last][Instruction.instructions[timeslice].Operation_last_kind][k] <0 else '<Q'
                            file.write(struct.pack(format_str, Instruction.instructions[timeslice].instructions[Instruction.instructions[timeslice].Operation_last][Instruction.instructions[timeslice].Operation_last_kind][k]))
                    else:
                        for j in range(len(Instruction.instructions[timeslice].instructions[Instruction.instructions[timeslice].Operation_last])):
                            format_str = '<q' if Instruction.instructions[timeslice].instructions[Instruction.instructions[timeslice].Operation_last][j] <0 else '<Q'
                            file.write(struct.pack(format_str, Instruction.instructions[timeslice].instructions[Instruction.instructions[timeslice].Operation_last][j]))
    
    #================================================================================================
    # The following functions are used for testing
    #================================================================================================
    # Define the function to print the generated instructions of each timeslice of each type of operation for testing
    def test_instruction(self):
        Instruction = Instructions.generate_instruction(self)
        idx = 1
        for timeslice in Instruction.instructions:
            if Instruction.instructions[timeslice].Operation_last != "":
                print(f"Timeslice {idx}:")
                for gate in Instruction.instructions[timeslice].instructions:
                    print(gate)
                    for i in range(len(Instruction.instructions[timeslice].instructions[gate])):
                        if gate == "control_gate_no_condition" or gate == "control_gate_condition" or gate == "single_gate_condition":
                            for j in range(len(Instruction.instructions[timeslice].instructions[gate][i])): 
                                instr = Instructions.GetBinary(Instruction.instructions[timeslice].instructions[gate][i][j], Instructions.N_instr_bits)
                                print(instr)
                        else:
                            instr = Instructions.GetBinary(Instruction.instructions[timeslice].instructions[gate][i], Instructions.N_instr_bits)
                            print(instr)
                idx += 1
        print(Instruction.N_qubit_bits)
            
    # Define the function to draw the draft quantum circuit for testing
    def test_draw(self):
        circuit_str = " "*(len(str(int(self.max_time_slice)))+2)
        qubit_pos = []
        pos = len(circuit_str)
        for qubit in self.qubits:
            circuit_str += qubit + "               "
            qubit_pos.append(pos)
            pos += len(qubit+"               ")
        idx = 0
        for i in range(1, self.max_time_slice+1):
            idx = idx if self.check_empty_timeslice(i) else idx+1
            if self.check_empty_timeslice(i):
                continue
            circuit_str += "\n"+" "*(len(str(int(self.max_time_slice)))+2)
            circuit_str += "|"
            for j in range(1, len(qubit_pos)):
                circuit_str += " " *(qubit_pos[j]-qubit_pos[j-1]-1) + "|"
            circuit_str += "\n"
            circuit_str += f"{idx}:"+" "*(qubit_pos[0]-len(str(i))-1)
            pos_idx = 0
            operation_len = 1
            for qubit in self.qubits:
                if f"timeslice_{i}" in self.qubits[qubit]:
                    if_str = ""
                    # Check if the current qubit is under the if condition
                    if self.qubits[qubit][f"timeslice_{i}"].if_flag:
                        if_str = f"|{self.qubits[qubit][f'timeslice_{i}'].if_creg}={self.qubits[qubit][f'timeslice_{i}'].if_num}"
                    if pos_idx == 0:
                        # Check for the reset operation
                        if self.qubits[qubit][f"timeslice_{i}"].reset:
                            circuit_str += "reset"+if_str
                            operation_len = 5 + len(if_str)
                        # Check for the measurement operation
                        elif self.qubits[qubit][f"timeslice_{i}"].measurement:
                            creg = self.qubits[qubit][f"timeslice_{i}"].connected_cregs
                            creg_names = f"{', '.join(map(str, creg))}"
                            circuit_str += "M -> "+creg_names + if_str
                            operation_len = len(creg_names)+5+len(if_str)
                        # Check for the controlled operation
                        elif self.qubits[qubit][f"timeslice_{i}"].controlled_operation:
                            if self.qubits[qubit][f"timeslice_{i}"].target_qubit:
                                gate_name = self.qubits[qubit][f"timeslice_{i}"].gate_operation
                                parameter = self.qubits[qubit][f"timeslice_{i}"].parameters
                                name = f"{gate_name}({', '.join(map(str, parameter))})" if self.qubits[qubit][f"timeslice_{i}"].with_parameter else gate_name
                                circuit_str += name+" o"+if_str
                                operation_len = len(name)+2+len(if_str)
                            else:
                                gate_name = self.qubits[qubit][f"timeslice_{i}"].gate_operation
                                parameter = self.qubits[qubit][f"timeslice_{i}"].parameters
                                name = f"{gate_name}({', '.join(map(str, parameter))})" if self.qubits[qubit][f"timeslice_{i}"].with_parameter else gate_name
                                circuit_str += name+" "+self.qubits[qubit][f"timeslice_{i}"].connected_qubits[0]+if_str
                                operation_len = len(name)+len(self.qubits[qubit][f"timeslice_{i}"].connected_qubits[0])+1+len(if_str)
                        else:
                            gate_name = self.qubits[qubit][f"timeslice_{i}"].gate_operation
                            parameter = self.qubits[qubit][f"timeslice_{i}"].parameters
                            name = f"{gate_name}({', '.join(map(str, parameter))})" if self.qubits[qubit][f"timeslice_{i}"].with_parameter else gate_name
                            circuit_str += name+if_str
                            operation_len = len(name)+len(if_str)
                    else:
                        # Check for the reset operation
                        if self.qubits[qubit][f"timeslice_{i}"].reset:
                            circuit_str += " " *(qubit_pos[pos_idx]-qubit_pos[pos_idx-1]-operation_len) + "reset"+if_str
                            operation_len = 5+len(if_str)
                        # Check for the measurement operation
                        elif self.qubits[qubit][f"timeslice_{i}"].measurement:
                            creg = self.qubits[qubit][f"timeslice_{i}"].connected_cregs
                            creg_names = f"{', '.join(map(str, creg))}"
                            circuit_str += " " *(qubit_pos[pos_idx]-qubit_pos[pos_idx-1]-operation_len) + "M -> "+creg_names+if_str
                            operation_len = len(creg_names)+5+len(if_str)
                        # Check for the controlled operations
                        elif self.qubits[qubit][f"timeslice_{i}"].controlled_operation:
                            if self.qubits[qubit][f"timeslice_{i}"].target_qubit:
                                gate_name = self.qubits[qubit][f"timeslice_{i}"].gate_operation
                                parameter = self.qubits[qubit][f"timeslice_{i}"].parameters
                                name = f"{gate_name}({', '.join(map(str, parameter))})" if self.qubits[qubit][f"timeslice_{i}"].with_parameter else gate_name
                                circuit_str += " " *(qubit_pos[pos_idx]-qubit_pos[pos_idx-1]-operation_len)+name+" o"+if_str
                                operation_len = len(name)+2+len(if_str)
                            else:
                                gate_name = self.qubits[qubit][f"timeslice_{i}"].gate_operation
                                parameter = self.qubits[qubit][f"timeslice_{i}"].parameters
                                name = f"{gate_name}({', '.join(map(str, parameter))})" if self.qubits[qubit][f"timeslice_{i}"].with_parameter else gate_name
                                circuit_str += " " *(qubit_pos[pos_idx]-qubit_pos[pos_idx-1]-operation_len)+name+" "+self.qubits[qubit][f"timeslice_{i}"].connected_qubits[0]+if_str
                                operation_len = len(name)+len(self.qubits[qubit][f"timeslice_{i}"].connected_qubits[0])+1+len(if_str)
                        else:
                            gate_name = self.qubits[qubit][f"timeslice_{i}"].gate_operation
                            parameter = self.qubits[qubit][f"timeslice_{i}"].parameters
                            name = f"{gate_name}({', '.join(map(str, parameter))})" if self.qubits[qubit][f"timeslice_{i}"].with_parameter else gate_name
                            circuit_str += " " *(qubit_pos[pos_idx]-qubit_pos[pos_idx-1]-operation_len) + name + if_str
                            operation_len = len(name)+len(if_str)
                else:
                    if pos_idx == 0:
                        circuit_str += " "
                        operation_len = 1
                    else:
                        circuit_str += " " *(qubit_pos[pos_idx]-qubit_pos[pos_idx-1]-operation_len) + " "
                        operation_len = 1
                pos_idx += 1
        print(circuit_str)
    
    # Helper function to check whether the current timeslice contains no operation
    def check_empty_timeslice(self, timeslice_idx):
        for qubit in self.qubits:
            if f"timeslice_{timeslice_idx}" in self.qubits[qubit]:
                return False
        return True

filepath = "IR/QASM2/Examples/test_instruction_control_condition.qasm"
# filepath = "IR/QASM2/Examples/iqft.qasm"
# filepath = "test_instruction_single_condition.qasm"
QC = Quantum_circuit.from_qasm2(filepath)
QC.test_draw()
QC.test_instruction()
QC.to_binary_text()
QC.to_binary_bin()