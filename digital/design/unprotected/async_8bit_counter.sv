module async_8bit_counter (
    input  logic clk,      
    input  logic rstn,    
    output logic [7:0] Q  
);

logic [7:0] D; 

always_comb begin
    D[0] = ~Q[0];
    for (int i = 1; i < 8; i++) begin
        D[i] = Q[i-1] ^ Q[i]; 
    end
end

   
d_flip_flop dff0 (.clk(clk), .rstn(rstn), .D(D[0]), .Q(Q[0]));
d_flip_flop dff1 (.clk(clk), .rstn(rstn), .D(D[1]), .Q(Q[1]));
d_flip_flop dff2 (.clk(clk), .rstn(rstn), .D(D[2]), .Q(Q[2]));
d_flip_flop dff3 (.clk(clk), .rstn(rstn), .D(D[3]), .Q(Q[3]));
d_flip_flop dff4 (.clk(clk), .rstn(rstn), .D(D[4]), .Q(Q[4]));
d_flip_flop dff5 (.clk(clk), .rstn(rstn), .D(D[5]), .Q(Q[5]));
d_flip_flop dff6 (.clk(clk), .rstn(rstn), .D(D[6]), .Q(Q[6]));
d_flip_flop dff7 (.clk(clk), .rstn(rstn), .D(D[7]), .Q(Q[7]));

endmodule