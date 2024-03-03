'''
This file contains the functions for hardware specification, which is used to modify the quantumcircuit to satisfy the 
requirements of the FPGA implementation. For now the FPGA implementation of QSoF doesn't support the parallel execution of the quantum operation
with matrix representation having off-diagonal elements. Therefore, there should only be one Rx, Ry, or H gate in each timeslice because a new
state will be generated by these gates. The hardware specification is mainly used to put these gates into different timeslices in the most
optimized way. The basic logic is to modify the timeslice index of the quantum operation based on the hardware specifications. There are two modes
now, mode 1 is to put the off-diagonal gates into different timeslices but non-off-diagonal gates can be put into the same timeslice with these 
off-diagonal gates. Mode 2 is to put an off-diagonal gate into an individual timeslice, so this timeslice only has this off-diagonal operation. 
Mode 1 could generate less instructions and make sure that maximum number of operations can be executed in parallel. Mode 2 may generate more 
instructions but for all the off-diagonal gates, the only gate that needs to be executed in the timeslice is the off-diagonal gate itself, since
the hardware architecture is a circular architecture with the timeslices will be executed circularly. And since the off-diagonal gates will generate
new states, the stalls happened for hardwware, therefore mode 2 could make hardware implementation easier. The choice of mode depends on the exact
comparison between the latency of the hardware implementation as well as the complexity of the control logic, which will be determined later.
'''
from timeslice import Time_slice_node

