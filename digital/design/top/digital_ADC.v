module digitalADC #(
    parameter ASYNC = 0,
    parameter WIDTH = 8
) (
    input               clk,
    input               rst,
    input               comp_out,

    output              valid,       
    output [WIDTH-1:0]  digital_val
);

    wire [WIDTH-1:0] count_value;
    wire             comp_pulsed;

    counter_half #(
        .WIDTH(WIDTH)
    ) counter (
        .clk        (clk        ),
        .rst        (rst        ),
        .en         (           ),
        .set        (0          ),
        .setval     ('0         ),
        .count      (count_value),
        .overflow   (           )
    );

    edge_sampler edge_detect (
        .clk        (clk        ),
        .rst        (rst        ),
        .in         (comp_out   ),
        .out        (comp_pulsed)
    );

    value_sampler #(
        .WIDTH(WIDTH)
    ) value_capture (
        .clk        (clk        ),
        .rst        (rst        ),
        .in         (count_value),
        .sample     (comp_pulsed),
        .valid      (valid      ),
        .out        (digital_val)
    );

endmodule

