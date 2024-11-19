`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 10/07/2024 01:51:15 AM
// Design Name: 
// Module Name: uart_rx
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


module uart_rx (
    input wire clk,           // System clock
    input wire rst,           // Reset signal
    input wire rx,            // UART receive pin
    output reg [7:0] rx_data, // 8-bit data received
    output reg rx_ready       // Flag indicating data is ready
);

    parameter BAUD_RATE = 9600;
    parameter CLOCK_FREQ = 100_000_000;  // 100 MHz clock frequency
    localparam BAUD_TICKS = CLOCK_FREQ / BAUD_RATE;

    reg [15:0] baud_counter;
    reg [3:0] bit_index;
    reg [7:0] shift_reg;
    reg receiving;

    always @(posedge clk or posedge rst) begin
        if (rst) begin
            baud_counter <= 0;
            bit_index <= 0;
            rx_data <= 0;
            rx_ready <= 0;
            receiving <= 0;
        end else if (!receiving && rx == 0) begin  // Detect start bit
            receiving <= 1;
            baud_counter <= BAUD_TICKS / 2;  // Center of the start bit
            bit_index <= 0;
            rx_ready <= 0;
        end else if (receiving) begin
            if (baud_counter == BAUD_TICKS - 1) begin
                baud_counter <= 0;
                if (bit_index == 8) begin
                    rx_ready <= 1;
                    rx_data <= shift_reg;
                    receiving <= 0;  // End of reception
                end else begin
                    shift_reg[bit_index] <= rx;
                    bit_index <= bit_index + 1;
                end
            end else begin
                baud_counter <= baud_counter + 1;
            end
        end
    end
endmodule

