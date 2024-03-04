'''
This file contains the class to represent the timeslice node of the quantum circuit, which is used to store the information of the quantum operation
for the specific qubit in the specific timeslice. Therefore, the timeslice node has the information of which gate is applied, the parameters associated 
with the gate, its corresponding timeslice index, the qubits and classical registers that this qubit is connected to at this timeslice, and some other flags
indicating whether the gate is under a classical condition or a measurement operation, etc.
'''
# The number requirement table for parameters of basic gates that need parameters
Param_Num_Table = {
    "RTHETA": 1,
    "RX": 1,
    "RY": 1,
    "RZ": 1,
    "U": 3,
    "CRTHETA": 1,
    "CRX": 1,
    "CRY": 1,
    "CRZ": 1,
    "CU": 3,
    "U1": 1,
    "U2": 2,
    "CU1": 1
}

# The table for current supported opaques in QSoF
Opaque_Table = {
    "mixamp": 1,
    "mixphase": 1
}
class Time_slice_node:
    def __init__(self, gate_operation):
        self.gate_operation = gate_operation
        self.controlled_operation = False
        self.connected_qubits = []
        self.connected_cregs = []
        self.parameters = []
        self.target_qubit = True
        self.time_slice_index = 0
        self.with_parameter = False # Flag to indicate if the gate has parameter
        self.measurement = False # Flag to indicate if the gate is a measurement operation
        self.reset = False # Flag to indicate if the gate is a reset operation
        self.if_flag = False # Flag to indicate if the gate is conditioned
        self.if_creg = "" # The name of the creg that is used to condition the gate
        self.if_num = 0 # The number of the condition
        self.if_kind = 0 # The kind of the condition, 0 for single bit == val, 1 for creg == val
        self.barrier = False # Flag to indicate if the gate is a barrier operation
    
    def add_connected_qubit(self, qubits):
        if isinstance(qubits, list):
            self.connected_qubits.extend(qubits)
        else:
            self.connected_qubits.append(qubits)
    
    def add_parameter(self, parameter):
        if isinstance(parameter, list):
            self.parameters.extend(parameter)
        else:
            self.parameters.append(parameter)
    