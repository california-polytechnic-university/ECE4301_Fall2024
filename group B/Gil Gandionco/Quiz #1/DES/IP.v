`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 10/09/2024 02:33:44 AM
// Design Name: 
// Module Name: initial_permutation
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


module initial_permutation (
    input  [63:0] in,
    output [63:0] out
);
    // Standard IP table adjusted for Verilog's 0-based indexing
    assign out[63] = in[57];  // IP[1]  = 58
    assign out[62] = in[49];  // IP[2]  = 50
    assign out[61] = in[41];  // IP[3]  = 42
    assign out[60] = in[33];  // IP[4]  = 34
    assign out[59] = in[25];  // IP[5]  = 26
    assign out[58] = in[17];  // IP[6]  = 18
    assign out[57] = in[9];   // IP[7]  = 10
    assign out[56] = in[1];   // IP[8]  = 2
    assign out[55] = in[59];  // IP[9]  = 60
    assign out[54] = in[51];  // IP[10] = 52
    assign out[53] = in[43];  // IP[11] = 44
    assign out[52] = in[35];  // IP[12] = 36
    assign out[51] = in[27];  // IP[13] = 28
    assign out[50] = in[19];  // IP[14] = 20
    assign out[49] = in[11];  // IP[15] = 12
    assign out[48] = in[3];   // IP[16] = 4
    assign out[47] = in[61];  // IP[17] = 62
    assign out[46] = in[53];  // IP[18] = 54
    assign out[45] = in[45];  // IP[19] = 46
    assign out[44] = in[37];  // IP[20] = 38
    assign out[43] = in[29];  // IP[21] = 30
    assign out[42] = in[21];  // IP[22] = 22
    assign out[41] = in[13];  // IP[23] = 14
    assign out[40] = in[5];   // IP[24] = 6
    assign out[39] = in[63];  // IP[25] = 64
    assign out[38] = in[55];  // IP[26] = 56
    assign out[37] = in[47];  // IP[27] = 48
    assign out[36] = in[39];  // IP[28] = 40
    assign out[35] = in[31];  // IP[29] = 32
    assign out[34] = in[23];  // IP[30] = 24
    assign out[33] = in[15];  // IP[31] = 16
    assign out[32] = in[7];   // IP[32] = 8
    assign out[31] = in[56];  // IP[33] = 57
    assign out[30] = in[48];  // IP[34] = 49
    assign out[29] = in[40];  // IP[35] = 41
    assign out[28] = in[32];  // IP[36] = 33
    assign out[27] = in[24];  // IP[37] = 25
    assign out[26] = in[16];  // IP[38] = 17
    assign out[25] = in[8];   // IP[39] = 9
    assign out[24] = in[0];   // IP[40] = 1
    assign out[23] = in[58];  // IP[41] = 59
    assign out[22] = in[50];  // IP[42] = 51
    assign out[21] = in[42];  // IP[43] = 43
    assign out[20] = in[34];  // IP[44] = 35
    assign out[19] = in[26];  // IP[45] = 27
    assign out[18] = in[18];  // IP[46] = 19
    assign out[17] = in[10];  // IP[47] = 11
    assign out[16] = in[2];   // IP[48] = 3
    assign out[15] = in[60];  // IP[49] = 61
    assign out[14] = in[52];  // IP[50] = 53
    assign out[13] = in[44];  // IP[51] = 45
    assign out[12] = in[36];  // IP[52] = 37
    assign out[11] = in[28];  // IP[53] = 29
    assign out[10] = in[20];  // IP[54] = 21
    assign out[9]  = in[12];  // IP[55] = 13
    assign out[8]  = in[4];   // IP[56] = 5
    assign out[7]  = in[62];  // IP[57] = 63
    assign out[6]  = in[54];  // IP[58] = 55
    assign out[5]  = in[46];  // IP[59] = 47
    assign out[4]  = in[38];  // IP[60] = 39
    assign out[3]  = in[30];  // IP[61] = 31
    assign out[2]  = in[22];  // IP[62] = 23
    assign out[1]  = in[14];  // IP[63] = 15
    assign out[0]  = in[6];   // IP[64] = 7
endmodule
