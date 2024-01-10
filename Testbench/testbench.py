from Module import Module
import random

class Singel_qubit_gate_tb(Module):
    def __init__(self, name, signal_property, parameters = {}, timeunit = "1ns", timeprecision = "100ps", clk_freq = "50MHz", mode = 0, input_tb = [], maxitr = 1):
        super().__init__(name, signal_property)
        self.AMP_WIDTH = parameters.get("AMP_WIDTH", None)
        self.N_QUBIT = parameters.get("N_QUBIT", None)
        self.timeunit = timeunit
        self.timeprecision = timeprecision
        self.clk_freq = clk_freq
        self.mode = mode
        self.input_tb = input_tb
        self.maxitr = maxitr
        self.randinput = []
    
    def timescale(self):
        self.verilog_strlist.append("`timescale " + self.timeunit + "/" + self.timeprecision) 
    
    def set_clk(self):
        #first only considering about timeunit as ns and frequency as MHz
        n_clk = 10**3/(2*int(self.timeunit[:-2]) * int(self.clk_freq[:-3]))
        self.content.append("//Create a clock with frequency " + self.clk_freq + " and duty cycle 50%")
        self.content.append("always # "+str(n_clk)+" clk = ~clk;")
    
    def set_initial_block(self, wait_time = 10):
        content_inside = []
        content_inside.append("$display($time, \" << Starting Simulation >> \");")
        content_inside.append("//intialise/set input")
        content_inside.append("clk = 1'b0;")
        content_inside.append("clk_en <= 1'b1;")
        content_inside.append("aclr <= 1'b0;")
        content_inside.append("en <= 1'b0;")
        content_inside.append("amp_in_real <= "+str(self.AMP_WIDTH)+"'b0;")
        content_inside.append("amp_in_img <= "+str(self.AMP_WIDTH)+"'b0;")
        content_inside.append("qubit_op <= "+str(self.N_QUBIT)+"'b0;")
        content_inside.append("state_in <= "+str(self.N_QUBIT)+"'b0;")
        content_inside.append("//Wait "+str(wait_time)+" cycles (corresponds to timescale at the top)")
        content_inside.append("#"+str(wait_time)+";")
        self.initial_block(content_inside)
    
    def DUT_instantiate(self, DUT_name):
        self.content.append("//Instantiate the DUT")
        self.content.append(DUT_name+" #(.AMP_WIDTH("+str(self.AMP_WIDTH)+"), .N_QUBIT("+str(self.N_QUBIT)+")) "+DUT_name+"_test(")
        self.content.append("\t.clk(clk),")
        self.content.append("\t.clk_en(clk_en),")
        self.content.append("\t.aclr(aclr),")
        self.content.append("\t.en(en),")
        self.content.append("\t.amp_in_real(amp_in_real),")
        self.content.append("\t.amp_in_img(amp_in_img),")
        self.content.append("\t.qubit_op(qubit_op),")
        self.content.append("\t.state_in(state_in),")
        self.content.append("\t.amp_out_real(amp_out_real),")
        self.content.append("\t.amp_out_img(amp_out_img),")
        self.content.append("\t.state_out(state_out));")
    
    def comment(self, comment):
        self.content.append("//"+comment)
    
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
    
    def test_input_block(self, DUT_cycletime = 1):
        self.content.append("integer i = 0;")
        content_always = []
        content_always.append("i = i+1;")
        if self.mode == 0:
            for i in range(1, len(self.input_tb)+1):
                content_if = []
                content_if.append("en <= 1'b1;")
                content_if.append("amp_in_real <= " + self.input_tb[i-1][0] + ";")
                content_if.append("amp_in_img <= " + self.input_tb[i-1][1] + ";")
                content_if.append("qubit_op <= " + self.input_tb[i-1][2] + ";")
                content_if.append("state_in <= " + self.input_tb[i-1][3] + ";")
                self.if_block("i == "+str(i), content_if, content_always)
            self.if_block("i == "+str(len(self.input_tb)+DUT_cycletime+1), ["aclr <= 1'b1;"], content_always)
            self.if_block("i == "+str(len(self.input_tb)+DUT_cycletime+2), ["$display($time, \"<< Simulation Complete >>\");", "$stop;"], content_always)
        else:
            for i in range(1, self.maxitr+1):
                content_if = []
                content_if.append("en <= 1'b1;")
                amp_real = random.randint(-2**(self.AMP_WIDTH-1)+1, 2**(self.AMP_WIDTH-1)-1)
                amp_img = random.randint(-2**(self.AMP_WIDTH-1)+1, 2**(self.AMP_WIDTH-1)-1)
                qubit_op = random.randint(0, 2**self.N_QUBIT-1)
                state = random.randint(0, 2**self.N_QUBIT-1)
                self.randinput.append((amp_real, amp_img, qubit_op, state))
                content_if.append("amp_in_real <= " + str(self.AMP_WIDTH) + "'b" + self.GetBinary(amp_real, self.AMP_WIDTH) + ";")
                content_if.append("amp_in_img <= " + str(self.AMP_WIDTH) + "'b" + self.GetBinary(amp_img, self.AMP_WIDTH) + ";")
                content_if.append("qubit_op <= " + str(self.N_QUBIT) + "'b" + self.GetBinary(qubit_op, self.N_QUBIT) + ";")
                content_if.append("state_in <= " + str(self.N_QUBIT) + "'b" + self.GetBinary(state, self.N_QUBIT) + ";")
                self.if_block("i == "+str(i), content_if, content_always)
            self.if_block("i == "+str(self.maxitr+DUT_cycletime+1), ["aclr <= 1'b1;"], content_always)
            self.if_block("i == "+str(self.maxitr+DUT_cycletime+2), ["$display($time, \"<< Simulation Complete >>\");", "$stop;"], content_always)
        self.always_block(content_always, [("clk", '+')])      
    
    @staticmethod
    def tb_verilog_generate(DUT_name, AMP_WIDTH, N_QUBIT, maxitr = 1, input_tb = [], timeunit = "1ns", timeprecision = "100ps", clk_freq = "50MHz"):
        mode = 0
        if not input_tb:
            mode = 1
        signal_property = {"reg": [("clk", 1, "unsigned"), ("clk_en", 1, "unsigned"), ("aclr", 1, "unsigned"), ("en", 1, "unsigned"), \
                                   ("amp_in_real", AMP_WIDTH, "signed"), ("amp_in_img", AMP_WIDTH, "signed"), ("qubit_op", N_QUBIT, "unsigned"), ("state_in", N_QUBIT, "unsigned")],\
                           "wire": [("amp_out_real", AMP_WIDTH, "signed"), ("amp_out_img", AMP_WIDTH, "signed"), ("state_out", N_QUBIT, "unsigned")]}
        parameters = {"AMP_WIDTH": AMP_WIDTH, "N_QUBIT": N_QUBIT}
        tb = Singel_qubit_gate_tb("tb", signal_property, parameters, timeunit, timeprecision, clk_freq, mode, input_tb, maxitr)
        tb.timescale()
        tb.DUT_instantiate(DUT_name)
        tb.set_clk()
        tb.comment("Initialization")
        tb.set_initial_block()
        tb.comment("Test cases")
        tb.test_input_block()
        tb.generate_verilog()
        return tb.randinput


# Singel_qubit_gate_tb.tb_verilog_generate("PauliY_core", 32, 5, 1, [("32'h4444", "32'h4444", "5'b00101", "5'b11111")])
print(Singel_qubit_gate_tb.tb_verilog_generate("PauliY_core", 32, 5, 10, []))


