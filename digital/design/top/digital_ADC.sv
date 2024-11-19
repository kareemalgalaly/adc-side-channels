module digitalADC #(
    parameter ASYNC = 1
) (
    input  clk,
    input  rstn,
    input  comp_out,
    input  restart,

    output ramp_en,
    output ramp_reset,
    output busy,
    output valid,
    output [7:0] count,
    output [7:0] digital_op
);

wire counter_rst;
wire counter_en;

control control(
    .clk        (clk        ),
    .rstn       (rstn       ),
    .comp_out   (comp_out   ),
    .restart    (restart    ),
    .counter_rst(counter_rst),
    .counter_en (counter_en ),
    .ramp_reset (ramp_reset ),
    .ramp_en    (ramp_en    ),
    .busy       (busy       ),
    .valid      (valid      ),
    .count      (count      )
);

sample sample(
    .clk        (clk),
    .rstn       (rstn),
    .coutn      (count),
    .comp_out   (comp_out),
    .digital_op (digital_op)
);

generate
    if (ASYNC == 1) begin
        rippleCarryCounter ctr(
            .clk        (clk         ), 
            .rstn       (!counter_rst),
            .ctrEn      (counter_en  ),
            .count      (count       )
        ); 
    end
    else begin
        async_8bit_counter ctr(
            .clk        (clk         ), 
            .rstn       (!counter_rst),
            .ctrEn      (counter_en  ),
            .count      (count       )
        ); 
    end
endgenerate

endmodule