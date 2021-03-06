module mips_cpu_bus(
    /* Standard signals */
    input  logic         clk,
    input  logic         reset,
    output logic         active,
    output logic [31:0]  register_v0,

    /* Avalon memory mapped bus controller*/
    output logic [31:0]  address,
    output logic         write,
    output logic         read,
    input  logic         waitrequest,
    output logic [31:0]  writedata,
    output logic [3:0]   byteenable,
    input  logic [31:0]  readdata
);
      // 4 possible states, clock enable is low when entering the fetch states
    typedef enum logic[1:0] {
        DATA_FETCH  = 2'b00,
        DATA_WRITE  = 2'b01,
        INSTR_FETCH = 2'b10,
        WAITING     = 2'b11
    } state_t;

    /* these are combinatorial signals, assigned in always_comb */
    logic         clk_enable;
    logic         data_read_en;
    logic         data_write;
    logic [1:0]   next_state;
    logic [31:0]  instr_addr;
    logic [31:0]  instr_read;
    logic [31:0]  data_addr;
    logic [31:0]  data_read;
    logic         delayed;
    logic [3:0]   harvard_byteenable;

    /* these are sequential, updated in always_ff */
    logic [1:0]   state;

    // these store values read from memory, needed to simulate combinatorial access to memory
    logic [31:0]  instr_reg;      // stores instruction read from memory
    logic [31:0]  data_reg;       // stores data read from memory

    // stores previous addresses, required to detect when addresses change
    logic [31:0]  instr_addr_reg;


    always @(*) begin
        if ((next_state == INSTR_FETCH) || (next_state == DATA_FETCH)) begin
            byteenable = 4'hF;
        end
        else begin
            byteenable = harvard_byteenable;
        end

        // Determines next state - state only changes if 'waitrequest' is low
        if ((instr_addr_reg != instr_addr) && state != DATA_WRITE) begin
            next_state = INSTR_FETCH;
        end

        else if (data_read_en && state != DATA_FETCH && state != INSTR_FETCH) begin
            next_state = DATA_FETCH;
        end

        else if (data_write && state != DATA_WRITE) begin
            next_state = DATA_WRITE;
        end

        else begin
            next_state = WAITING;
        end

        // Harvard cpu will be stalled when 'waitrequest' is high or if fetch is required

        address = (next_state == INSTR_FETCH) ? instr_addr : data_addr;
        write   = (state == DATA_WRITE);
        read    = ((next_state == INSTR_FETCH) || (next_state == DATA_FETCH));
        clk_enable = !((waitrequest && (read || write)) || (delayed) || (next_state != WAITING) || (data_read_en && (state != DATA_FETCH)) || (instr_addr_reg != instr_addr));

        instr_read = ((((waitrequest && (read || write)) || delayed) && (next_state==INSTR_FETCH)) || (~((waitrequest && (read || write)) || delayed) && (state==INSTR_FETCH))) ? readdata : instr_reg;
        data_read  = ((((waitrequest && (read || write)) || delayed) && (next_state==DATA_FETCH))  || (~((waitrequest && (read || write)) || delayed) && (state==DATA_FETCH)))  ? readdata : data_reg;
    end

    always_ff @(posedge clk) begin
        if (reset) begin
            state          <= WAITING;
            delayed        <= 0;
            instr_reg      <= 0;
            data_reg       <= 0;
            instr_addr_reg <= 0;
        end

        else if (~(waitrequest && (read || write))) begin
            state          <= next_state;

            delayed        <= (waitrequest && (read || write));

            instr_addr_reg <= (next_state==INSTR_FETCH) ? instr_addr : instr_addr_reg;

            data_reg   <= ((delayed && (next_state==DATA_FETCH))  || (~delayed && (state==DATA_FETCH)))  ? readdata : data_reg;
            instr_reg  <= ((delayed && (next_state==INSTR_FETCH)) || (~delayed && (state==INSTR_FETCH))) ? readdata : instr_reg;
        end

        else begin
            delayed    <= (waitrequest && (read || write));
        end
    end

    /* Harvard CPU declaration */
    mips_cpu_harvard_mod harvard_cpu(
        .clk             (clk),
        .reset           (reset),
        .active          (active),
        .register_v0     (register_v0),

        .clk_enable      (clk_enable),

        .instr_readdata  (instr_read),
        .instr_address   (instr_addr),

        .data_readdata   (data_read),
        .data_write      (data_write),
        .data_byteenable (harvard_byteenable),
        .data_read       (data_read_en),
        .data_writedata  (writedata),
        .data_address    (data_addr)
    );

endmodule
