module d_flip_flop (
    input  logic clk,  
    input  logic rstn, 
    input  logic D,    
    output logic Q     
);

    always @(posedge clk or negedge rstn) begin
        if (!rstn) begin
            Q <= 1'b0; 
        end else begin
            Q <= D;    
        end
    end

endmodule