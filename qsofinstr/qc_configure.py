'''
This file contains the dumping and loading function of json file for the quantum circuit. Since the quantum circuit
is represented as a graph based data structure in QSoF, the quantum circuit can be dumped into a json file for interfaces
with other tools, and the quantum circuit itself can also be configured through a json file. 
'''
import json
from qsofinstr.timeslice import Time_slice_node

# The function to transfer the timeslice node to a dictionary
def timeslice_node_to_dict(timeslice_node):
    timeslice_node_dict = {}
    timeslice_node_dict["gate_operation"] = timeslice_node.gate_operation
    timeslice_node_dict["controlled_operation"] = timeslice_node.controlled_operation
    timeslice_node_dict["connected_qubits"] = timeslice_node.connected_qubits
    timeslice_node_dict["connected_cregs"] = timeslice_node.connected_cregs
    timeslice_node_dict["parameters"] = timeslice_node.parameters
    timeslice_node_dict["target_qubit"] = timeslice_node.target_qubit
    timeslice_node_dict["time_slice_index"] = timeslice_node.time_slice_index
    timeslice_node_dict["with_parameter"] = timeslice_node.with_parameter
    timeslice_node_dict["measurement"] = timeslice_node.measurement
    timeslice_node_dict["reset"] = timeslice_node.reset
    timeslice_node_dict["if_flag"] = timeslice_node.if_flag
    timeslice_node_dict["if_creg"] = timeslice_node.if_creg
    timeslice_node_dict["if_num"] = timeslice_node.if_num
    timeslice_node_dict["if_kind"] = timeslice_node.if_kind
    timeslice_node_dict["barrier"] = timeslice_node.barrier
    return timeslice_node_dict

# The function to transfer the dictionary to a timeslice node
def dict_to_timeslice_node(timeslice_node_dict):
    timeslice_node = Time_slice_node(timeslice_node_dict["gate_operation"])
    for property in timeslice_node_dict:
        if property == "gate_operation":
            continue
        setattr(timeslice_node, property, timeslice_node_dict[property])
    return timeslice_node

# Function to dump the quantum circuit into a json file
def dump_to_json(quantumcircuit):
    quantumcircuit_dict = {}
    quantumcircuit_dict["name"] = quantumcircuit.name
    quantumcircuit_dict["cregs_size"] = quantumcircuit.cregs_size
    quantumcircuit_dict["qubits_idx"] = quantumcircuit.qubits_idx
    quantumcircuit_dict["cregs_idx"] = quantumcircuit.cregs_idx
    quantumcircuit_dict["qubit_max_time_slice"] = quantumcircuit.qubit_max_time_slice   
    quantumcircuit_dict["creg_max_time_slice"] = quantumcircuit.creg_max_time_slice
    quantumcircuit_dict["max_time_slice"] = quantumcircuit.max_time_slice
    quantumcircuit_dict["measured_max_time_slice"] = quantumcircuit.measured_max_time_slice
    quantumcircuit_dict["cregs"] = quantumcircuit.cregs
    quantumcircuit_dict["qubits"] = {}
    for qubit in quantumcircuit.qubits:
        quantumcircuit_dict["qubits"][qubit] = {}
        for timeslice in quantumcircuit.qubits[qubit]:
            quantumcircuit_dict["qubits"][qubit][timeslice] = timeslice_node_to_dict(quantumcircuit.qubits[qubit][timeslice])
    with open(quantumcircuit.name+".json", 'w') as f:
            json.dump(quantumcircuit_dict, f, indent=4)

# Function to load the quantum circuit from a json file
def load_from_json(filename, quantumcircuit):
    with open(filename, 'r') as f:
        quantumcircuit_dict = json.load(f)
        for property in quantumcircuit_dict:
            # Skip the qubits
            if property == "qubits":
                continue
            setattr(quantumcircuit, property, quantumcircuit_dict[property])
        # Set the qubits and its corresponding timeslice nodes to the quantum circuit
        for qubit in quantumcircuit_dict["qubits"]:
            quantumcircuit.qubits[qubit] = {}
            for timeslice in quantumcircuit_dict["qubits"][qubit]:
                quantumcircuit.qubits[qubit][timeslice] = dict_to_timeslice_node(quantumcircuit_dict["qubits"][qubit][timeslice])