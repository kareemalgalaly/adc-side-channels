//*****************************************************************************
// File        : digital/design/samplers/double_rate_sampler.v
// Author      : kareem
// Created     : 2025 Mar 27
// Description : 
//*****************************************************************************

// multipart -----------------------------------------------

module pulse_detect (
    input clk,
    input rst, 
    input val,
    input en,
    output out
);

reg vald;

always @(posedge clk) begin
    if (rst) begin
        vald <= 0;
    end
    else if (en) begin
        vald <= val;
    end
end

assign out = val && ~vald;

endmodule : pulse_detect


module double_rate_sampler #(
    parameter WIDTH=8
) (
    input clk,
    input rst, 
    input comp,
    input compn,
    input      [WIDTH-1:0] counter,
    output reg [WIDTH-1:0] count_true,
    output reg [WIDTH-1:0] count_false
);

reg reset_cycle;
wire set_cycle;
assign set_cycle = ~reset_cycle;

(* keep *)
wire wen, wenn;

pulse_detect pdp (
    .clk (clk       ),
    .rst (rst       ),
    .val (comp      ),
    .en  (set_cycle ),
    .out (wen       )
);

pulse_detect pdn (
    .clk (clk       ),
    .rst (rst       ),
    .val (compn     ),
    .en  (set_cycle ),
    .out (wenn      )
);

always @(posedge clk) begin
    if (rst) begin
        count_true  <= 0;
        count_false <= 0;
        reset_cycle <= 0;
    end
    else begin
        reset_cycle <= ~reset_cycle;

        if (reset_cycle) begin
            count_false <= 0;
        end
        else begin
            if (wen) count_true  <= counter;
            else     count_false <= counter;
        end
    end
end

endmodule : double_rate_sampler

// version 2 -----------------------------------------------

module double_rate_sampler_v1 #(
    parameter WIDTH=8
) (
    input clk,
    input rst, 
    input comp,
    input compn,
    input [WIDTH-1:0] counter,
    output reg [WIDTH-1:0] count_true,
    output reg [WIDTH-1:0] count_false
);

reg reset_cycle; // 1 on posedge 0 on negedge of main clk
reg comp_d;
wire wen;
assign wen = comp && ~comp_d;

always @(posedge clk) begin
    if (rst) begin
        comp_d      <= 0;
        count_true  <= 0;
        count_false <= 0;
        reset_cycle <= 0;
    end
    else begin
        reset_cycle <= ~reset_cycle;
        if (reset_cycle) count_false <= 0;
        else begin
            comp_d <= comp;
            comp_dn <= compn;
            if (wen) begin
                count_true <= counter;
            end
            else begin
                count_false <= counter;
            end
        end
    end
end

reg comp_dn;
(* keep *)
wire wenn;
assign wenn = compn && ~comp_dn;

always @(posedge clk) begin
    if (rst) begin
        comp_dn <= 0;
    end
    else begin
        if (~reset_cycle) begin
            comp_dn <= compn;
        end
    end
end

endmodule

// original ------------------------------------------------

module double_rate_sampler_v0 #(
    parameter WIDTH=8
) (
    input clk,
    input rst, 
    input comp,
    input [WIDTH-1:0] counter,
    output reg [WIDTH-1:0] count_true,
    output reg [WIDTH-1:0] count_false
);

reg reset_cycle; // 1 on posedge 0 on negedge of main clk
reg comp_d;

always @(posedge clk) begin
    if (rst) begin
        comp_d      <= 0;
        count_true  <= 0;
        count_false <= 0;
        reset_cycle <= 0;
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

