`ifndef __TB_LIB__
`define __TB_LIB__

`define inf(message) \
    $display($sformatf("INFO : %t: %s", $realtime, message))

`define err(message) \
    $display($sformatf("ERROR: %t: %s", $realtime, message))

`define check(signal, value, msg="") \
    if (signal !== value) begin \
        `err($sformatf("ASSERTION FAILED in %m: %s", msg)); \
        `inf($sformatf("Expected %0d, Got %0d", value, signal)); \
        $finish; \
    end

module clock_reset_gen #(
    parameter CLOCK_NS=5,
    parameter RESET_NS=20,
    parameter RESET_DELAY_NS=5,
    parameter CLOCK_DELAY_NS=10,
    parameter RESET_ACTIVE=1
) (
    output reg clk,
    output reg rst
);

    initial begin
        clk = 1'bx;
        #(CLOCK_DELAY_NS * 1ns);
        clk = 0;
        forever #(CLOCK_NS * 1ns) clk = ~clk;
    end

    initial begin
        rst = 1'bx;
        #(RESET_DELAY_NS * 1ns);
        rst = RESET_ACTIVE;
        #(RESET_NS * 1ns) rst = ~rst;
    end
endmodule

`endif
