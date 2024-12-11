module control (input a, input b, input clk, output c);
    wire c_d;
    assign c_d = a ^ b;
    always @(posedge clk) begin
        c <= c_d;
    end
endmodule
