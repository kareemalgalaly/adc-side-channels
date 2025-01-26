module digitalADC #(
    parameter ASYNC = 0,
    parameter NUM_SENSORS = 1,
    parameter WIDTH = 8
) (
    input  clk,
    input  rst,
    input  comp_out, // [NUM_SENSORS-1:0]

    output reg valid, // [NUM_SENSORS-1:0]
    output reg [WIDTH-1:0] digital_val, // [NUM_SENSORS-1:0]
);

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

