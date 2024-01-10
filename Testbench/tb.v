`timescale 1ns/100ps
module tb (
);
reg clk;
reg clk_en;
reg aclr;
reg en;
reg signed [31:0] amp_in_real;
reg signed [31:0] amp_in_img;
reg [4:0] qubit_op;
reg [4:0] state_in;
wire signed [31:0] amp_out_real;
wire signed [31:0] amp_out_img;
wire [4:0] state_out;

//Instantiate the DUT
PauliY_core #(.AMP_WIDTH(32), .N_QUBIT(5)) PauliY_core_test(
	.clk(clk),
	.clk_en(clk_en),
	.aclr(aclr),
	.en(en),
	.amp_in_real(amp_in_real),
	.amp_in_img(amp_in_img),
	.qubit_op(qubit_op),
	.state_in(state_in),
	.amp_out_real(amp_out_real),
	.amp_out_img(amp_out_img),
	.state_out(state_out));
//Create a clock with frequency 50MHz and duty cycle 50%
always # 10.0 clk = ~clk;
//Initialization
initial begin
	$display($time, " << Starting Simulation >> ");
	//intialise/set input
	clk = 1'b0;
	clk_en <= 1'b1;
	aclr <= 1'b0;
	en <= 1'b0;
	amp_in_real <= 32'b0;
	amp_in_img <= 32'b0;
	qubit_op <= 5'b0;
	state_in <= 5'b0;
	//Wait 10 cycles (corresponds to timescale at the top)
	#10;
end
//Test cases
integer i = 0;
always @(posedge clk) begin
	i = i+1;
	if (i == 1) begin
		en <= 1'b1;
		amp_in_real <= 32'b11111111110010011000111000001111;
		amp_in_img <= 32'b00101110111110111010000101000001;
		qubit_op <= 5'b10011;
		state_in <= 5'b00100;
	end
	if (i == 2) begin
		en <= 1'b1;
		amp_in_real <= 32'b11100110111001111111011100101101;
		amp_in_img <= 32'b10010011100000111101100111011001;
		qubit_op <= 5'b00011;
		state_in <= 5'b11100;
	end
	if (i == 3) begin
		en <= 1'b1;
		amp_in_real <= 32'b11110001100000111010001101000100;
		amp_in_img <= 32'b00011100100010011011111111100111;
		qubit_op <= 5'b00100;
		state_in <= 5'b10101;
	end
	if (i == 4) begin
		en <= 1'b1;
		amp_in_real <= 32'b11100110000111100010010000110111;
		amp_in_img <= 32'b10000101001100011001011000010110;
		qubit_op <= 5'b10111;
		state_in <= 5'b00110;
	end
	if (i == 5) begin
		en <= 1'b1;
		amp_in_real <= 32'b10110101111000110010101001111111;
		amp_in_img <= 32'b11011000011010110110100101000010;
		qubit_op <= 5'b11011;
		state_in <= 5'b00001;
	end
	if (i == 6) begin
		en <= 1'b1;
		amp_in_real <= 32'b10011010011111111111111000001100;
		amp_in_img <= 32'b11101101110101010011001101111010;
		qubit_op <= 5'b00111;
		state_in <= 5'b11100;
	end
	if (i == 7) begin
		en <= 1'b1;
		amp_in_real <= 32'b10010110100000101011001001011101;
		amp_in_img <= 32'b10110011100110000011101000101001;
		qubit_op <= 5'b00001;
		state_in <= 5'b01011;
	end
	if (i == 8) begin
		en <= 1'b1;
		amp_in_real <= 32'b11110101011100001100111111000100;
		amp_in_img <= 32'b10001100110001111101100111100101;
		qubit_op <= 5'b00110;
		state_in <= 5'b10101;
	end
	if (i == 9) begin
		en <= 1'b1;
		amp_in_real <= 32'b11001000001011101111111110111100;
		amp_in_img <= 32'b01110110111101000100111100001110;
		qubit_op <= 5'b11000;
		state_in <= 5'b00011;
	end
	if (i == 10) begin
		en <= 1'b1;
		amp_in_real <= 32'b10011111011111100100010010101101;
		amp_in_img <= 32'b10000010010001101100011000000111;
		qubit_op <= 5'b10001;
		state_in <= 5'b00101;
	end
	if (i == 12) begin
		aclr <= 1'b1;
	end
	if (i == 13) begin
		$display($time, "<< Simulation Complete >>");
		$stop;
	end
end
endmodule