class Specification:
    # The flag to indicate whether the hardware specification is needed, which is set to False by default and can be changed through command line
    Need = True
    # The flag to indicate the mode of the hardware specification, which is set to 1 by default and can be changed through command line
    Mode = 1
    Offdiag_Gates = {
        "rx",
        "ry",
        "h",
        "crx",
        "cry",
        "ch"
    }

    def __init__(self):
        # This dictionary is to store the additional timeslice indexes for each qubit for mode 1
        # For mode 2, this is used to store the new timeslice indexes of each original timeslice index
        self.additional_timeslice = {}
        # The dictionary to store how many off-diagonal gates are appeared in each timeslice
        self.offdiag_gate_count = {}
        # The variable to store the maximum measurement timeslice
        self.max_measurement_timeslice = 0
        # The variable to indicate the new maximum timeslice index
        self.new_max_timeslice = 0
        # The dictionary to store the list of the connected qubits for controlled off-diagonal gates in each timeslice
        # each element of the list is a set containing the connected qubits
        self.off_diag_contr_connected = {}
        # The dictionary to store the how many off-diagonal controlled gates are appeared in each timeslice
        self.off_diag_contr_count = {}
        # The variable to store the current maximum timeslice index of all the appeared off-diagonal operations
        self.offdiag_max_timeslice = 0
    
    @staticmethod
    def update_offdiag_gate_count(timeslice_idx, spec, timeslice_node, qubit):
        if timeslice_idx not in spec.offdiag_gate_count:
            spec.offdiag_gate_count[timeslice_idx] = 0
        if timeslice_idx not in spec.off_diag_contr_connected:
            spec.off_diag_contr_connected[timeslice_idx] = []
            spec.off_diag_contr_count[timeslice_idx] = []
        if timeslice_node.gate_operation in Specification.Offdiag_Gates:
            # If the gate is not a controlled gate
            if not timeslice_node.controlled_operation:
                spec.offdiag_gate_count[timeslice_idx] += 1
                spec.total_offdiag_gate_count += 1
                return spec.offdiag_gate_count[timeslice_idx]
                # return spec.offdiag_gate_count[timeslice_idx]
            else:
                # Check whether the current qubit is the connected qubit in the list
                idx = -1
                for i in range(len(spec.off_diag_contr_connected[timeslice_idx])):
                    if qubit in spec.off_diag_contr_connected[timeslice_idx][i]:
                        idx = i
                        break
                # If the current qubit is not in the list, add a new set to the list and set the off_diag_contr_count to offdiag_gate_count plus 1
                if idx == -1:
                    spec.off_diag_contr_connected[timeslice_idx].append(set(timeslice_node.connected_qubits))
                    spec.offdiag_gate_count[timeslice_idx] += 1
                    spec.off_diag_contr_count[timeslice_idx].append(spec.offdiag_gate_count[timeslice_idx])
                    return spec.offdiag_gate_count[timeslice_idx]
                else:
                    # If the current qubit is in the list, its offdiag gate count should be the same as its connected qubits
                    return spec.off_diag_contr_count[timeslice_idx][idx]
        return spec.offdiag_gate_count[timeslice_idx]
    
    @staticmethod
    def update_max_measurement_timeslice(timeslice_idx, spec, timeslice_node, additional_index):
        if timeslice_node.measurement:
            spec.max_measurement_timeslice = max(spec.max_measurement_timeslice, timeslice_idx+additional_index)
        return
    
    @staticmethod
    def update_additional_timeslice_controlled(spec, timeslice_node, additional_index, quantumcircuit):
        if timeslice_node.controlled_operation:
            # Find the maximum additional timeslice index among all the connected qubits of the controlled gate
            max_additional_index = additional_index
            for q in timeslice_node.connected_qubits:
                max_additional_index = max(max_additional_index, spec.additional_timeslice[q])
            # print(max_additional_index)
            return max_additional_index
        else:
            return additional_index
    
    @staticmethod
    def update_additional_timeslice_condition(timeslice_idx, spec, timeslice_node, additional_index):
        if timeslice_node.if_flag:
            return max(additional_index, spec.max_measurement_timeslice+1-timeslice_idx)
        else:
            return additional_index
    
    @staticmethod
    def update_timeslice_idx_mode1(timeslice_idx, spec, timeslice_node, qubit, quantumcircuit):
        # Update the off-diagonal gate count
        # offdiag_count = Specification.update_offdiag_gate_count(timeslice_idx, spec, timeslice_node, qubit)
        additional_timeslice_idx = 0
        if timeslice_node.gate_operation in Specification.Offdiag_Gates:
            if not timeslice_node.controlled_operation:
                additional_timeslice_idx = spec.additional_timeslice[qubit] if timeslice_idx > spec.offdiag_max_timeslice else spec.offdiag_max_timeslice-timeslice_idx+1
            else:
                if timeslice_idx not in spec.off_diag_contr_connected:
                    spec.off_diag_contr_connected[timeslice_idx] = []
                    spec.off_diag_contr_count[timeslice_idx] = []
                idx = -1
                for i in range(len(spec.off_diag_contr_connected[timeslice_idx])):
                    if qubit in spec.off_diag_contr_connected[timeslice_idx][i]:
                        idx = i
                        break
                if idx == -1:
                    spec.off_diag_contr_connected[timeslice_idx].append(set(timeslice_node.connected_qubits))
                    additional_timeslice_idx = spec.additional_timeslice[qubit] if timeslice_idx > spec.offdiag_max_timeslice else spec.offdiag_max_timeslice-timeslice_idx+1
                    spec.off_diag_contr_count[timeslice_idx].append(additional_timeslice_idx+timeslice_idx)
                else:
                    # If the current qubit is in the list, its offdiag gate count should be the same as its connected qubits
                    additional_timeslice_idx = spec.off_diag_contr_count[timeslice_idx][idx]-timeslice_idx
        else:
            additional_timeslice_idx = spec.additional_timeslice[qubit]
        # Add the qubit to the additional timeslice dictionary if it's not in the dictionary
        if qubit not in spec.additional_timeslice:
            spec.additional_timeslice[qubit] = 0
        # Update the maximum measurement 
        Specification.update_max_measurement_timeslice(timeslice_idx, spec, timeslice_node, additional_timeslice_idx)
        # Update the additional timeslice index for controlled gates
        additional_timeslice_idx = Specification.update_additional_timeslice_controlled(spec, timeslice_node, additional_timeslice_idx, quantumcircuit)
        # Update the additional timeslice index for classical conditioned quantum operations
        additional_timeslice_idx = Specification.update_additional_timeslice_condition(timeslice_idx, spec, timeslice_node, additional_timeslice_idx)
        # Update the additional timeslice index for the qubit
        spec.additional_timeslice[qubit] = additional_timeslice_idx
        # Update the new maximum timeslice index
        spec.new_max_timeslice = max(spec.new_max_timeslice, timeslice_idx+additional_timeslice_idx)
        if timeslice_node.gate_operation in Specification.Offdiag_Gates:
            spec.offdiag_max_timeslice = max(spec.offdiag_max_timeslice, timeslice_idx+additional_timeslice_idx)
        # Update the timeslice index 
        return timeslice_idx + additional_timeslice_idx
    
    # Define the function to update the timeslice index for mode 2
    @staticmethod
    def update_timeslice_idx_mode2(timeslice_idx, spec, timeslice_node, qubit):
        # Check whether the current timeslice index first appears
        if timeslice_idx not in spec.additional_timeslice:
            spec.additional_timeslice[timeslice_idx] = spec.offdiag_max_timeslice+1
        # For the off-diagonal gates, the timeslice needs to be changed
        if timeslice_node.gate_operation in Specification.Offdiag_Gates:
            if not timeslice_node.controlled_operation:
                spec.offdiag_max_timeslice += 1
                # Update the new maximum timeslice index of the new quantum circuit
                spec.new_max_timeslice = max(spec.new_max_timeslice, spec.offdiag_max_timeslice)
                return spec.offdiag_max_timeslice
            else:
                # Check whether the current qubit is the connected qubit in the list
                if timeslice_idx not in spec.off_diag_contr_connected:
                    spec.off_diag_contr_connected[timeslice_idx] = []
                    spec.off_diag_contr_count[timeslice_idx] = []
                idx = -1
                for i in range(len(spec.off_diag_contr_connected[timeslice_idx])):
                    if qubit in spec.off_diag_contr_connected[timeslice_idx][i]:
                        idx = i
                        break
                # For the first appeared controlled off-diagonal gate, the timeslice is the next of the maximum offdiag timeslice
                if idx == -1:
                    # Add the connected qubits to the list
                    spec.off_diag_contr_connected[timeslice_idx].append(set(timeslice_node.connected_qubits))
                    spec.offdiag_max_timeslice += 1
                    # Add the timeslice index of this controlled operation to the list
                    spec.off_diag_contr_count[timeslice_idx].append(spec.offdiag_max_timeslice)
                    spec.new_max_timeslice = max(spec.new_max_timeslice, spec.offdiag_max_timeslice)
                    return spec.offdiag_max_timeslice
                # For the qubit with its controlled off-diagonal gate appeared before, the timeslice is the same as its connected qubits
                else:
                    spec.new_max_timeslice = max(spec.new_max_timeslice, spec.offdiag_max_timeslice)
                    return spec.off_diag_contr_count[timeslice_idx][idx]
        # For the non-off-diagonal gates, the timeslice index is the new timeslice index of the original timeslice
        else:
            spec.offdiag_max_timeslice = spec.additional_timeslice[timeslice_idx]
            spec.new_max_timeslice = max(spec.new_max_timeslice, spec.offdiag_max_timeslice)
            return spec.additional_timeslice[timeslice_idx]
    
    # This decorator is used for directly applying hardware specification on instruction generation instead of one quantumcircuit
    @staticmethod
    def HardwareSpecification(func):
        def wrapper(*args, **kwargs):
            if Specification.Need:
                input_args = list(args)
                # Get the timeslice index
                timeslice_idx = input_args[1]
                # Get the specification instance
                spec = input_args[len(input_args)-1]
                # Get the timeslice node
                timeslice_node = input_args[3]
                # Get the quantum circuit instance
                quantumcircuit = input_args[5]
                # Get the qubit
                qubit = input_args[2]
                # Update the timeslice index 
                input_args[1] = Specification.update_timeslice_idx_mode1(timeslice_idx, spec, timeslice_node, qubit, quantumcircuit)
                # Call the original function with the modified input
                return func(*input_args, **kwargs)
            else:
                return func(*args, **kwargs)
        return wrapper
    
    @staticmethod
    def create_specified_quantumcircuit(quantumcircuit_orig, quantumcircuit_new, spec):
        # First setup the additional timeslice dictionary
        spec.additional_timeslice = {qubit: 0 for qubit in quantumcircuit_orig.qubits}
        # Copy all the basic attributes to the new quantumcircuit except for the timeslice node dictionary
        quantumcircuit_new.name = quantumcircuit_orig.name
        quantumcircuit_new.cregs = quantumcircuit_orig.cregs
        quantumcircuit_new.cregs_size = quantumcircuit_orig.cregs_size
        quantumcircuit_new.qubits_idx = quantumcircuit_orig.qubits_idx
        quantumcircuit_new.cregs_idx = quantumcircuit_orig.cregs_idx
        quantumcircuit_new.qubits_idx_idx = quantumcircuit_orig.qubits_idx_idx
        quantumcircuit_new.cregs_idx_idx = quantumcircuit_orig.cregs_idx_idx
        # Create the empty timeslice node dictionary using the same qubit names
        quantumcircuit_new.qubits = {qubit: {} for qubit in quantumcircuit_orig.qubits}
        # Loop through all the qubits of all timeslices to create the new timeslice node dictionary for the new quantumcircuit
        for timeslice_idx in range(1, quantumcircuit_orig.max_time_slice+1):
            for qubit in quantumcircuit_orig.qubits:
                if f"timeslice_{timeslice_idx}" in quantumcircuit_orig.qubits[qubit]:
                    idx = 0
                    if Specification.Mode == 1:
                        # Update the timeslice index for mode 1
                        idx = Specification.update_timeslice_idx_mode1(timeslice_idx, spec, quantumcircuit_orig.qubits[qubit][f"timeslice_{timeslice_idx}"], qubit, quantumcircuit_orig)
                    else:
                        idx = Specification.update_timeslice_idx_mode2(timeslice_idx, spec, quantumcircuit_orig.qubits[qubit][f"timeslice_{timeslice_idx}"], qubit)
                    # Create the new timeslice node for the new quantumcircuit
                    new_timeslice_node = Time_slice_node(quantumcircuit_orig.qubits[qubit][f"timeslice_{timeslice_idx}"].gate_operation)
                    new_timeslice_node.controlled_operation = quantumcircuit_orig.qubits[qubit][f"timeslice_{timeslice_idx}"].controlled_operation
                    new_timeslice_node.connected_qubits = quantumcircuit_orig.qubits[qubit][f"timeslice_{timeslice_idx}"].connected_qubits
                    new_timeslice_node.connected_cregs = quantumcircuit_orig.qubits[qubit][f"timeslice_{timeslice_idx}"].connected_cregs
                    new_timeslice_node.parameters = quantumcircuit_orig.qubits[qubit][f"timeslice_{timeslice_idx}"].parameters
                    new_timeslice_node.target_qubit = quantumcircuit_orig.qubits[qubit][f"timeslice_{timeslice_idx}"].target_qubit
                    new_timeslice_node.time_slice_index = idx
                    new_timeslice_node.with_parameter = quantumcircuit_orig.qubits[qubit][f"timeslice_{timeslice_idx}"].with_parameter
                    new_timeslice_node.measurement = quantumcircuit_orig.qubits[qubit][f"timeslice_{timeslice_idx}"].measurement
                    new_timeslice_node.reset = quantumcircuit_orig.qubits[qubit][f"timeslice_{timeslice_idx}"].reset
                    new_timeslice_node.if_flag = quantumcircuit_orig.qubits[qubit][f"timeslice_{timeslice_idx}"].if_flag
                    new_timeslice_node.if_creg = quantumcircuit_orig.qubits[qubit][f"timeslice_{timeslice_idx}"].if_creg
                    new_timeslice_node.if_num = quantumcircuit_orig.qubits[qubit][f"timeslice_{timeslice_idx}"].if_num
                    new_timeslice_node.if_kind = quantumcircuit_orig.qubits[qubit][f"timeslice_{timeslice_idx}"].if_kind
                    # Add the new timeslice node to the new quantumcircuit
                    quantumcircuit_new.qubits[qubit][f"timeslice_{idx}"] = new_timeslice_node
        # Update the maximum timeslice index of the quantumcircuit_new
        quantumcircuit_new.max_time_slice = spec.new_max_timeslice
        # print(spec.additional_timeslice)
        # print(spec.offdiag_gate_count)
        # print(quantumcircuit_new.max_time_slice)
        