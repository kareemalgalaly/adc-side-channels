module bitAdder (
    input [7:0] a,
    input b,
    output [7:0] s
);

wire [7:0] carry;

halfadder ha1(.a(a[0]), .b(b),        .s(s[0]), .c(carry[0]));
halfadder ha2(.a(a[1]), .b(carry[0]), .s(s[1]), .c(carry[1]));
halfadder ha3(.a(a[2]), .b(carry[1]), .s(s[2]), .c(carry[2]));
halfadder ha4(.a(a[3]), .b(carry[2]), .s(s[3]), .c(carry[3]));
halfadder ha5(.a(a[4]), .b(carry[3]), .s(s[4]), .c(carry[4]));
halfadder ha6(.a(a[5]), .b(carry[4]), .s(s[5]), .c(carry[5]));
halfadder ha7(.a(a[6]), .b(carry[5]), .s(s[6]), .c(carry[6]));
halfadder ha8(.a(a[7]), .b(carry[6]), .s(s[7]), .c(carry[7]));

//generate
//    genvar i=0;
//    for (i=1; i<7; i+=1) begin
//        halfadder ha(.a(a[i]), .b(carry[i-1]), .s(s[i]), .c(carry[i]));
//    end
//endgenerate

endmodule
