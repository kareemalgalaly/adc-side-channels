module edge_detector #(
    parameter integer NUM_PIXELS = 1 // Number of comparators (default: 50)
)(
    input logic clk,
    input logic reset,
    input logic [NUM_PIXELS-1:0] comp,
    output logic [NUM_PIXELS-1:0] enable // Goes high when rising edge of comp is detected
);
    logic [NUM_PIXELS-1:0] comp_prev;

    always_ff @(posedge clk) begin
        if (reset)
            comp_prev <= {NUM_PIXELS{1'b0}};
        else
            comp_prev <= comp;
    end

    assign enable = comp & ~comp_prev; // Detect rising edges
    
endmodule
