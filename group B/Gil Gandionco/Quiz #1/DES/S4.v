`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 10/09/2024 02:36:21 AM
// Design Name: 
// Module Name: sbox4
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


module sbox4 (
    input  [5:0] in,        // 6-bit input
    output reg [3:0] out    // 4-bit output
);

    // Internal signals for row and column
    wire [1:0] row;
    wire [3:0] col;

    // Extract the row (first and last bits) and column (middle 4 bits)
    assign row = {in[5], in[0]};   // Row is formed from bits 1 and 6
    assign col = in[4:1];          // Column is formed from bits 2, 3, 4, 5

    // S-Box 4 lookup
    always @(*) begin
        case (row)
            2'b00: begin  // Row 0
                case (col)
                    4'd0:  out = 4'h7;  // 7
                    4'd1:  out = 4'hD;  // 13
                    4'd2:  out = 4'hE;  // 14
                    4'd3:  out = 4'h3;  // 3
                    4'd4:  out = 4'h0;  // 0
                    4'd5:  out = 4'h6;  // 6
                    4'd6:  out = 4'h9;  // 9
                    4'd7:  out = 4'hA;  // 10
                    4'd8:  out = 4'h1;  // 1
                    4'd9:  out = 4'h2;  // 2
                    4'd10: out = 4'h8;  // 8
                    4'd11: out = 4'h5;  // 5
                    4'd12: out = 4'hB;  // 11
                    4'd13: out = 4'hC;  // 12
                    4'd14: out = 4'h4;  // 4
                    4'd15: out = 4'hF;  // 15
                    default: out = 4'h0;
                endcase
            end
            2'b01: begin  // Row 1
                case (col)
                    4'd0:  out = 4'hD;  // 13
                    4'd1:  out = 4'h8;  // 8
                    4'd2:  out = 4'hB;  // 11
                    4'd3:  out = 4'h5;  // 5
                    4'd4:  out = 4'h6;  // 6
                    4'd5:  out = 4'hF;  // 15
                    4'd6:  out = 4'h0;  // 0
                    4'd7:  out = 4'h3;  // 3
                    4'd8:  out = 4'h4;  // 4
                    4'd9:  out = 4'h7;  // 7
                    4'd10: out = 4'h2;  // 2
                    4'd11: out = 4'hC;  // 12
                    4'd12: out = 4'h1;  // 1
                    4'd13: out = 4'hA;  // 10
                    4'd14: out = 4'hE;  // 14
                    4'd15: out = 4'h9;  // 9
                    default: out = 4'h0;
                endcase
            end
            2'b10: begin  // Row 2
                case (col)
                    4'd0:  out = 4'hA;  // 10
                    4'd1:  out = 4'h6;  // 6
                    4'd2:  out = 4'h9;  // 9
                    4'd3:  out = 4'h0;  // 0
                    4'd4:  out = 4'hC;  // 12
                    4'd5:  out = 4'hB;  // 11
                    4'd6:  out = 4'h7;  // 7
                    4'd7:  out = 4'hD;  // 13
                    4'd8:  out = 4'hF;  // 15
                    4'd9:  out = 4'h1;  // 1
                    4'd10: out = 4'h3;  // 3
                    4'd11: out = 4'hE;  // 14
                    4'd12: out = 4'h5;  // 5
                    4'd13: out = 4'h2;  // 2
                    4'd14: out = 4'h8;  // 8
                    4'd15: out = 4'h4;  // 4
                    default: out = 4'h0;
                endcase
            end
            2'b11: begin  // Row 3
                case (col)
                    4'd0:  out = 4'h3;  // 3
                    4'd1:  out = 4'hF;  // 15
                    4'd2:  out = 4'h0;  // 0
                    4'd3:  out = 4'h6;  // 6
                    4'd4:  out = 4'hA;  // 10
                    4'd5:  out = 4'h1;  // 1
                    4'd6:  out = 4'hD;  // 13
                    4'd7:  out = 4'h8;  // 8
                    4'd8:  out = 4'h9;  // 9
                    4'd9:  out = 4'h4;  // 4
                    4'd10: out = 4'h5;  // 5
                    4'd11: out = 4'hB;  // 11
                    4'd12: out = 4'hC;  // 12
                    4'd13: out = 4'h7;  // 7
                    4'd14: out = 4'h2;  // 2
                    4'd15: out = 4'hE;  // 14
                    default: out = 4'h0;
                endcase
            end
            default: out = 4'h0;  // Default to 0 if invalid
        endcase
    end

endmodule