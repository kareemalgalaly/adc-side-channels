//*****************************************************************************
// File        : comparator_sampler.v
// Author      : kareemahmad
// Created     : 2025 Jan 08
// Description : Collection of modules related to sampling
//*****************************************************************************

// --------------------------------------------------
// module: negedge_sampler
// - Samples a signal on negative edge of the clock
// --------------------------------------------------

module negedge_sampler (
    input clk,
    input in,
    output reg out
);

    wire in_1n;
    wire in_1p;
    wire in_2n;
    wire in_2p;

    assign in_1n = ~in;
    assign in_1p = ~in_1n;
    assign in_2n = ~in_1p;
    assign in_2p = ~in_2n;

    always @(negedge clk) begin
        out <= in_2p;
    end
endmodule

// --------------------------------------------------
// module: sample_hold
// - Holds output high when input rises until reset
// --------------------------------------------------

module sample_hold (
    input clk,
    input rst,
    input in,
    output reg out
);

    wire sampled;

    negedge_sampler sampler (
        .clk    (clk    ),
        .in     (in     ),
        .out    (sampled)
    );

    always @(posedge clk) begin
        if      (rst    ) out <= 0;
        else if (sampled) out <= 1;
    end

endmodule

// --------------------------------------------------
// module: edge_sampler
// - Pulses output for one cycle on rising edge of input
// --------------------------------------------------

module edge_sampler (
    input clk,
    input rst,
    input in,
    output out
);

    wire held;
    reg held_q;

    sample_hold hold (
        .clk    (clk    ),
        .rst    (rst    ),
        .in     (in     ),
        .out    (held   )
    );

    always @(posedge clk) begin
        if      (rst    ) held_q <= 0;
        else              held_q <= held;
    end

    assign out = held & ~held_q;
endmodule

// --------------------------------------------------
// module: value_sampler
// - Updates output from input when sample is high
// --------------------------------------------------

module value_sampler #(
    parameter WIDTH=8,
) (
    input clk,
    input rst,
    input [WIDTH-1:0] in,
    input sample,
    output reg valid,
    output reg [WIDTH-1:0] out
); 

    always @(posedge clk) begin
        if (rst) begin
            valid <= 0;
            out   <= '0;
        end
        else begin
            if (sample) begin
                valid <= 1;
                out   <= in;
            end
        end
    end

endmodule
