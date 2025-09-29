//*****************************************************************************
// File        : counter_half.v
// Author      : kareemahmad
// Created     : 2025 Jan 01
// Description : Half-adder based counter model.
//
// rst : 0 1 0 . . .
// cnt : X X 0 0 1 2
// sum : X X 0 1 2 2
// en  : 0 0 0 1 1 0
//*****************************************************************************

module half_addr (
    input A, 
    input B,
    output C,
    output S
);
    assign S = A ^ B;
    assign C = A & B;
endmodule


module counter_half #(
    parameter WIDTH = 8
) (
    input  clk,
    input  rst,
    input  en,
    output reg [WIDTH-1:0] count,
    output reg overflow
);

    wire [WIDTH-1:0] sum;
    wire [WIDTH-1:0] carry;
    wire [WIDTH-1:0] oper2;

    assign oper2[0] = en;
    assign oper2[WIDTH-1:1] = carry[WIDTH-2:0];

    genvar i;
    generate
        for (i = 0; i < WIDTH; i+=1) begin
            half_addr half_adder(
                .A(count[i]),
                .B(oper2[i]),
                .C(carry[i]),
                .S(sum[i])
            );
        end
    endgenerate

    always @(posedge clk) begin
        if (rst) begin
            count    <= 0;
            overflow <= 0;
        end 
        else begin
            count    <= sum;
            overflow <= carry[WIDTH-1];
        end
    end

endmodule
