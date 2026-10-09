`timescale 1ns / 1ps

module main (
    // AD9484 Data Clock Output
    input  wire       clk_p,
    input  wire       clk_n,

    // AD9484 8-bit LVDS data
    input  wire [7:0] data_p,
    input  wire [7:0] data_n,

    // FT2232H Channel B UART
    output wire       uart_tx
);

    // ============================================================
    // Parameters
    // ============================================================

    localparam integer CLOCK_HZ    = 500_000_000;
    localparam integer UART_BAUD   = 115200;

    // 65536 samples x 8 bits = 64 KiB
    localparam integer NUM_SAMPLES = 65536;


    // ============================================================
    // AD9484 DCO input
    // ============================================================

    wire adc_dco_ibuf;
    wire adc_clk;

    IBUFDS #(
        .DIFF_TERM("FALSE"),
        .IOSTANDARD("LVDS_25")
    ) adc_dco_input (
        .I  (clk_p),
        .IB (clk_n),
        .O  (adc_dco_ibuf)
    );

    BUFG adc_dco_bufg (
        .I(adc_dco_ibuf),
        .O(adc_clk)
    );


    // ============================================================
    // AD9484 data inputs
    // ============================================================

    wire [7:0] adc_data_wire;

    genvar i;

    generate
        for (i = 0; i < 8; i = i + 1) begin : ADC_DATA_INPUTS

            IBUFDS #(
                .DIFF_TERM("FALSE"),
                .IOSTANDARD("LVDS_25")
            ) adc_data_ibuf (
                .I  (data_p[i]),
                .IB (data_n[i]),
                .O  (adc_data_wire[i])
            );

        end
    endgenerate


    // ============================================================
    // Input register
    //
    // Keep this register in the FPGA I/O cells.
    // AD9484 data is captured on rising DCO edge.
    // ============================================================

    (* IOB = "TRUE" *)
    reg [7:0] adc_data_reg = 8'h00;

    always @(posedge adc_clk) begin
        adc_data_reg <= adc_data_wire;
    end


    // ============================================================
    // Sample BRAM
    //
    // 65536 x 8 = 524288 bits
    // ============================================================

    (* ram_style = "block" *)
    reg [7:0] sample_mem [0:NUM_SAMPLES-1];

    reg [15:0] write_addr = 16'd0;
    reg [15:0] read_addr  = 16'd0;


    // ============================================================
    // UART interface
    // ============================================================

    reg  [7:0] uart_data  = 8'h00;
    reg        uart_start = 1'b0;

    wire uart_busy;
    wire uart_done;

    uart_tx #(
        .CLOCK_HZ(CLOCK_HZ),
        .BAUD(UART_BAUD)
    ) uart (
        .clk     (adc_clk),
        .start   (uart_start),
        .data_in (uart_data),

        .tx      (uart_tx),
        .busy    (uart_busy),
        .done    (uart_done)
    );


    // ============================================================
    // Capture / transmit state machine
    // ============================================================

    localparam [2:0]
        ST_ARM      = 3'd0,
        ST_CAPTURE  = 3'd1,
        ST_READ     = 3'd2,
        ST_TX_START = 3'd3,
        ST_TX_WAIT  = 3'd4,
        ST_DONE     = 3'd5;

    reg [2:0] state = ST_ARM;


    always @(posedge adc_clk) begin

        // UART start is a one-clock pulse
        uart_start <= 1'b0;

        case (state)

            // ----------------------------------------------------
            // Wait one clock so adc_data_reg contains a valid sample
            // ----------------------------------------------------

            ST_ARM: begin
                write_addr <= 16'd0;
                read_addr  <= 16'd0;

                state <= ST_CAPTURE;
            end


            // ----------------------------------------------------
            // Capture 65536 ADC samples
            // ----------------------------------------------------

            ST_CAPTURE: begin

                sample_mem[write_addr] <= adc_data_reg;

                if (write_addr == 16'hFFFF) begin
                    read_addr <= 16'd0;
                    state <= ST_READ;
                end
                else begin
                    write_addr <= write_addr + 1'b1;
                end

            end


            // ----------------------------------------------------
            // BRAM synchronous read
            // ----------------------------------------------------

            ST_READ: begin

                uart_data <= sample_mem[read_addr];

                state <= ST_TX_START;

            end


            // ----------------------------------------------------
            // Start UART transmitter
            // ----------------------------------------------------

            ST_TX_START: begin

                if (!uart_busy) begin
                    uart_start <= 1'b1;
                    state <= ST_TX_WAIT;
                end

            end


            // ----------------------------------------------------
            // Wait for current byte to finish
            // ----------------------------------------------------

            ST_TX_WAIT: begin

                if (uart_done) begin

                    if (read_addr == 16'hFFFF) begin
                        state <= ST_DONE;
                    end
                    else begin
                        read_addr <= read_addr + 1'b1;
                        state <= ST_READ;
                    end

                end

            end


            // ----------------------------------------------------
            // Entire capture has been transmitted.
            //
            // Reprogram FPGA to make another capture.
            // ----------------------------------------------------

            ST_DONE: begin
                state <= ST_DONE;
            end


            default: begin
                state <= ST_ARM;
            end

        endcase
    end

endmodule



// ============================================================================
// UART TRANSMITTER
//
// 8 data bits
// no parity
// 1 stop bit
// LSB first
// ============================================================================

module uart_tx #(
    parameter integer CLOCK_HZ = 250_000_000,
    parameter integer BAUD     = 115200
)(
    input  wire       clk,
    input  wire       start,
    input  wire [7:0] data_in,

    output reg        tx   = 1'b1,
    output reg        busy = 1'b0,
    output reg        done = 1'b0
);

    localparam integer CLKS_PER_BIT = CLOCK_HZ / BAUD;

    localparam [2:0]
        UART_IDLE  = 3'd0,
        UART_START = 3'd1,
        UART_DATA  = 3'd2,
        UART_STOP  = 3'd3,
        UART_DONE  = 3'd4;

    reg [2:0] state = UART_IDLE;

    reg [31:0] clock_count = 32'd0;

    reg [2:0] bit_index = 3'd0;

    reg [7:0] data_latched = 8'h00;


    always @(posedge clk) begin

        done <= 1'b0;

        case (state)

            // ----------------------------------------------------
            // Idle
            // ----------------------------------------------------

            UART_IDLE: begin

                tx          <= 1'b1;
                busy        <= 1'b0;
                clock_count <= 32'd0;
                bit_index   <= 3'd0;

                if (start) begin
                    data_latched <= data_in;

                    busy  <= 1'b1;
                    state <= UART_START;
                end

            end


            // ----------------------------------------------------
            // Start bit
            // ----------------------------------------------------

            UART_START: begin

                tx <= 1'b0;

                if (clock_count == CLKS_PER_BIT - 1) begin
                    clock_count <= 32'd0;
                    state <= UART_DATA;
                end
                else begin
                    clock_count <= clock_count + 1'b1;
                end

            end


            // ----------------------------------------------------
            // Eight data bits, LSB first
            // ----------------------------------------------------

            UART_DATA: begin

                tx <= data_latched[bit_index];

                if (clock_count == CLKS_PER_BIT - 1) begin

                    clock_count <= 32'd0;

                    if (bit_index == 3'd7) begin
                        bit_index <= 3'd0;
                        state <= UART_STOP;
                    end
                    else begin
                        bit_index <= bit_index + 1'b1;
                    end

                end
                else begin
                    clock_count <= clock_count + 1'b1;
                end

            end


            // ----------------------------------------------------
            // Stop bit
            // ----------------------------------------------------

            UART_STOP: begin

                tx <= 1'b1;

                if (clock_count == CLKS_PER_BIT - 1) begin
                    clock_count <= 32'd0;
                    state <= UART_DONE;
                end
                else begin
                    clock_count <= clock_count + 1'b1;
                end

            end


            // ----------------------------------------------------
            // Finished
            // ----------------------------------------------------

            UART_DONE: begin

                tx   <= 1'b1;
                busy <= 1'b0;
                done <= 1'b1;

                state <= UART_IDLE;

            end


            default: begin
                state <= UART_IDLE;
            end

        endcase

    end

endmodule
