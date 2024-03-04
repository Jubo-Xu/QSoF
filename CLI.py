from quantumcircuit import Quantum_circuit
from hardware_specification import Specification
import argparse
import sys

# Define the functions to get the flags
def get_parser_qsofinstr():
    parser = argparse.ArgumentParser(description='QSOF Quantum Circuit Transpiler')
    parser.add_argument('--hardwarespec', action='store_true', help='Enable hardware specification')
    parser.add_argument('-mode', type=int, choices=[1, 2], help='Set the mode for hardware specification')
    parser.add_argument('-qasm2', action='store_true', help='Compile the OpenQASM 2.0 files')
    parser.add_argument('-json', action='store_true', help='Load the quantum circuit from a json file')
    parser.add_argument('-test', action='store_true', help='Indicates testing mode')
    parser.add_argument('-draw', action='store_true', help='=Draw the raw quantum circuit under the testing mode on the console')
    parser.add_argument('-instr', action='store_true', help='Compile the QSoF instruction files')
    parser.add_argument('-bin', action='store_true', help='Compile the instruction into the .bin file')
    parser.add_argument('-txt', action='store_true', help='Compile the instruction into the .txt file')
    parser.add_argument('filename', type=str, help='The file to compile or process')
    return parser

# Define the function to do the compilation based on compiler flags
def execute(args):
    if args.hardwarespec:
        Specification.Need = True
        if args.mode is not None:
            Specification.Mode = args.mode
    QC = None
    if args.qasm2:
        QC = Quantum_circuit.from_qasm2(args.filename)
    if args.json:
        if not args.filename.lower().endswith('.json'):
            print("\033[91m" + "Error: Filename must end with .json when using -json flag" + "\033[0m")
            sys.exit(1) 
        QC = Quantum_circuit.from_json(args.filename)
    if args.test:
        if args.draw:
            QC.test_draw()
        elif args.instr:
            QC.test_instruction()
        else:
            # Temporarily use the test draw as the default option
            QC.test_draw()
    else:
        if args.instr:
            if args.bin:
                QC.to_binary_bin()
            elif args.txt:
                QC.to_binary_text()
            else:
                # Temporarily use the text file as the default output
                QC.to_binary_text()
        else:
            # Dump the quantum circuit into a json file
            QC.to_json()
    
# Define the main function to execute the program
def main():
    parser = get_parser_qsofinstr()
    args = parser.parse_args()
    execute(args)

if __name__ == '__main__':
    main()
        
            
        
            
