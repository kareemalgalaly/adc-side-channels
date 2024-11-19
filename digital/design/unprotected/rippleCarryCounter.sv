module rippleCarryCounter (
    input clk,
    input rstn,
    input ctrEn,
    output [7:0] count // what happens when s reaches max value?
);

wire [7:0] sum;

bitAdder bA(.a(count), .b(1'b1), .c(sum));

always @(posedge clk) begin
    if (!rstn)
        count <= 8'b0; // reset on start
    else if (ctrEn)
        count <= sum; // update counter with sum
end

endmodule
