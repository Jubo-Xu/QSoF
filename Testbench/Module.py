class Module (object):
    def __init__ (self, name, signal_property):
        self.name = name
        self.input = signal_property.get("input", None)
        self.output = signal_property.get("output", None)
        self.wire = signal_property.get("wire", None)
        self.reg = signal_property.get("reg", None)
        self.content = [""]
        self.verilog_strlist = []
    
    def always_block (self, content_inside, sensitivity_list = []):
        if not sensitivity_list:  # Check for an empty list
            self.content.append("always @(*) begin")
        else:
            formatted_triggers = []
            for signal, edge in sensitivity_list:
                if edge == '+':
                    formatted_triggers.append(f"posedge {signal}")
                elif edge == '-':
                    formatted_triggers.append(f"negedge {signal}")
                else:
                    formatted_triggers.append(signal)  # In case it's neither posedge nor negedge
            self.content.append("always @(" + "or".join(formatted_triggers) + ") begin")
        self.content.extend (["\t" + line for line in content_inside])
        self.content.append ("end")
    
    def assign (self, lhs, rhs):
        self.content.append(f"assign {lhs} = {rhs};")
    
    @staticmethod
    def add_block(block_name, content_inside, content):
        content.append(block_name)
        content.extend(["\t" + line for line in content_inside])
        content.append("end" + block_name if block_name == "generate" else "end")

    def initial_block(self, content_inside):
        self.add_block("initial begin", content_inside, self.content)

    def generate_block(self, content_inside):
        self.add_block("generate", content_inside, self.content)
    
    def if_block(self, condition, content_inside, content):
        self.add_block(f"if ({condition}) begin", content_inside, content)
    
    def write_to_file(self, filename):
        with open(filename, 'w') as f:
            for i, line in enumerate(self.verilog_strlist):
                if i != len(self.verilog_strlist) - 1:  # If it's not the last line
                    f.write(line + '\n')
                else:
                    f.write(line)  # Write the last line without a newline character
    
    def generate_verilog (self):
        self.verilog_strlist.append("module " + self.name + " (")
        if self.input is not None:
            for signal in self.input:
                self.verilog_strlist.append(signal[0] + ",")
        if self.output is not None:
            for signal in self.output:
                self.verilog_strlist.append(", ".join(signal[0]))
        self.verilog_strlist.append(");")
        if self.input is not None:
            for signal in self.input:
                if signal[1] > 1:
                    self.verilog_strlist.append(f"input signed [{signal[1]-1}:0] {signal[0]};") if signal[2] == "signed" else \
                        self.verilog_strlist.append(f"input [{signal[1]-1}:0] {signal[0]};")
                else:
                    self.verilog_strlist.append(f"input {signal[0]};") 
        if self.output is not None:
            for signal in self.output:
                if signal[1] > 1:
                    self.verilog_strlist.append(f"output signed [{signal[1]-1}:0] {signal[0]};") if signal[2] == "signed" else \
                        self.verilog_strlist.append(f"output [{signal[1]-1}:0] {signal[0]};")
                else:
                    self.verilog_strlist.append(f"output {signal[0]};")
        if self.reg is not None:
            for signal in self.reg:
                if signal[1] > 1:
                    self.verilog_strlist.append(f"reg signed [{signal[1]-1}:0] {signal[0]};") if signal[2] == "signed" else \
                        self.verilog_strlist.append(f"reg [{signal[1]-1}:0] {signal[0]};")
                else:
                    self.verilog_strlist.append(f"reg {signal[0]};")
        if self.wire is not None:
            for signal in self.wire:
                if signal[1] > 1:
                    self.verilog_strlist.append(f"wire signed [{signal[1]-1}:0] {signal[0]};") if signal[2] == "signed" else \
                        self.verilog_strlist.append(f"wire [{signal[1]-1}:0] {signal[0]};")
                else:
                    self.verilog_strlist.append(f"wire {signal[0]};")
        self.verilog_strlist.extend(self.content)
        self.verilog_strlist.append("endmodule")
        self.write_to_file(self.name + ".v")

    def __str__ (self):
        return self.name 

Module1 = Module("Module1", {"reg": [("a", 3, "unsigned"), ("b", 1, "unsigned")], "wire": [("c", 2, "unsigned")]})
Module1.always_block(["c <= c;"], [("clk", '+')])
Module1.generate_verilog()