module counter(
    input logic clk,
    input logic reset,
    output logic [7:0] count
);
    always_ff @(posedge clk) begin
        if (reset)
            count <= 8'b0; // Reset counter to 0
        else
            count <= count + 1; // Increment counter
    end

endmodule