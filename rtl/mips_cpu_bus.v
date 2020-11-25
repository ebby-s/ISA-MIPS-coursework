module mips_cpu_bus(
    /* Standard signals */
    input  logic        clk,
    input  logic        reset,
    output logic        active,
    output logic[31:0]  register_v0,

    /* Avalon memory mapped bus controller (master) */
    input  logic        waitrequest,
    input  logic[31:0]  readdata
    output logic        write,
    output logic        read,
    output logic[3:0]   byteenable,
    output logic[31:0]  writedata,
    output logic[31:0]  address,
);
      // 4 possible states, clock enable is low when entering the fetch states
    typedef enum logic[1:0] {
        DATA_FETCH = 2'b00
        DATA_WRITE = 2'b01
        INSTR_FETCH = 2'b10
        CHILLING = 2'b11
    } state_t;

    /* these are combinatorial signals, assigned in always_comb */
    logic clk_enable;
    logic data_read;
    logic data_write;
    logic[31:0] instr_addr;
    logic[31:0] readinstr;
    logic[31:0] data_addr;
    logic[31:0] readdata;
    logic[1:0] next_state;

    /* these are sequential, updated in always_ff */
    logic[1:0] state;

      // these store values read from memory, needed to simulate combinatorial access to memory
    logic[31:0] instr_reg;      // stores instruction read from memory
    logic[31:0] data_reg;       // stores data read from memory

       // stores previous instruction address, required to detect when the instruction address changes
    logic[31:0] instr_addr_reg;


    always_comb begin
        byteenable = 4'hF;   // changing this would require changing the declaration for mips_cpu_harvard

          // this determines the next state, however, state only changes if waitrequest is low, see always_ff
        if (instr_addr_reg != instr_addr) begin
            next_state = INSTR_FETCH;
        end
        else if (data_Read) begin
            next_state = DATA_FETCH;
        end
        else if (data_write) begin
            next_state = DATA_WRITE;
        end
        else begin
            next_state = CHILLING;
        end

        address = (next_state == INSTR_FETCH) ? instr_addr : data_addr;
        write = (next_state == DATA_WRITE);
        read = ((next_state == INSTR_FETCH) || (next_state == DATA_FETCH));

        readinstr = (state==INSTR_FETCH) ? readdata : instr_reg;
        readdata = (state==DATA_FETCH) ? readdata : data_reg;

          // the harvard cpu will be stalled when waitrequest is high or if a fetch is required
        clk_enable = (~waitrequest && (next_state[0] != 0));
    end

    always_ff @(posedge clk) begin
        if (reset) begin
            instr_reg <= 0;
            data_reg <= 0;
            instr_addr_reg <= 0;
            state <= CHILLING;
        end
        else if (~waitrequest) begin
            instr_addr_reg <= instr_addr;
            data_reg <= (state==DATA_FETCH) ? readdata : data_reg;
            instr_reg <= (state==INSTR_FETCH) ? readdata : instr_reg;
            state <= next_state;
        end
    end

    mips_cpu_harvard harvard_cpu(
        .clk(clk),
        .reset(reset),
        .active(active),
        .register_v0(register_v0),

        .clk_enable(clk_enable),

        .instr_readdata(readinstr),
        .instr_address(instr_addr),

        .data_readdata(readdata),
        .data_write(data_write),
        .data_read(data_read),
        .data_writedata(writedata),
        .data_address(data_addr),
    );

endmodule
