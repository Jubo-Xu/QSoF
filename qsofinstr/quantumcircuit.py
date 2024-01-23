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

class Time_slice_node:
    def __init__(self, gate_operation):
        self.gate_operation = gate_operation
        self.controlled_operation = False
        self.connected_qubits = []
        self.connected_cregs = []
        self.target_qubit = True
        self.time_slice_index = 0
    


class Quantum_circuit:
    def __init__(self):
        self.name = ""
        self.qubits = {}
        self.cregs = {}
        # This is an intermidiate variable to store the current maximum time slice index for each qubit 
        self.qubit_max_time_slice = {}
        self.max_time_slice = 0
    
    # Add a new qubit with the given name and size to the current circuit
    def add_qubit(self, qubit_name, size):
        if size == 1:
            self.qubits[qubit_name] = {}
        else:
            for i in range(size):
                self.qubits[qubit_name + f"[{i}]"] = {}
    
    def add_creg(self, creg_name, size):
        if size == 1:
            self.cregs[creg_name] = {}
        else:
            for i in range(size):
                self.cregs[creg_name + f"[{i}]"] = {}
    
    # Add the current maximum time slice index for the qubit 
    def add_qubit_max_time_slice(self, qubit_name, time_slice_index, size=1):
        if qubit_name not in self.qubit_max_time_slice:
            if size == 1:
                self.qubit_max_time_slice[qubit_name] = 0
            else:
                for i in range(size):
                    self.qubit_max_time_slice[qubit_name + f"[{i}]"] = 0
        else:
            if size == -1:
                self.qubit_max_time_slice[qubit_name] = time_slice_index
            else:
                self.qubit_max_time_slice[qubit_name + f"[{size}]"] = time_slice_index
    
    # Define the function to calculate the 
    def test_draw(self):
        circuit_str = "   "
        qubit_pos = []
        pos = len(circuit_str)
        for qubit in self.qubits:
            circuit_str += qubit + "  "
            qubit_pos.append(pos)
            pos += len(qubit+"  ")
        circuit_str += "\n   "
        circuit_str += "|"
        for i in range(1, len(qubit_pos)):
            circuit_str += " " *(qubit_pos[i]-qubit_pos[i-1]-1) + "|"
        
        print(circuit_str)