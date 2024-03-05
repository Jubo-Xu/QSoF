# qsofinstr v0.0.1 of QSoF
This branch contains the testing version 0 of the transpiler of `QSoF`. It could compile the `OpenQASM 2.0` files into a graph structured quantum circuit, and it could also load the quantum circuit from its configuration json file. For now, `qsofinstr v0.0.1` supports compiling quantum circuit into self-designed instruction set that would be sent to FPGA for emulation, test draw of quantum circuit on the console, and the json file that contains the structure configuration of the quantum circuit. 

## Installation
  ```bash
  pip install qsofinstr
  ```
## File Structure
  ```bash
qsofinstr/
│
├── IR/
│ └── QASM2/
│ ├── qasm2_parser.py
│ ├── qasm2_token.py
│ └── Examples/
│
└── InstructionGenerator/
├── instruction.py
└── measurement.py
│
└── Optimizations/
└── ...
│
└── Visualization/
└── ...
│
├── quantumcircuit.py
├── hardware_specification.py
├── timeslice.py
└── ...
  ```
The file structure of `qsofinstr` is shown above. Subfolder `IR` contains all the Intermediate Representations supported that could be compiled into quantum circuit. Now the only IR supported is `OpenQASM 2.0`, the lexer, parser, and quantum circuit generation files are contained in the subfolder `QASM2`. The `Examples` folder contains the example `.qasm` files. Later when more IRs are supported, like `OpenQASM 3.0`, the folder would be extended following the same structure. The folder `InstructionGenerator` contains the files that used to generate the self-designed instruction set, which behaves like an assembiler in classical compilers. Folder `Optimizations` should contain the files that achieve the optimizations of the quantum circuit for the best performance and lowest number quantum gates, which would be added later. `Visualization` folder should contain the visualization tools of the compiled circuit, like high quality latex image or matplotlib images, just like that of `qiskit`. This will be added later. Other files are used to define the quantum circuit data structure, the hardware specifications needed by FPGA implementation, and other package related files, like command line interface configurations. 
## Transpiler Flags
1. `--hardwarespec`: the flag to indicate whether the hardware specification is needed
2. `-mode`: this flag is used following the `--hardwarespec`, which indicates which mode in [1, 2] is applied for hardware specification
3. `-qasm2`: the flag indicates compiling the `OpenQASM 2.0` files
4. `-json`: the flag indicates generating the quantum circuit from configuration json file
5. `-test`: the flag indicates the following behaviors are for testing
6. `-draw`: the flag that should be used in together with `-test` to print the test draw of quantum circuit on the console
7. `-instr`: the flag indicates instruction generation, if used together with `-test`, the test of instructions is printed on the console
8. `-bin`: the flag that should be used together with `-instr` to generate the `.bin` file contains the 64 bits little endian binaries of instruction
9. `-txt`: the flag that should be used together with `-instr` to generate the `.txt` file contains the 64 bits binary representation of instructions
## Getting Started
### Generate from JSON
  ```bash
  qsofinstr -json [flag options] <json filename>
  ```
### Generate from OpenQASM 2.0
1. Generate the json configuration of quantum circuit data structure
   ```bash
   qsofinstr -qasm2 [hardwarespec flags] <filename>
   ```
2. Print the test draw of quantum circuit on console
   >**Note**: For controlled gates, the target qubit is represented as `gatename o`, like `cx o` and the control qubts are represented as `gatename targetqubit`, like `cx q[0]`. If the gate operation is under the               condition, then it should be represented as `gatename qubit|classicalbit=val`, for example if the statement is `if(c[0]==0)h q[0]`, then the test draw is `h q[0]|c[0]=0`. The measurement is                        represented as `M qubit->bit`, like `M q[0]->c[0]`. The general structure is like this: the first line prints the qubit names, and the gate operations of all the qubits in a timeslice are printed                  following the timeslice index. The gate operations on the same qubit are connected by `|`, and if there's no gate operation on that qubit at this timeslice, the an empty string is printed.
    ```bash
    qsofinstr -qasm2 [hardwarespec flags] -test -draw <filename>
    ```
3. Print the test of generated instruction on console
   ```bash
   qsofinstr -qasm2 [hardwarespec flags] -test -instr <filename>
   ```
   The instruction of each timeslice will be printed in sequence, an example of the format of one timeslice is
   ```bash
   Timeslice 1:
   single_gate_no_condition
   1000000100111111111111111111111111111111111111111111111111111111
   single_gate_condition
   control_gate_no_condition
   control_gate_condition
   decoherence
   measurement
   reset
   ```
4. Generate the binary representation of instruction to .txt or .bin
   >**Note**: The format of the output file name is `<input filename>_instr_bin.bin` or `<input filename>_instr_bin.txt`
   ```bash
   qsofinstr -qasm2 [hardwarespec flags] -instr -bin <filename>
   ```
   ```bash
   qsofinstr -qasm2 [hardwarespec flags] -instr -txt <filename>
   ```
### Example
In this example, the input file is `qec.qasm`, which describes a repitational quantum error correction with error syndrome measurement. The code is
```python
OPENQASM 2.0;
include "qelib1.inc";
qreg q[3];
qreg a[2];
creg c[3];
creg syn[2];
gate syndrome d1,d2,d3,a1,a2
{
cx d1,a1; cx d2,a1;
cx d2,a2; cx d3,a2;
}
x q[0]; // error
barrier q;
syndrome q[0],q[1],q[2],a[0],a[1];
measure a -> syn;
if(syn==1) x q[0];
if(syn==2) x q[2];
if(syn==3) x q[1];
measure q -> c;
```
Compile this file under the mode 1 hardware specification and print the test draw of compiled quantum circuit on console using command
```bash
qsofinstr -qasm2 --hardwarespec -mode 1 -test -draw "qec.qasm"
```
The test draw of this example is 
```bash
   q[0]               q[1]               q[2]               a[0]               a[1]
   |                  |                  |                  |                  |
1: x
   |                  |                  |                  |                  |
2: BARRIER            BARRIER            BARRIER
   |                  |                  |                  |                  |
3: cx a[0]                                                  cx o
   |                  |                  |                  |                  |
4:                    cx a[0]                               cx o
   |                  |                  |                  |                  |
5:                    cx a[1]                                                  cx o
   |                  |                  |                  |                  |
6:                                       cx a[1]                               cx o
   |                  |                  |                  |                  |
7:                                                          M -> syn[0]        M -> syn[1]
   |                  |                  |                  |                  |
8: x|syn=1            x|syn=3            x|syn=2
   |                  |                  |                  |                  |
9: M -> c[0]          M -> c[1]          M -> c[2]
```