`include "tb_lib.v"

module counter_tb;
    wire clk, rst;
    wire overflow;
    wire [7:0] count;
    reg ctr_en, ctr_set;
    reg [7:0] ctr_set_v;

    clock_reset_gen crgen (
        .clk(clk), 
        .rst(rst)
    );

    `ifdef BEHAV
        counter_behav counter_inst (
            .clk        (clk        ), 
            .rst        (rst        ),
            .en         (ctr_en     ),
            .set        (ctr_set    ),
            .setval     (ctr_set_v  ),
            .count      (count      ),
            .overflow   (overflow   )
        );
    `else
        counter_half counter_inst (
            .clk        (clk        ), 
            .rst        (rst        ),
            .en         (ctr_en     ),
            .set        (ctr_set    ),
            .setval     (ctr_set_v  ),
            .count      (count      ),
            .overflow   (overflow   )
        );
    `endif

    initial begin
        $timeformat(-9, 2, " ns", 10);
        $dumpfile("build/counter_tb_dump.vcd");
        $dumpvars;
        $display("==================================================");
        $display("Test Starting");
        ctr_en  = 0;
        ctr_set = 0;

        test_reset();
        test_counting();
        test_set();
        test_overflow();
        $display("Test Complete");
        $display("==================================================");
        $finish;
    end

    task automatic test_reset();
        wait (rst === 1);
        wait (rst === 0);
        @(posedge clk);
        `check(count, 0, "Counter not 0 after reset")
    endtask : test_reset

    task automatic test_counting();
        int init_count = count;
        int num_ticks = $urandom_range(2, 60);

        ctr_en = 0;
        @(posedge clk);
        `check(count, init_count, "Counter should not change if ctr_en is low")
        `check(overflow, 0, "Overflow should be 0")

        ctr_en = 1;
        @(posedge clk);
        `check(count, init_count+1, "Counter should change if ctr_en is high")
        `check(overflow, 0, "Overflow should be 0")

        repeat(num_ticks - 1) @(posedge clk);
        `check(count, init_count+num_ticks, "Counter should change if ctr_en is high")
        `check(overflow, 0, "Overflow should be 0")
    endtask : test_counting

    task automatic test_set();
        ctr_set_v = $urandom_range(254);
        ctr_set   = 1;

        @(posedge clk);
        `check(count, ctr_set_v, "Counter did not get set to set value")
        `check(overflow, 0, "Overflow should be 0")

        @(posedge clk);
        `check(count, ctr_set_v, "Counter did not get set to set value")
        `check(overflow, 0, "Overflow should be 0")

        ctr_set = 0;
        @(posedge clk);
        `check(count, ctr_set_v+1, "Counter remained set after ctr_set went low")
        `check(overflow, 0, "Overflow should be 0")
    endtask : test_set

    task automatic test_overflow();
        ctr_set_v = 255;
        ctr_set = 1;

        @(posedge clk);
        `check(count, 255, "Counter remained set after ctr_set went low")
        `check(overflow, 0, "Overflow should be 0")
        
        ctr_set = 0;

        @(posedge clk);
        `check(count, 0, "Counter did not overflow")
        `check(overflow, 1, "Overflow should be 1")

        @(posedge clk);
        `check(count, 1, "Counter should continue counting")
        `check(overflow, 0, "Overflow should be 0")
    endtask : test_overflow
endmodule
