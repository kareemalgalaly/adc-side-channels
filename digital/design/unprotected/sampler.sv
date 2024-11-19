module sampler (
    input  clk,
    input  rstn,
    input [7:0] count,
    output [7:0] digital_op 
)

always @(posedge clk) begin
    if (!rstn)
        digital_op <= 0;
    else if (comp_out)
        digital_op <= count;
end