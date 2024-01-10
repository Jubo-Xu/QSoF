module Module1 (
);
reg [2:0] a;
reg b;
wire [1:0] c;

always @(posedge clk) begin
	c <= c;
end
endmodule