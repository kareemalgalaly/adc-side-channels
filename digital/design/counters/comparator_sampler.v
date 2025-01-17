//*****************************************************************************
// File        : comparator_sampler.v
// Author      : kareemahmad
// Created     : 2025 Jan 08
// Description : 
//*****************************************************************************

module negedge_sampler (
    input clk,
    input in,
    output reg out
);

    reg test_a;
    reg test_b;
    reg test_c;

    wire in_1n;
    wire in_1p;
    wire in_2n;
    wire in_2p;

    assign in_1n = ~in;
    assign in_1p = ~in_1n;
    assign in_2n = ~in_1p;
    assign in_2p = ~in_2n;

    always_ff @(negedge clk) begin
        out <= in_2p;
        test_a <= in;
    end

    always_ff @(posedge clk) begin
        test_b <= in;
        test_c <= in_2p;
    end


endmodule

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
