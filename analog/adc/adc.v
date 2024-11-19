module control (
    // dclk drst dcomp dstart_over
    input  clk,
    input  rstn,
    input  comp_out,
    input  restart,
    // drs dre db dvld dc7 dc6 dc5 dc4 dc3 dc2 dc1 dc0
    output ramp_reset,
    output ramp_en,
    output busy,
    output valid,
    output reg [7:0] count
);

typedef enum {
    RESET,
    IDLE,
    START,
    COUNT,
    DONE
    // DUMMY
} state_e;

state_e state_d;
state_e state_q;

// initial $display("Loaded verilog");

always @(*) begin
    if (rstn == 0) begin
        state_d = RESET;
    end
    else begin // transitions
        state_d = state_q;

        // question about restart overriding everything else or if it just needs to pulse
        case (state_q)
            RESET : if (rstn == 1)      state_d = IDLE;
            IDLE  : if (restart == 1)   state_d = START;
            START :                     state_d = COUNT;
            COUNT : if (comp_out == 1)  state_d = DONE;
            DONE  :                     state_d = IDLE;
        endcase
    end
end

always @(posedge clk) begin
    // if (rstn == 0) begin
    //     state <= RESET;
    // end
    // else begin
    state_q <= state_d;
    // end

    // $display("clk");

    if (state_d == START) count <= 0;
    else if (state_d == COUNT) count <= count + 1;
end

// need safe values for these in power-off cases
assign ramp_reset = rstn || state_q == START; // || state_q == RESET
assign ramp_en    = !rstn && state_q == COUNT; 
assign busy       = !rstn && state_q != IDLE; // restartn would be accepted if not busy
assign valid      = !rstn && state_q == DONE;

endmodule

