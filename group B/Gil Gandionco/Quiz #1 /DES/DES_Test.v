`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 10/09/2024 02:32:16 AM
// Design Name: 
// Module Name: DES_Test
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

module DES_Test(
    input        clk,             // System clock
    input        rst,             // Reset signal
    input        start,           // Start signal for encryption/decryption
    output       tx,              // UART transmit line
    output       tx_done          // Signal indicating UART transmission is done
);

    // Hardcoded key (64-bit DES key)
    reg [63:0] key = 64'h133457799BBCDFF1;  // Example hardcoded key

    // Hardcoded plaintext (64-bit)
    reg [63:0] plaintext = 64'h37A593FB5C1CAC09;  // Example hardcoded plaintext
    //reg [63:0] plaintext = 64'h0123456789ABCDEF;  // Example hardcoded plaintext


    // Internal signals
    reg [63:0] ciphertext;        // 64-bit ciphertext result
    reg [63:0] decrypted_text;    // 64-bit decrypted text result
    wire [63:0] initial_permuted; // Data after Initial Permutation (IP)
    wire [63:0] final_permuted;   // Data after Final Permutation (FP)
    reg  [31:0] left, right;
    wire [47:0] round_keys[0:15]; // 16 48-bit round keys from the key schedule
    wire [31:0] feistel_out;      // Output from Feistel function
    reg  [4:0] round_counter;     // Round counter for 16 rounds
    reg        encrypt;           // Encryption/Decryption mode
    reg [63:0] pre_output;        // Holds swapped halves before final permutation

    // UART Signals
    reg [7:0] uart_data;          // Data byte to send via UART
    reg       uart_send;          // Signal to send data via UART
    wire      uart_ready;         // UART ready for the next byte
    reg [7:0] char_count;         // Character counter for UART transmission
    reg [1:0] state;              // FSM state
    localparam [1:0] IDLE = 2'b00, SEND_CHAR = 2'b01, WAIT_READY = 2'b10;

    // Registers to hold the key, plaintext, ciphertext, and decrypted text for transmission
    reg [63:0] key_reg;
    reg [63:0] plain_reg;
    reg [63:0] cipher_reg;
    reg [63:0] decrypted_reg;

    // Instantiate the Initial Permutation (IP)
    initial_permutation ip_inst (
        .in(encrypt ? plaintext : ciphertext),
        .out(initial_permuted)
    );

    // Instantiate the Final Permutation (FP)
    final_permutation fp_inst (
        .in(pre_output),       // Swapped halves are input to FP
        .out(final_permuted)
    );

    // Instantiate the key schedule module to generate round keys
    des_key_schedule key_schedule_inst (
        .key(key),
        .round_key_1(round_keys[0]),
        .round_key_2(round_keys[1]),
        .round_key_3(round_keys[2]),
        .round_key_4(round_keys[3]),
        .round_key_5(round_keys[4]),
        .round_key_6(round_keys[5]),
        .round_key_7(round_keys[6]),
        .round_key_8(round_keys[7]),
        .round_key_9(round_keys[8]),
        .round_key_10(round_keys[9]),
        .round_key_11(round_keys[10]),
        .round_key_12(round_keys[11]),
        .round_key_13(round_keys[12]),
        .round_key_14(round_keys[13]),
        .round_key_15(round_keys[14]),
        .round_key_16(round_keys[15])
    );

    // Instantiate the Feistel function
    feistel_function feistel_inst (
        .R_in(right),                                     // Right half of the data
        .round_key(encrypt ? round_keys[round_counter - 1] : round_keys[15 - (round_counter - 1)]), // Round key
        .R_out(feistel_out)                               // Output from the Feistel function
    );

    // UART Transmitter
    UART_TX uart_tx_inst (
        .clk(clk),
        .rst(rst),
        .tx_data(uart_data),        // 8-bit data to transmit
        .send(uart_send),           // Send data signal
        .tx(tx),                    // UART transmit line
        .ready(uart_ready)          // Ready to send next byte
    );

    // Function to convert 4-bit nibble to corresponding ASCII hex character
    function [7:0] nibble_to_ascii(input [3:0] nibble);
        begin
            if (nibble < 4'd10)
                nibble_to_ascii = 8'h30 + nibble; // '0' to '9'
            else
                nibble_to_ascii = 8'h41 + (nibble - 4'd10); // 'A' to 'F'
        end
    endfunction

    // Main DES Process (Perform encryption, decryption, and transmit over UART)
    always @(posedge clk) begin
        if (rst) begin
            // Reset all registers
            left <= 32'b0;
            right <= 32'b0;
            round_counter <= 0;
            char_count <= 0;
            uart_send <= 0;
            uart_data <= 8'h00;
            key_reg <= key;
            plain_reg <= plaintext;
            cipher_reg <= 64'b0;
            decrypted_reg <= 64'b0;
            state <= IDLE;
            encrypt <= 1'b1;  // Start with encryption
            pre_output <= 64'b0;
            ciphertext <= 64'b0;
            decrypted_text <= 64'b0;
        end else if (start) begin
            if (round_counter == 0) begin
                // Initial permutation
                left <= initial_permuted[63:32];
                right <= initial_permuted[31:0];
                round_counter <= round_counter + 1;
            end else if (round_counter <= 16) begin
                // Perform one round of DES (16 rounds total)
                left <= right;
                right <= left ^ feistel_out;
                round_counter <= round_counter + 1;
            end else if (round_counter == 17) begin
                // Swap halves after 16 rounds
                pre_output <= {right, left}; // Swap halves
                round_counter <= round_counter + 1;
            end else if (round_counter == 18) begin
                // Apply Final Permutation and store results
                if (encrypt) begin
                    ciphertext <= final_permuted;  // Store ciphertext
                    cipher_reg <= final_permuted;  // For UART transmission
                    encrypt <= 1'b0;               // Switch to decryption
                    round_counter <= 0;            // Reset round counter
                end else begin
                    decrypted_text <= final_permuted;  // Store decrypted text
                    decrypted_reg <= final_permuted;   // For UART transmission
                    round_counter <= 0;
                end
            end
        end

        // FSM to send the key, plaintext, ciphertext, and decrypted text as ASCII hex characters over UART
        case (state)
            IDLE: begin
                if (uart_ready) begin
                    if (char_count == 0) begin
                        key_reg <= key;
                        plain_reg <= plaintext;
                        cipher_reg <= ciphertext;
                        decrypted_reg <= decrypted_text;
                    end
                    state <= SEND_CHAR;
                end
            end

            SEND_CHAR: begin
                uart_send <= 1;
                if (char_count < 5) begin
                    // Send "Key: " prefix
                    case (char_count)
                        0: uart_data <= "K";
                        1: uart_data <= "e";
                        2: uart_data <= "y";
                        3: uart_data <= ":";
                        4: uart_data <= " ";
                    endcase
                end else if (char_count >= 5 && char_count < 21) begin
                    // Send key in ASCII hex (16 nibbles)
                    uart_data <= nibble_to_ascii(key_reg[63:60]);
                    key_reg <= {key_reg[59:0], 4'b0000};  // Shift left by 4 bits
                end else if (char_count >= 21 && char_count < 33) begin
                    // Send " PlainText: " prefix (12 characters)
                    case (char_count - 21)
                        0: uart_data <= " ";
                        1: uart_data <= "P";
                        2: uart_data <= "l";
                        3: uart_data <= "a";
                        4: uart_data <= "i";
                        5: uart_data <= "n";
                        6: uart_data <= "T";
                        7: uart_data <= "e";
                        8: uart_data <= "x";
                        9: uart_data <= "t";
                        10: uart_data <= ":";
                        11: uart_data <= " ";
                    endcase
                end else if (char_count >= 33 && char_count < 49) begin
                    // Send plaintext in ASCII hex (16 nibbles)
                    uart_data <= nibble_to_ascii(plain_reg[63:60]); //extracts the most significant 4 bits and convert to the corresponding ASCII
                    plain_reg <= {plain_reg[59:0], 4'b0000};  // Shift left by 4 bits
                end else if (char_count >= 49 && char_count < 62) begin
                    // Send " CipherText: " prefix (13 characters)
                    case (char_count - 49)
                        0: uart_data <= " ";
                        1: uart_data <= "C";
                        2: uart_data <= "i";
                        3: uart_data <= "p";
                        4: uart_data <= "h";
                        5: uart_data <= "e";
                        6: uart_data <= "r";
                        7: uart_data <= "T";
                        8: uart_data <= "e";
                        9: uart_data <= "x";
                        10: uart_data <= "t";
                        11: uart_data <= ":";
                        12: uart_data <= " ";
                    endcase
                end else if (char_count >= 62 && char_count < 78) begin
                    // Send ciphertext in ASCII hex (16 nibbles)
                    uart_data <= nibble_to_ascii(cipher_reg[63:60]);
                    cipher_reg <= {cipher_reg[59:0], 4'b0000};  // Shift left by 4 bits
                end else if (char_count >= 78 && char_count < 94) begin
                    // Send " DecryptedText: " prefix (16 characters)
                    case (char_count - 78)
                        0: uart_data <= " ";
                        1: uart_data <= "D";
                        2: uart_data <= "e";
                        3: uart_data <= "c";
                        4: uart_data <= "r";
                        5: uart_data <= "y";
                        6: uart_data <= "p";
                        7: uart_data <= "t";
                        8: uart_data <= "e";
                        9: uart_data <= "d";
                        10: uart_data <= "T";
                        11: uart_data <= "e";
                        12: uart_data <= "x";
                        13: uart_data <= "t";
                        14: uart_data <= ":";
                        15: uart_data <= " ";
                    endcase
                end else if (char_count >= 94 && char_count < 110) begin
                    // Send decrypted text in ASCII hex (16 nibbles)
                    uart_data <= nibble_to_ascii(decrypted_reg[63:60]);
                    decrypted_reg <= {decrypted_reg[59:0], 4'b0000};  // Shift left by 4 bits
                end else if (char_count == 110) begin
                    uart_data <= 8'h0D;  // CR (Carriage Return)
                end else if (char_count == 111) begin
                    uart_data <= 8'h0A;  // LF (Line Feed)
                end
                state <= WAIT_READY;
            end

            WAIT_READY: begin
                uart_send <= 0;
                if (uart_ready) begin
                    if (char_count == 111) begin
                        char_count <= 0;  // Reset for next transmission
                    end else begin
                        char_count <= char_count + 1;
                    end
                    state <= IDLE;
                end
            end

            default: state <= IDLE;
        endcase
    end

    assign tx_done = (char_count == 0);  // Transmission is done when char_count is reset
endmodule


