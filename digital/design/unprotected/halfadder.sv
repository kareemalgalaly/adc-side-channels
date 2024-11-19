module halfadder (
    input wire a,
    input wire b,

    output wire s,
    output wire c 
);

assign  s = a ^ b;
assign  c = a & b;

endmodule

