__all__ = ['aes_encrypt', 'key_expansion', 'aes_ctr_decrypt', 'aes_decrypt_text']

import base64
from math import ceil

from .utils import bytes_to_intlist, intlist_to_bytes

BLOCK_SIZE_BYTES = 16

def aes_ctr_decrypt(data, key, counter):
    """
    Decrypt with aes in counter mode
    
    @param {int[]} data        cipher
    @param {int[]} key         16/24/32-Byte cipher key
    @param {instance} counter  Instance whose next_value function (@returns {int[]}  16-Byte block)
                               returns the next counter block
    @returns {int[]}           decrypted data
    """
    expanded_key = key_expansion(key)
    block_count = int(ceil(float(len(data)) / BLOCK_SIZE_BYTES))
    
    decrypted_data=[]
    for i in range(block_count):
        counter_block = counter.next_value()
        block = data[i*BLOCK_SIZE_BYTES : (i+1)*BLOCK_SIZE_BYTES]
        block += [0]*(BLOCK_SIZE_BYTES - len(block))
        
        cipher_counter_block = aes_encrypt(counter_block, expanded_key)
        decrypted_data += xor(block, cipher_counter_block)
    decrypted_data = decrypted_data[:len(data)]
    
    return decrypted_data

def key_expansion(data):
    """
    Generate key schedule
    
    @param {int[]} data  16/24/32-Byte cipher key
    @returns {int[]}     176/208/240-Byte expanded key 
    """
    data = data[:] # copy
    rcon_iteration = 1
    key_size_bytes = len(data)
    expanded_key_size_bytes = (key_size_bytes // 4 + 7) * BLOCK_SIZE_BYTES
    
    while len(data) < expanded_key_size_bytes:
        temp = data[-4:]
        temp = key_schedule_core(temp, rcon_iteration)
        rcon_iteration += 1
        data += xor(temp, data[-key_size_bytes : 4-key_size_bytes])
        
        for _ in range(3):
            temp = data[-4:]
            data += xor(temp, data[-key_size_bytes : 4-key_size_bytes])
        
        if key_size_bytes == 32:
            temp = data[-4:]
            temp = sub_bytes(temp)
            data += xor(temp, data[-key_size_bytes : 4-key_size_bytes])
        
        for _ in range(3 if key_size_bytes == 32  else 2 if key_size_bytes == 24 else 0):
            temp = data[-4:]
            data += xor(temp, data[-key_size_bytes : 4-key_size_bytes])
    data = data[:expanded_key_size_bytes]
    
    return data

def aes_encrypt(data, expanded_key):
    """
    Encrypt one block with aes
    
    @param {int[]} data          16-Byte state
    @param {int[]} expanded_key  176/208/240-Byte expanded key 
    @returns {int[]}             16-Byte cipher
    """
    rounds = len(expanded_key) // BLOCK_SIZE_BYTES - 1
    
    data = xor(data, expanded_key[:BLOCK_SIZE_BYTES])
    for i in range(1, rounds+1):
        data = sub_bytes(data)
        data = shift_rows(data)
        if i != rounds:
            data = mix_columns(data)
        data = xor(data, expanded_key[i*BLOCK_SIZE_BYTES : (i+1)*BLOCK_SIZE_BYTES])
    
    return data

def aes_decrypt_text(data, password, key_size_bytes):
    """
    Decrypt text
    - The first 8 Bytes of decoded 'data' are the 8 high Bytes of the counter
    - The cipher key is retrieved by encrypting the first 16 Byte of 'password'
      with the first 'key_size_bytes' Bytes from 'password' (if necessary filled with 0's)
    - Mode of operation is 'counter'
    
    @param {str} data                    Base64 encoded string
    @param {str,unicode} password        Password (will be encoded with utf-8)
    @param {int} key_size_bytes          Possible values: 16 for 128-Bit, 24 for 192-Bit or 32 for 256-Bit
    @returns {str}                       Decrypted data
    """
    NONCE_LENGTH_BYTES = 8
    
    data = bytes_to_intlist(base64.b64decode(data))
    password = bytes_to_intlist(password.encode('utf-8'))
    
    key = password[:key_size_bytes] + [0]*(key_size_bytes - len(password))
    key = aes_encrypt(key[:BLOCK_SIZE_BYTES], key_expansion(key)) * (key_size_bytes // BLOCK_SIZE_BYTES)
    
    nonce = data[:NONCE_LENGTH_BYTES]
    cipher = data[NONCE_LENGTH_BYTES:]
    
    class Counter:
        __value = nonce + [0]*(BLOCK_SIZE_BYTES - NONCE_LENGTH_BYTES)
        def next_value(self):
            temp = self.__value
            self.__value = inc(self.__value)
            return temp
    
    decrypted_data = aes_ctr_decrypt(cipher, key, Counter())
    plaintext = intlist_to_bytes(decrypted_data)
    
    return plaintext

RCON = (0x8d, 0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80, 0x1b, 0x36)
SBOX = (0x63, 0x7C, 0x77, 0x7B, 0xF2, 0x6B, 0x6F, 0xC5, 0x30, 0x01, 0x67, 0x2B, 0xFE, 0xD7, 0xAB, 0x76,
        0xCA, 0x82, 0xC9, 0x7D, 0xFA, 0x59, 0x47, 0xF0, 0xAD, 0xD4, 0xA2, 0xAF, 0x9C, 0xA4, 0x72, 0xC0,
        0xB7, 0xFD, 0x93, 0x26, 0x36, 0x3F, 0xF7, 0xCC, 0x34, 0xA5, 0xE5, 0xF1, 0x71, 0xD8, 0x31, 0x15,
        0x04, 0xC7, 0x23, 0xC3, 0x18, 0x96, 0x05, 0x9A, 0x07, 0x12, 0x80, 0xE2, 0xEB, 0x27, 0xB2, 0x75,
        0x09, 0x83, 0x2C, 0x1A, 0x1B, 0x6E, 0x5A, 0xA0, 0x52, 0x3B, 0xD6, 0xB3, 0x29, 0xE3, 0x2F, 0x84,
        0x53, 0xD1, 0x00, 0xED, 0x20, 0xFC, 0xB1, 0x5B, 0x6A, 0xCB, 0xBE, 0x39, 0x4A, 0x4C, 0x58, 0xCF,
        0xD0, 0xEF, 0xAA, 0xFB, 0x43, 0x4D, 0x33, 0x85, 0x45, 0xF9, 0x02, 0x7F, 0x50, 0x3C, 0x9F, 0xA8,
        0x51, 0xA3, 0x40, 0x8F, 0x92, 0x9D, 0x38, 0xF5, 0xBC, 0xB6, 0xDA, 0x21, 0x10, 0xFF, 0xF3, 0xD2,
        0xCD, 0x0C, 0x13, 0xEC, 0x5F, 0x97, 0x44, 0x17, 0xC4, 0xA7, 0x7E, 0x3D, 0x64, 0x5D, 0x19, 0x73,
        0x60, 0x81, 0x4F, 0xDC, 0x22, 0x2A, 0x90, 0x88, 0x46, 0xEE, 0xB8, 0x14, 0xDE, 0x5E, 0x0B, 0xDB,
        0xE0, 0x32, 0x3A, 0x0A, 0x49, 0x06, 0x24, 0x5C, 0xC2, 0xD3, 0xAC, 0x62, 0x91, 0x95, 0xE4, 0x79,
        0xE7, 0xC8, 0x37, 0x6D, 0x8D, 0xD5, 0x4E, 0xA9, 0x6C, 0x56, 0xF4, 0xEA, 0x65, 0x7A, 0xAE, 0x08,
        0xBA, 0x78, 0x25, 0x2E, 0x1C, 0xA6, 0xB4, 0xC6, 0xE8, 0xDD, 0x74, 0x1F, 0x4B, 0xBD, 0x8B, 0x8A,
        0x70, 0x3E, 0xB5, 0x66, 0x48, 0x03, 0xF6, 0x0E, 0x61, 0x35, 0x57, 0xB9, 0x86, 0xC1, 0x1D, 0x9E,
        0xE1, 0xF8, 0x98, 0x11, 0x69, 0xD9, 0x8E, 0x94, 0x9B, 0x1E, 0x87, 0xE9, 0xCE, 0x55, 0x28, 0xDF,
        0x8C, 0xA1, 0x89, 0x0D, 0xBF, 0xE6, 0x42, 0x68, 0x41, 0x99, 0x2D, 0x0F, 0xB0, 0x54, 0xBB, 0x16)
MIX_COLUMN_MATRIX = ((2,3,1,1),
                     (1,2,3,1),
                     (1,1,2,3),
                     (3,1,1,2))

def sub_bytes(data):
    return [SBOX[x] for x in data]

def rotate(data):
    return data[1:] + [data[0]]

def key_schedule_core(data, rcon_iteration):
    data = rotate(data)
    data = sub_bytes(data)
    data[0] = data[0] ^ RCON[rcon_iteration]
    
    return data

def xor(data1, data2):
    return [x^y for x, y in zip(data1, data2)]

def mix_column(data):
    data_mixed = []
    for row in range(4):
        mixed = 0
        for column in range(4):
            addend = data[column]
            if MIX_COLUMN_MATRIX[row][column] in (2,3):
                addend <<= 1
                if addend > 0xff:
                    addend &= 0xff
                    addend ^= 0x1b
                if MIX_COLUMN_MATRIX[row][column] == 3:
                    addend ^= data[column]
            mixed ^= addend & 0xff
        data_mixed.append(mixed)
    return data_mixed

def mix_columns(data):
    data_mixed = []
    for i in range(4):
        column = data[i*4 : (i+1)*4]
        data_mixed += mix_column(column)
    return data_mixed

def shift_rows(data):
    data_shifted = []
    for column in range(4):
        for row in range(4):
            data_shifted.append( data[((column + row) & 0b11) * 4 + row] )
    return data_shifted

def inc(data):
    data = data[:] # copy
    for i in range(len(data)-1,-1,-1):
        if data[i] == 255:
            data[i] = 0
        else:
            data[i] = data[i] + 1
            break
    return data
