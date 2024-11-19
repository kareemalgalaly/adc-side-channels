// 1Mhz clk

module digital_ADC_tb();
    reg  clk,   // Inputs are set as regs
    reg  rstn,  // 
    reg  comp_out,
    reg  restart,

    wire ramp_en, // Outputs are set as wires (always will be driven)
    wire ramp_reset,
    wire busy,
    wire valid,
    wire [7:0] count


    // Design Under Test mapping
    digital_ADC #(
        .ASYNC(ASYNC)
    ) dut (
        .clk(clk), .rstn(rstn), .comp_out(comp_out), 
    .restart(restart), .ramp_en(ramp_en), .ramp_reset(ramp_reset), 
    .busy(busy), .valid(valid), .count(count));

    initial
        begin
            //Put test cases in here
            

        end

endmodule:


