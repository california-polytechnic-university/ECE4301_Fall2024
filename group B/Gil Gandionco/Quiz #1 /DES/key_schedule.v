`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 10/09/2024 02:37:29 AM
// Design Name: 
// Module Name: key_schedule
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

module des_key_schedule (
    input [63:0] key,
    output [47:0] round_key_1,
    output [47:0] round_key_2,
    output [47:0] round_key_3,
    output [47:0] round_key_4,
    output [47:0] round_key_5,
    output [47:0] round_key_6,
    output [47:0] round_key_7,
    output [47:0] round_key_8,
    output [47:0] round_key_9,
    output [47:0] round_key_10,
    output [47:0] round_key_11,
    output [47:0] round_key_12,
    output [47:0] round_key_13,
    output [47:0] round_key_14,
    output [47:0] round_key_15,
    output [47:0] round_key_16
);

    // Permuted Choice 1 (PC-1)
    wire [55:0] key_56 = {
        key[56], key[48], key[40], key[32], key[24], key[16], key[8],
        key[0],  key[57], key[49], key[41], key[33], key[25], key[17],
        key[9],  key[1],  key[58], key[50], key[42], key[34], key[26],
        key[18], key[10], key[2],  key[59], key[51], key[43], key[35],
        key[62], key[54], key[46], key[38], key[30], key[22], key[14],
        key[6],  key[61], key[53], key[45], key[37], key[29], key[21],
        key[13], key[5],  key[60], key[52], key[44], key[36], key[28],
        key[20], key[12], key[4],  key[27], key[19], key[11], key[3]
    };

    // Split the key into left and right halves
    wire [27:0] C0 = key_56[55:28];
    wire [27:0] D0 = key_56[27:0];

    // Perform left shifts and generate round keys
    // Round 1
    wire [27:0] C1 = {C0[26:0], C0[27]}; //takes the least significant 27 bits of C0 and adds the most significant bit C0(27)
    wire [27:0] D1 = {D0[26:0], D0[27]}; //rotating the bits one position to the left
    assign round_key_1 = permuted_choice_2(C1, D1); //PC-2 selects 48 specific bits from the concatenation of C1 and D1 to form a 48-bit round key.

    // Round 2
    wire [27:0] C2 = {C1[26:0], C1[27]};
    wire [27:0] D2 = {D1[26:0], D1[27]};
    assign round_key_2 = permuted_choice_2(C2, D2);

    // Round 3
    wire [27:0] C3 = {C2[25:0], C2[27:26]};
    wire [27:0] D3 = {D2[25:0], D2[27:26]};
    assign round_key_3 = permuted_choice_2(C3, D3);

    // Round 4
    wire [27:0] C4 = {C3[25:0], C3[27:26]};
    wire [27:0] D4 = {D3[25:0], D3[27:26]};
    assign round_key_4 = permuted_choice_2(C4, D4);

    // Round 5
    wire [27:0] C5 = {C4[25:0], C4[27:26]};
    wire [27:0] D5 = {D4[25:0], D4[27:26]};
    assign round_key_5 = permuted_choice_2(C5, D5);

    // Round 6
    wire [27:0] C6 = {C5[25:0], C5[27:26]};
    wire [27:0] D6 = {D5[25:0], D5[27:26]};
    assign round_key_6 = permuted_choice_2(C6, D6);

    // Round 7
    wire [27:0] C7 = {C6[25:0], C6[27:26]};
    wire [27:0] D7 = {D6[25:0], D6[27:26]};
    assign round_key_7 = permuted_choice_2(C7, D7);

    // Round 8
    wire [27:0] C8 = {C7[25:0], C7[27:26]};
    wire [27:0] D8 = {D7[25:0], D7[27:26]};
    assign round_key_8 = permuted_choice_2(C8, D8);

    // Round 9
    wire [27:0] C9 = {C8[26:0], C8[27]};
    wire [27:0] D9 = {D8[26:0], D8[27]};
    assign round_key_9 = permuted_choice_2(C9, D9);

    // Round 10
    wire [27:0] C10 = {C9[25:0], C9[27:26]};
    wire [27:0] D10 = {D9[25:0], D9[27:26]};
    assign round_key_10 = permuted_choice_2(C10, D10);

    // Round 11
    wire [27:0] C11 = {C10[25:0], C10[27:26]};
    wire [27:0] D11 = {D10[25:0], D10[27:26]};
    assign round_key_11 = permuted_choice_2(C11, D11);

    // Round 12
    wire [27:0] C12 = {C11[25:0], C11[27:26]};
    wire [27:0] D12 = {D11[25:0], D11[27:26]};
    assign round_key_12 = permuted_choice_2(C12, D12);

    // Round 13
    wire [27:0] C13 = {C12[25:0], C12[27:26]};
    wire [27:0] D13 = {D12[25:0], D12[27:26]};
    assign round_key_13 = permuted_choice_2(C13, D13);

    // Round 14
    wire [27:0] C14 = {C13[25:0], C13[27:26]};
    wire [27:0] D14 = {D13[25:0], D13[27:26]};
    assign round_key_14 = permuted_choice_2(C14, D14);

    // Round 15
    wire [27:0] C15 = {C14[25:0], C14[27:26]};
    wire [27:0] D15 = {D14[25:0], D14[27:26]};
    assign round_key_15 = permuted_choice_2(C15, D15);

    // Round 16
    wire [27:0] C16 = {C15[26:0], C15[27]};
    wire [27:0] D16 = {D15[26:0], D15[27]};
    assign round_key_16 = permuted_choice_2(C16, D16);

    // Permuted Choice 2 (PC-2) function
    function [47:0] permuted_choice_2;
        input [27:0] C_in;
        input [27:0] D_in;
        reg [55:0] CD;
        begin
            CD = {C_in, D_in};
            permuted_choice_2 = {
                CD[13], CD[16], CD[10], CD[23], CD[0],  CD[4],
                CD[2],  CD[27], CD[14], CD[5],  CD[20], CD[9],
                CD[22], CD[18], CD[11], CD[3],  CD[25], CD[7],
                CD[15], CD[6],  CD[26], CD[19], CD[12], CD[1],
                CD[40], CD[51], CD[30], CD[36], CD[46], CD[54],
                CD[29], CD[39], CD[50], CD[44], CD[32], CD[47],
                CD[43], CD[48], CD[38], CD[55], CD[33], CD[52],
                CD[45], CD[41], CD[49], CD[35], CD[28], CD[31]
            };
        end
    endfunction

endmodule