module control (
    // dclk drst dcomp dstart_over
    input  clk,
    input  rstn,
    input  comp_out,
    input  restart,
    // drs dre db dvld dc7 dc6 dc5 dc4 dc3 dc2 dc1 dc0
    output counter_rst,
    output counter_en,
    output ramp_reset,
    output ramp_en,
    output busy,
    output valid,
    output [7:0] count
);

typedef enum {
    RESET,
    IDLE,
    START,
    COUNT,
    DONE
} state_e;

state_e state_d;
state_e state_q;

always_comb begin
    if (rstn == 0) begin
        state_d = RESET;
    end
    else begin // transitions
        state_d = state_q;

        case (state_q)
            RESET : if (rstn == 1)      state_d = IDLE;
            IDLE  : if (restart == 1)   state_d = START;
            START :                     state_d = COUNT;
            COUNT : if (!counter_rst)   state_d = DONE;
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

    counter_rst <= !rstn || (count == '1);
end

// need safe values for these in power-off cases
assign ramp_reset = !rstn || state_q == START; // || state_q == RESET
assign ramp_en    = rstn && state_q == COUNT; 
assign busy       = rstn && state_q != IDLE; // restartn would be accepted if not busy
assign valid      = rstn && state_q == DONE;
assign counter_en = rstn && state_q == COUNT; // we need these two lines
assign counter_rst = !rstn || state_q = START;


endmodule
