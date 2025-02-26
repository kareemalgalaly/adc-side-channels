module register_array #(
    parameter integer NUM_PIXELS = 1 // Number of comparators (default: 50)
)(
    input logic clk,
    input logic reset,
    input logic [NUM_PIXELS-1:0] enable,
    input logic [7:0] count,
    output logic [NUM_PIXELS-1:0] [7:0] stored_values
);
    always_ff @(posedge clk) begin
        if (reset) begin
            for (int i = 0; i < NUM_PIXELS; i++) begin
                stored_values[i] <= 8'b0;
            end
        end else begin
            for (int i = 0; i < NUM_PIXELS; i++) begin
                if (enable[i])
                    stored_values[i] <= count; // Sample counter value at rising edge of comparator output
            end
        end
    end

endmodule
