//*****************************************************************************
// File        : counter_behav.v
// Author      : kareemahmad
// Created     : 2025 Jan 01
// Description : Behavioral counter model.
//
// rst : 0 1 0 . . .
// cnt : X X 0 0 1 2
// sum : X X 0 1 2 2
// en  : 0 0 0 1 1 0
//*****************************************************************************

module counter_behav #(
        parameter WIDTH = 8
    ) (
        input  clk,
        input  rst,
        input  en,
        input  set,
        input  [WIDTH-1:0] setval,
        output reg [WIDTH-1:0] count,
        output reg overflow
    );

    wire [WIDTH-1:0] wrdat;
    wire [WIDTH:0]   sum;

    assign sum = count + en;
    
    always @(posedge clk) begin
        if (rst) begin
            count    <= 0;
            overflow <= 0;
        end 
        else if (set) begin
            count    <= setval;
            overflow <= 0;
        end
        else begin
            count    <= sum[WIDTH-1:0];
            overflow <= sum[WIDTH];
        end
    end
endmodule

