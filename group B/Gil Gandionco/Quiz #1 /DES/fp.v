`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 10/09/2024 02:38:01 AM
// Design Name: 
// Module Name: final_permutation
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


module final_permutation (
    input  [63:0] in,
    output [63:0] out
);
    // Standard FP table adjusted for Verilog's 0-based indexing
    assign out[63] = in[39];  // FP[1]  = 40
    assign out[62] = in[7];   // FP[2]  = 8
    assign out[61] = in[47];  // FP[3]  = 48
    assign out[60] = in[15];  // FP[4]  = 16
    assign out[59] = in[55];  // FP[5]  = 56
    assign out[58] = in[23];  // FP[6]  = 24
    assign out[57] = in[63];  // FP[7]  = 64
    assign out[56] = in[31];  // FP[8]  = 32
    assign out[55] = in[38];  // FP[9]  = 39
    assign out[54] = in[6];   // FP[10] = 7
    assign out[53] = in[46];  // FP[11] = 47
    assign out[52] = in[14];  // FP[12] = 15
    assign out[51] = in[54];  // FP[13] = 55
    assign out[50] = in[22];  // FP[14] = 23
    assign out[49] = in[62];  // FP[15] = 63
    assign out[48] = in[30];  // FP[16] = 31
    assign out[47] = in[37];  // FP[17] = 38
    assign out[46] = in[5];   // FP[18] = 6
    assign out[45] = in[45];  // FP[19] = 46
    assign out[44] = in[13];  // FP[20] = 14
    assign out[43] = in[53];  // FP[21] = 54
    assign out[42] = in[21];  // FP[22] = 22
    assign out[41] = in[61];  // FP[23] = 62
    assign out[40] = in[29];  // FP[24] = 30
    assign out[39] = in[36];  // FP[25] = 37
    assign out[38] = in[4];   // FP[26] = 5
    assign out[37] = in[44];  // FP[27] = 45
    assign out[36] = in[12];  // FP[28] = 13
    assign out[35] = in[52];  // FP[29] = 53
    assign out[34] = in[20];  // FP[30] = 21
    assign out[33] = in[60];  // FP[31] = 61
    assign out[32] = in[28];  // FP[32] = 29
    assign out[31] = in[35];  // FP[33] = 36
    assign out[30] = in[3];   // FP[34] = 4
    assign out[29] = in[43];  // FP[35] = 44
    assign out[28] = in[11];  // FP[36] = 12
    assign out[27] = in[51];  // FP[37] = 52
    assign out[26] = in[19];  // FP[38] = 20
    assign out[25] = in[59];  // FP[39] = 60
    assign out[24] = in[27];  // FP[40] = 28
    assign out[23] = in[34];  // FP[41] = 35
    assign out[22] = in[2];   // FP[42] = 3
    assign out[21] = in[42];  // FP[43] = 43
    assign out[20] = in[10];  // FP[44] = 11
    assign out[19] = in[50];  // FP[45] = 51
    assign out[18] = in[18];  // FP[46] = 19
    assign out[17] = in[58];  // FP[47] = 59
    assign out[16] = in[26];  // FP[48] = 27
    assign out[15] = in[33];  // FP[49] = 34
    assign out[14] = in[1];   // FP[50] = 2
    assign out[13] = in[41];  // FP[51] = 42
    assign out[12] = in[9];   // FP[52] = 10
    assign out[11] = in[49];  // FP[53] = 50
    assign out[10] = in[17];  // FP[54] = 18
    assign out[9]  = in[57];  // FP[55] = 58
    assign out[8]  = in[25];  // FP[56] = 26
    assign out[7]  = in[32];  // FP[57] = 33
    assign out[6]  = in[0];   // FP[58] = 1
    assign out[5]  = in[40];  // FP[59] = 41
    assign out[4]  = in[8];   // FP[60] = 9
    assign out[3]  = in[48];  // FP[61] = 49
    assign out[2]  = in[16];  // FP[62] = 17
    assign out[1]  = in[56];  // FP[63] = 57
    assign out[0]  = in[24];  // FP[64] = 25
endmodule