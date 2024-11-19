

module f(input [32:1] R, input [48:1] K, output [32:1] OUT);
  wire [48:1] R_E;
  E E_inst(R, R_E);

  wire [48:1] T = R_E ^ K;

  wire [6:1] S1_in, S2_in, S3_in, S4_in, S5_in, S6_in, S7_in, S8_in;
  assign {S1_in, S2_in, S3_in, S4_in, S5_in, S6_in, S7_in, S8_in} = T;

  wire [4:1] S1_out, S2_out, S3_out, S4_out, S5_out, S6_out, S7_out, S8_out;
  S1 S1_inst(S1_in, S1_out);
  S2 S2_inst(S2_in, S2_out);
  S3 S3_inst(S3_in, S3_out);
  S4 S4_inst(S4_in, S4_out);
  S5 S5_inst(S5_in, S5_out);
  S6 S6_inst(S6_in, S6_out);
  S7 S7_inst(S7_in, S7_out);
  S8 S8_inst(S8_in, S8_out);

  wire [32:1] S_out = {S1_out, S2_out, S3_out, S4_out, S5_out, S6_out, S7_out, S8_out};
  P P_inst(S_out, OUT);
endmodule

module KS_left_shift(input [5:1] level, input [28:1] in, output [28:1] out);
  assign out = (level == 1 || level == 2 || level == 9 || level == 16) ?
                {in[27:1], in[28]} : {in[26:1], in[28:27]};
endmodule

module KS(input [64:1] key, output [48:1] k1,
                            output [48:1] k2,
                            output [48:1] k3,
                            output [48:1] k4,
                            output [48:1] k5,
                            output [48:1] k6,
                            output [48:1] k7,
                            output [48:1] k8,
                            output [48:1] k9,
                            output [48:1] k10,
                            output [48:1] k11,
                            output [48:1] k12,
                            output [48:1] k13,
                            output [48:1] k14,
                            output [48:1] k15,
                            output [48:1] k16);
  wire [56:1] key_pc1;
  PC1 pc1_inst(key, key_pc1);

  wire [28:1] c [0:16];
  wire [28:1] d [0:16];
  wire [48:1] k [1:16];

  assign {c[0], d[0]} = key_pc1;

  genvar i;
  generate
    for (i = 1; i <= 16; i = i + 1) begin : blk
      wire [5:1] j = i;
      KS_left_shift KS_ls_inst1(j, c[i - 1], c[i]);
      KS_left_shift KS_ls_inst2(j, d[i - 1], d[i]);
      PC2 pc2_inst({c[i], d[i]}, k[i]);
    end
  endgenerate

  assign k1 = k[1];
  assign k2 = k[2];
  assign k3 = k[3];
  assign k4 = k[4];
  assign k5 = k[5];
  assign k6 = k[6];
  assign k7 = k[7];
  assign k8 = k[8];
  assign k9 = k[9];
  assign k10 = k[10];
  assign k11 = k[11];
  assign k12 = k[12];
  assign k13 = k[13];
  assign k14 = k[14];
  assign k15 = k[15];
  assign k16 = k[16];
endmodule

module DES(input [64:1] in, input [64:1] key, output [64:1] decryption_out, output [64:1] encryption_out);
  // Encryption Phase
  wire [64:1] in_ip;
  IP ip_inst(in, in_ip);  // Initial permutation

  wire [32:1] l_enc [0:16];
  wire [32:1] r_enc [0:16];
  wire [32:1] f_val_enc [1:16];
  assign {l_enc[0], r_enc[0]} = in_ip;

  wire [48:1] k [1:16]; // Round keys for encryption and decryption
  KS ks_inst(key, k[1], k[2], k[3], k[4], k[5], k[6], k[7], k[8], k[9],
                  k[10], k[11], k[12], k[13], k[14], k[15], k[16]);

  // Encryption rounds
  genvar i;
  generate
    for (i = 1; i <= 16; i = i + 1) begin : enc_blk
      assign l_enc[i] = r_enc[i - 1];
      f f_inst(r_enc[i - 1], k[i], f_val_enc[i]);
      assign r_enc[i] = l_enc[i - 1] ^ f_val_enc[i];
    end
  endgenerate

  wire [64:1] enc_out_ip_inv;
  IP_inv ip_inv_enc_inst({r_enc[16], l_enc[16]}, enc_out_ip_inv); // Ciphertext after encryption
  assign encryption_out = enc_out_ip_inv;

  // Decryption Phase (uses the same DES rounds with keys in reverse order)
  wire [64:1] in_ip_dec;
  IP ip_dec_inst(enc_out_ip_inv, in_ip_dec);  // Initial permutation for decryption

  wire [32:1] l_dec [0:16];
  wire [32:1] r_dec [0:16];
  wire [32:1] f_val_dec [1:16];
  assign {l_dec[0], r_dec[0]} = in_ip_dec;

  // Decryption rounds (same process but keys are used in reverse)
  generate
    for (i = 1; i <= 16; i = i + 1) begin : dec_blk
      assign l_dec[i] = r_dec[i - 1];
      f f_inst_dec(r_dec[i - 1], k[17 - i], f_val_dec[i]); // Reverse order of keys
      assign r_dec[i] = l_dec[i - 1] ^ f_val_dec[i];
    end
  endgenerate

  // Final output after decryption
  IP_inv ip_inv_dec_inst({r_dec[16], l_dec[16]}, decryption_out); // Plaintext after decryption
endmodule
