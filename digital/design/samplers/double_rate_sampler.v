//*****************************************************************************
// File        : digital/design/samplers/double_rate_sampler.v
// Author      : kareem
// Created     : 2025 Mar 27
// Description : 
//*****************************************************************************

module double_rate_sampler #(
    parameter WIDTH=8
) (
    input clk,
    input rst, 
    input comp,
    input [WIDTH-1:0] counter
    output reg [WIDTH-1:0] count_true,
    output reg [WIDTH-1:0] count_false
);

reg reset_cycle; // 1 on posedge 0 on negedge of main clk
reg comp_d;

always @(posedge clk) begin
    if (rst) begin
        count_true  <= 0;
        count_false <= 0;
        reset_cycle <= 1;
    end
    else begin
        reset_cycle <= ~reset_cycle;
        if (reset_cycle) count_false <= 0;
        else begin
            comp_d <= comp;
            if (comp && ~comp_d) begin
                count_true <= counter;
            end
            else begin
                count_false <= counter;
            end
        end
    end
end

endmodule

