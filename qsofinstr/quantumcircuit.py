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
    "CU": 3
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
                self.qubits[qubit_name + f"[{i}]"] = {} # the value of each qubit is a dictionary, where key is timeslice and value is the timeslice node
    
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
    
    # Add a new no parameter single qubit gate to the circuit
    def add_single_qubit_gate_no_parameter(self, gate_name, qubit_name, index=-1, if_creg=None, if_num=0, if_flag=False):
        qubit = qubit_name + f"[{index}]" if index != -1 else qubit_name
        time_slice = self.qubit_max_time_slice[qubit] + 1
        self.qubit_max_time_slice[qubit] = time_slice
        time_slice_node = Time_slice_node(gate_name)
        time_slice_node.time_slice_index = time_slice
        # Check if the gate is conditioned
        if if_flag:
            if_creg_name = if_creg[0] + f"[{if_creg[1]}]" if if_creg[1] != -1 else if_creg[0]
            time_slice_node.if_flag = True
            time_slice_node.if_num = if_num
            time_slice_node.if_creg = if_creg_name
        self.qubits[qubit][f"timeslice_{time_slice}"] = time_slice_node
        self.max_time_slice = max(self.max_time_slice, time_slice)  
    
    # Add a new single qubit gate with parameter to the circuit
    def add_single_qubit_gate_with_parameter(self, gate_name, qubit_name, parameter, index = -1, if_creg=None, if_num=0, if_flag=False):
        qubit = qubit_name + f"[{index}]" if index != -1 else qubit_name
        time_slice = self.qubit_max_time_slice[qubit] + 1
        self.qubit_max_time_slice[qubit] = time_slice
        time_slice_node = Time_slice_node(gate_name)
        time_slice_node.with_parameter = True
        time_slice_node.time_slice_index = time_slice
        time_slice_node.add_parameter(parameter)
        if if_flag:
            if_creg_name = if_creg[0] + f"[{if_creg[1]}]" if if_creg[1] != -1 else if_creg[0]
            time_slice_node.if_flag = True
            time_slice_node.if_num = if_num
            time_slice_node.if_creg = if_creg_name
        self.qubits[qubit][f"timeslice_{time_slice}"] = time_slice_node
        self.max_time_slice = max(self.max_time_slice, time_slice)
    
    # Add a new controlled single qubit gate without parameter to the circuit
    def add_controlled_gate_no_parameter(self, gate_name, control_qubit, target_qubit, target_index=-1, if_creg=None, if_num=0, if_flag=False):
        if_creg_name = ""
        if_creg_num = 0
        if if_flag:
            if_creg_name = if_creg[0] + f"[{if_creg[1]}]" if if_creg[1] != -1 else if_creg[0]
            if_creg_num = if_num
        # create a new list that stores all the qubit names, the first element is the target qubit
        qubit_names = [target_qubit + f"[{target_index}]" if target_index != -1 else target_qubit]
        # add the control qubit to the list and find the maximum timeslice index
        max_time_slice = self.qubit_max_time_slice[qubit_names[0]]
        for i in range(len(control_qubit)):
            qubit_name = control_qubit[i][0]+f"[{control_qubit[i][1]}]" if control_qubit[i][1] != -1 else control_qubit[i][0]
            qubit_names.append(qubit_name)
            if self.qubit_max_time_slice[qubit_name] > max_time_slice:
                max_time_slice = self.qubit_max_time_slice[qubit_name]
        # Add 1 to the maximum timeslice index to get the current timeslice index
        max_time_slice += 1
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
            self.qubits[qubit][f"timeslice_{max_time_slice}"] = time_slice_node_control
        # Update the maximum timeslice index of the circuit
        self.max_time_slice = max(self.max_time_slice, max_time_slice)
    
    # Add a new controlled single qubit gate with parameter to the circuit
    def add_controlled_gate_with_parameter(self, gate_name, control_qubit, target_qubit, parameter, target_index=-1, if_creg=None, if_num=0, if_flag=False):
        if_creg_name = ""
        if_creg_num = 0
        if if_flag:
            if_creg_name = if_creg[0] + f"[{if_creg[1]}]" if if_creg[1] != -1 else if_creg[0]
            if_creg_num = if_num
        # create a new list that stores all the qubit names, the first element is the target qubit
        qubit_names = [target_qubit + f"[{target_index}]" if target_index != -1 else target_qubit]
        # add the control qubit to the list and find the maximum timeslice index
        max_time_slice = self.qubit_max_time_slice[qubit_names[0]]
        for i in range(len(control_qubit)):
            qubit_name = control_qubit[i][0]+f"[{control_qubit[i][1]}]" if control_qubit[i][1] != -1 else control_qubit[i][0]
            qubit_names.append(qubit_name)
            if self.qubit_max_time_slice[qubit_name] > max_time_slice:
                max_time_slice = self.qubit_max_time_slice[qubit_name]
        # Add 1 to the maximum timeslice index to get the current timeslice index
        max_time_slice += 1
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
            self.qubits[qubit][f"timeslice_{max_time_slice}"] = time_slice_node_control
        # Update the maximum timeslice index of the circuit
        self.max_time_slice = max(self.max_time_slice, max_time_slice)
    
    # Add the measurement operation to the circuit
    def add_measurement(self, qubit, creg, if_creg=None, if_num=0, if_flag=False):
        max_time_slice = 0
        qubit_names = []
        creg_names = []
        if_creg_name = ""
        if_creg_num = 0
        if if_flag:
            if_creg_name = if_creg[0] + f"[{if_creg[1]}]" if if_creg[1] != -1 else if_creg[0]
            if_creg_num = if_num
        for i in range(len(qubit)):
            # Get the qubit name and the creg name
            qubit_name = qubit[i][0] + f"[{qubit[i][1]}]" if qubit[i][1] != -1 else qubit[i][0]
            creg_name = creg[i][0] + f"[{creg[i][1]}]" if creg[i][1] != -1 else creg[i][0]
            qubit_names.append(qubit_name)
            creg_names.append(creg_name)
            # Set the maximum timeslice index for the current qubit
            time_slice = self.qubit_max_time_slice[qubit_name] + 1
            max_time_slice = time_slice if time_slice > max_time_slice else max_time_slice
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
        if if_flag:
            if_creg_name = if_creg[0] + f"[{if_creg[1]}]" if if_creg[1] != -1 else if_creg[0]
            if_creg_num = if_num
        for i in range(len(qubit)):
            # Get the qubit name
            qubit_name = qubit[i][0] + f"[{qubit[i][1]}]" if qubit[i][1] != -1 else qubit[i][0]
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
            qubit_name = qubit[i][0] + f"[{qubit[i][1]}]" if qubit[i][1] != -1 else qubit[i][0]
            qubit_names.append(qubit_name)
            # Set the maximum timeslice index for the current qubit
            time_slice = self.qubit_max_time_slice[qubit_name] + 1
            max_time_slice = time_slice if time_slice > max_time_slice else max_time_slice
        for i in range(len(qubit_names)):
            self.qubit_max_time_slice[qubit_names[i]] = max_time_slice
            # Create a new timeslice node for the current qubit
            time_slice_node = Time_slice_node("BARRIER")
            time_slice_node.time_slice_index = max_time_slice
            # Add the new timeslice node to the circuit
            self.qubits[qubit_names[i]][f"timeslice_{max_time_slice}"] = time_slice_node
            # Set the maximum timeslice index for the circuit
        self.max_time_slice = max(self.max_time_slice, max_time_slice)
        
    
    # Define the function to draw the draft quantum circuit for testing
    def test_draw(self):
        circuit_str = " "*(len(str(int(self.max_time_slice)))+2)
        qubit_pos = []
        pos = len(circuit_str)
        for qubit in self.qubits:
            circuit_str += qubit + "               "
            qubit_pos.append(pos)
            pos += len(qubit+"               ")
        for i in range(1, self.max_time_slice+1):
            circuit_str += "\n"+" "*(len(str(int(self.max_time_slice)))+2)
            circuit_str += "|"
            for j in range(1, len(qubit_pos)):
                circuit_str += " " *(qubit_pos[j]-qubit_pos[j-1]-1) + "|"
            circuit_str += "\n"
            circuit_str += f"{i}:"+" "*(qubit_pos[0]-len(str(i))-1)
            pos_idx = 0
            operation_len = 1
            for qubit in self.qubits:
                if f"timeslice_{i}" in self.qubits[qubit]:
                    if_str = ""
                    # Check if the current qubit is under the if condition
                    if self.qubits[qubit][f"timeslice_{i}"].if_flag:
                        if_str = f" |{self.qubits[qubit][f'timeslice_{i}'].if_creg}={self.qubits[qubit][f'timeslice_{i}'].if_num}"
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