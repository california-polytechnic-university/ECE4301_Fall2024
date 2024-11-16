`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 10/09/2024 03:20:47 AM
// Design Name: 
// Module Name: UART_TX
// Project Name: 
// Target Devices: 
// Tool Versions: 
// Description: 
// 
// Dependencies: 
// 
// Revision:
// Revision 0.01 - File Created
// Additional Comments:
// 
//////////////////////////////////////////////////////////////////////////////////


module UART_TX (
    input wire clk,              // System clock
    input wire rst,              // Reset signal
    input wire [7:0] tx_data,    // 8-bit data to send
    input wire send,             // Trigger to send data
    output reg tx,               // UART transmit line
    output reg ready             // UART ready to send next byte
);
    parameter CLOCK_FREQ = 100_000_000;  // System clock frequency (100 MHz for Nexys A7-100T)
    parameter BAUD_RATE = 9600;          // Baud rate (9600 is common for UART)
    
    localparam BAUD_TICK = CLOCK_FREQ / BAUD_RATE; // Clock cycles per UART bit

    // UART state machine states
    localparam [1:0]
        IDLE  = 2'b00,
        START = 2'b01,
        DATA  = 2'b10,
        STOP  = 2'b11;

    reg [1:0] state;            // State variable for the state machine
    reg [15:0] baud_counter;    // Counter for baud rate generation
    reg [2:0] bit_index;        // Counter for bits being sent (0-7)
    reg [7:0] tx_buffer;        // Data buffer to hold data while being sent

    // Sequential logic for UART transmission
    always @(posedge clk or posedge rst) begin
        if (rst) begin
            state <= IDLE;
            baud_counter <= 0;
            bit_index <= 0;
            ready <= 1;
            tx <= 1;            // UART line is idle-high when not transmitting
        end else begin
            case (state)
                IDLE: begin
                    ready <= 1; // Ready to send
                    if (send) begin
                        tx_buffer <= tx_data;  // Load the data to be sent
                        state <= START;        // Move to the start bit
                        ready <= 0;            // Not ready while sending
                        baud_counter <= 0;
                    end
                end
                
                START: begin
                    tx <= 0;  // Start bit is '0'
                    if (baud_counter == BAUD_TICK - 1) begin
                        baud_counter <= 0;
                        state <= DATA;     // Move to sending data bits
                        bit_index <= 0;
                    end else begin
                        baud_counter <= baud_counter + 1;
                    end
                end
                
                DATA: begin
                    tx <= tx_buffer[bit_index];  // Send current bit
                    if (baud_counter == BAUD_TICK - 1) begin
                        baud_counter <= 0;
                        if (bit_index == 7) begin
                            state <= STOP;  // After 8 bits, go to stop bit
                        end else begin
                            bit_index <= bit_index + 1;  // Move to next bit
                        end
                    end else begin
                        baud_counter <= baud_counter + 1;
                    end
                end
                
                STOP: begin
                    tx <= 1;  // Stop bit is '1'
                    if (baud_counter == BAUD_TICK - 1) begin
                        baud_counter <= 0;
                        state <= IDLE;  // Return to idle state after stop bit
                        ready <= 1;     // Ready to send next byte
                    end else begin
                        baud_counter <= baud_counter + 1;
                    end
                end
                
                default: state <= IDLE;
            endcase
        end
    end
endmodule
