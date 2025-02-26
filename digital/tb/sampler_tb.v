//*****************************************************************************
// File        : sampler_tb.v
// Author      : kareemahmad
// Description : Testbench for edge_sampler
//*****************************************************************************

`include "tb_lib.v"

module sampler_tb;
    wire clk, rst;
    wire comp_pulse;
    reg comp_out;
    reg comp_switched;

    clock_reset_gen crgen (
        .clk(clk), 
        .rst(rst)
    );

    edge_sampler sampler (
        .clk        (clk        ), 
        .rst        (rst        ),
        .in         (comp_out   ),
        .out        (comp_pulse )
    );

    // --------------------------------------------------
    // process: test_main
    // --------------------------------------------------


    initial begin
        $timeformat(-9, 2, " ns", 10);
        $dumpfile("build/sample_tb_dump.vcd");
        $dumpvars;
        $display("==================================================");
        $display("Test Starting");

        wait (rst === 1) @(posedge clk) `check(comp_pulse, 0, "comp_pulse not reset")

        fork 
            while (comp_switched !== 1) begin
                @(posedge clk); 
                `check(comp_pulse, 0, "comparator hasn't switched yet")
            end
            begin
                wait (comp_switched);
                @(posedge clk);
                `check(comp_pulse, 0, "comparator switching delay")
                @(posedge clk);
                `check(comp_pulse, 0, "comparator switching delay")
                @(posedge clk);
                `check(comp_pulse, 1, "comparator pulsing")
                @(posedge clk);
                `check(comp_pulse, 0, "comparator pulse deasserted")
                @(posedge clk);
                `check(comp_pulse, 0, "comparator pulse deasserted")
                @(posedge clk);
                `check(comp_pulse, 0, "comparator pulse deasserted")
            end
        join

        $display("Test Complete");
        $display("==================================================");
        $finish;
    end

    // --------------------------------------------------
    // process: Generate comp_out
    // --------------------------------------------------

    initial begin
        comp_out = 0;
        comp_switched = 0;

        $info("Waiting for reset");
        wait (rst === 0);
        repeat ($urandom_range(5,10)) @(posedge clk);

        $info("Comparator switching");
        comp_switched = 1;

        repeat (30) begin
            @(posedge clk) #1 comp_out = 1; // NOTE: without #1, nonblocking assignment 
            @(negedge clk) #1 comp_out = 0; // appears at the same time as the clk
        end
    end

endmodule

