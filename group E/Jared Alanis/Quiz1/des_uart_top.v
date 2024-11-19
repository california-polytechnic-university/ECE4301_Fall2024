`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 10/07/2024 01:52:31 AM
// Design Name: 
// Module Name: des_uart_top
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


module des_uart_top(
    input wire clk,            // 100 MHz system clock
    input wire rst,
    input wire [3:0] key_switch,
    input wire [3:0] message_switch,           // Reset signal
    output wire tx              // UART transmission line for output to Tera Term
);

    // Output wires for the DES result
    wire [63:0] encryption_out;
    wire [63:0] decryption_out;

    wire [63:0] data_in;   // Example input data
    wire [63:0] key; 
    
    // Instance of key and message selector
    key_message_selector selector (
        .key_switch(key_switch),
        .message_switch(message_switch),
        .selected_key(key),
        .selected_message(data_in)
    );

    // DES instance
    DES des_inst (
        .in(data_in),                     // Data input to DES
        .key(key),                        // Key input to DES
        .encryption_out(encryption_out),   // Encryption output of DES
        .decryption_out(decryption_out)    // Decryption output of DES
    );

    // UART Transmitter instantiation
    wire tx_ready;             // Signal to indicate UART is ready to send
    reg [7:0] uart_data;       // Byte of data to send over UART
    reg uart_send;             // Signal to trigger UART transmission
    reg [8:0] char_count;      // Counter to send 16 hex chars + CR + LF (18 total)

    uart_tx uart_tx_inst (
        .clk(clk),
        .rst(rst),
        .tx_data(uart_data),
        .send(uart_send),
        .tx(tx),
        .ready(tx_ready)
    );

    // Function to convert 4-bit nibble to corresponding ASCII hex character
    function [7:0] nibble_to_ascii(input [3:0] nibble);
        begin
            nibble_to_ascii = (nibble < 4'hA) ? (8'h30 + nibble) : (8'h41 + (nibble - 4'hA));
        end
    endfunction

    // Register to store output pattern
    reg [63:0] key_reg;
    reg [63:0] plain_reg;
    reg [63:0] encryption_reg;
    reg [63:0] decryption_reg;

    // State machine states
    localparam [1:0]
        IDLE = 2'b00,
        SEND_CHAR = 2'b01,
        WAIT_READY = 2'b10;

    reg [1:0] state;

    // FSM to send the 64-bit pattern as ASCII hex characters over UART
always @(posedge clk or posedge rst) begin
    if (rst) begin
        char_count <= 0;
        uart_send <= 0;
        uart_data <= 8'h00;
        key_reg <= key;
        plain_reg <= data_in;
        encryption_reg <= encryption_out;
        decryption_reg <= decryption_out;
        
        state <= IDLE;
    end else begin
        case (state)
            IDLE: begin
                if (tx_ready) begin
                    if (char_count == 0) begin
                        // Reload registers for new output line
                        key_reg <= key;
                        plain_reg <= data_in;
                        encryption_reg <= encryption_out;
                        decryption_reg <= decryption_out;
                    end
                    state <= SEND_CHAR;
                end
            end

            SEND_CHAR: begin
                // Send "Key: "
                if (char_count < 5) begin
                    case (char_count)
                    0: uart_data <= "K";
                    1: uart_data <= "e";
                    2: uart_data <= "y";
                    3: uart_data <= ":";
                    4: uart_data <= " ";
                    endcase

                // Send key (16 hex digits)
                end else if (char_count >= 5 && char_count < 21) begin
                    uart_data <= nibble_to_ascii(key_reg[63:60]);
                    key_reg <= {key_reg[59:0], 4'b0000};  // Shift left by 4 bits

                // Send " PlainText: "
                end else if (char_count >= 21 && char_count < 33) begin
                    case (char_count - 21)
                    0:  uart_data <= " ";
                    1:  uart_data <= "P";
                    2:  uart_data <= "l";
                    3:  uart_data <= "a";
                    4:  uart_data <= "i";
                    5:  uart_data <= "n";
                    6:  uart_data <= "T";
                    7:  uart_data <= "e";
                    8:  uart_data <= "x";
                    9:  uart_data <= "t";
                    10: uart_data <= ":";
                    11: uart_data <= " ";
                    endcase

                // Send plaintext (16 hex digits)
                end else if (char_count >= 33 && char_count < 49) begin
                    uart_data <= nibble_to_ascii(plain_reg[63:60]);
                    plain_reg <= {plain_reg[59:0], 4'b0000};  // Shift left by 4 bits

                // Send " EncryptedText: "
                end else if (char_count >= 49 && char_count < 65) begin
                    case (char_count - 49)
                    0:  uart_data <= " ";
                    1:  uart_data <= "E";
                    2:  uart_data <= "n";
                    3:  uart_data <= "c";
                    4:  uart_data <= "r";
                    5:  uart_data <= "y";
                    6:  uart_data <= "p";
                    7:  uart_data <= "t";
                    8:  uart_data <= "e";
                    9:  uart_data <= "d";
                    10: uart_data <= "T";
                    11: uart_data <= "e";
                    12: uart_data <= "x";
                    13: uart_data <= "t";
                    14: uart_data <= ":";
                    15: uart_data <= " ";
                    endcase

                // Send encrypted text (16 hex digits)
                end else if (char_count >= 65 && char_count < 81) begin
                    uart_data <= nibble_to_ascii(encryption_reg[63:60]);
                    encryption_reg <= {encryption_reg[59:0], 4'b0000};  // Shift left by 4 bits

                // Send CR + LF
                end else if (char_count == 81) begin
                    uart_data <= 8'h0D;  // CR (Carriage Return)
                end else if (char_count == 82) begin
                    uart_data <= 8'h0A;  // LF (Line Feed)

                // Send " DecryptedText: "
                end else if (char_count >= 83 && char_count < 99) begin
                    case (char_count - 83)
                    0:  uart_data <= "D";
                    1:  uart_data <= "e";
                    2:  uart_data <= "c";
                    3:  uart_data <= "r";
                    4:  uart_data <= "y";
                    5:  uart_data <= "p";
                    6:  uart_data <= "t";
                    7:  uart_data <= "e";
                    8:  uart_data <= "d";
                    9:  uart_data <= "T";
                    10: uart_data <= "e";
                    11: uart_data <= "x";
                    12: uart_data <= "t";
                    13: uart_data <= ":";
                    14: uart_data <= " ";
                    endcase

                // Send decrypted text (16 hex digits)
                end else if (char_count >= 99 && char_count < 115) begin
                    uart_data <= nibble_to_ascii(decryption_reg[63:60]);
                    decryption_reg <= {decryption_reg[59:0], 4'b0000};  // Shift left by 4 bits

                // Send final CR + LF
                end else if (char_count == 115) begin
                    uart_data <= 8'h0D;  // CR (Carriage Return)
                end else if (char_count == 116) begin
                    uart_data <= 8'h0A;  // LF (Line Feed)
                end

                uart_send <= 1;
                state <= WAIT_READY;
            end

            WAIT_READY: begin
                uart_send <= 0;
                if (tx_ready) begin
                    if (char_count == 116) begin
                        char_count <= 0;
                    end else begin
                        char_count <= char_count + 1;
                    end
                    state <= IDLE;
                end
            end

            default: state <= IDLE;
        endcase
    end
end

endmodule
