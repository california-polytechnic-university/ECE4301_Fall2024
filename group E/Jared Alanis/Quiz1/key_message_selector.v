`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 10/07/2024 12:02:36 PM
// Design Name: 
// Module Name: key_message_selector
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


module key_message_selector(
    input wire [3:0] key_switch,
    input wire [3:0] message_switch,
    output reg [63:0] selected_key,
    output reg [63:0] selected_message
);

    always @(*) begin
        case(key_switch)
            4'b0000: selected_key = 64'hA1B2C3D4E5F61234;
            4'b0001: selected_key = 64'h1122334455667788;
            4'b0010: selected_key = 64'hAABBCCDDEEFF0011;
            4'b0011: selected_key = 64'hFEDCBA9876543210;
            4'b0100: selected_key = 64'h0123456789ABCDEF;
            4'b0101: selected_key = 64'hFFFEFDFCFBFAF9F8;
            4'b0110: selected_key = 64'h0F1E2D3C4B5A6978;
            4'b0111: selected_key = 64'hA5A5A5A5A5A5A5A5;
            4'b1000: selected_key = 64'h5A5A5A5A5A5A5A5A;
            4'b1001: selected_key = 64'h1234567890ABCDEF;
            4'b1010: selected_key = 64'hFEDCBA0987654321;
            4'b1011: selected_key = 64'h0000FFFFFFFF0000;
            4'b1100: selected_key = 64'hFFFF0000FFFF0000;
            4'b1101: selected_key = 64'h0F0F0F0F0F0F0F0F;
            4'b1110: selected_key = 64'hF0F0F0F0F0F0F0F0;
            4'b1111: selected_key = 64'h5555AAAA5555AAAA;
        endcase
    end

    always @(*) begin
        case(message_switch)
            4'b0000: selected_message = 64'hA9887654385ABCD1;
            4'b0001: selected_message = 64'h123456789ABCDEF0;
            4'b0010: selected_message = 64'hFEDCBA9876543210;
            4'b0011: selected_message = 64'h0123456789ABCDEF;
            4'b0100: selected_message = 64'hFFFFFFFFFFFFFFFF;
            4'b0101: selected_message = 64'h0000000000000000;
            4'b0110: selected_message = 64'hAAAAAAAAAAAAAAAA;
            4'b0111: selected_message = 64'h5555555555555555;
            4'b1000: selected_message = 64'h1111222233334444;
            4'b1001: selected_message = 64'h5555666677778888;
            4'b1010: selected_message = 64'h9999AAAABBBBCCCC;
            4'b1011: selected_message = 64'hDDDDEEEEFFFF0000;
            4'b1100: selected_message = 64'h0F0F0F0F0F0F0F0F;
            4'b1101: selected_message = 64'hF0F0F0F0F0F0F0F0;
            4'b1110: selected_message = 64'h0123456776543210;
            4'b1111: selected_message = 64'hFEDCBA9889ABCDEF;
        endcase
    end

endmodule
