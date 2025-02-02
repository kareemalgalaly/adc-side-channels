module negedge_detector #(
    parameter int NUM_PIXELS = 1  // Number of comparators (default: 50)
)(
    input  logic clk,                          // Clock signal
    input  logic reset,                        // Active-high reset signal
    input  logic [NUM_PIXELS-1:0] comp,        // Array of comparator outputs
    output logic [NUM_PIXELS-1:0] enable       // Array of enable signals
);

    // Internal delayed signal for each comparator
    logic [NUM_PIXELS-1:0] delayed_signal;
    logic [NUM_PIXELS-1:0] negedge_sample;
    logic [NUM_PIXELS-1:0] sample_hold;
    logic [NUM_PIXELS-1:0] sample_hold_registered;

    // Delayed signal through inverters (4-stage delay)
    assign delayed_signal = ~( ~( ~( ~comp ) ) ); // Four inverters for delay

    // First register to sample delayed signal
    always_ff @(negedge clk) begin
        if (reset)
            negedge_sample <= 'b0; // Reset to 0
        else
            negedge_sample <= delayed_signal;
    end

    // Register to hold previous value
    always_ff @(posedge clk) begin
        if (reset)
            sample_hold <= '0; // Reset all elements to 0
        else begin
            for (int i = 0; i < NUM_PIXELS; i++) begin
                if (negedge_sample[i])
                    sample_hold[i] <= 1'b1;
            end
        end
    end

    // Register to store sampled value
    always_ff @(posedge clk) begin
        if (reset)
            sample_hold_registered <= '0; // Reset all elements to 0
        else
            sample_hold_registered <= sample_hold;
    end

    // AND gate logic for negative edge detection
    assign enable = (~sample_hold_registered) & sample_hold;

endmodule
