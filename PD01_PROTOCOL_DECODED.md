# PD01 Printer Protocol - EXTRACTED FROM FUN PRINT APK

## Decompiled from: Fun Print APK
## Source Files:
- `com/xyz/yintibao/library/V5g.java` - Main protocol implementation
- `com/xyz/yintibao/OpencvUtilsWXModule.java` - Helper functions
- `com/wtx/ytbbleplugin/ytbBleFastV3Module.java` - BLE communication

## Protocol Structure

**Packet Format:**
```
[0x51][0x78][CMD][0x00][LEN_LO][LEN_HI][DATA...][CRC8][0xFF]
```

### Key Differences from Our Implementation:
1. ✅ Magic Header: `0x51 0x78` (we got this right)
2. ❌ **Separator**: `0x00` after CMD (we had this)
3. ❌ **Bit Ordering**: Uses MSB-first for bitmap packing (we changed to LSB - WRONG!)
4. ❌ **Command Codes**: Different codes than we used

## Command Codes (Java signed bytes → hex)

From `V5g.java`:
```java
byte[] quality1  = {81, 120, -92, 0, 1, 0, 49, -105, -1};
//                   51  78   A2 00 01 00  31   97   FF
// 0xA2 = Set Quality (not 0xA8 like we used!)

byte[] paper     = {81, 120, -95, 0, 2, 0, 48, 0, -7, -1};
//                   51  78   A1 00 02 00  30 00  F9  FF  
// 0xA1 = Feed Paper (not 0xB1!)

byte[] getDevState = {81, 120, -93, 0, 1, 0, 0, 0, -1};
//                     51  78   A3 00 01 00 00 00  FF
// 0xA3 = Get Device State

byte[] updateDev = {81, 120, -87, 0, 1, 0, 0, 0, -1};
//                  51  78   A9 00 01 00 00 00  FF
// 0xA9 = Update Device

byte[] printLattice = {81, 120, -90, 0, 11, 0, -86, 85, 23, 56, ...};
//                      51  78   A6 00 0B 00  AA  55  17  38 ...
// 0xA6 = Print Lattice (initialization pattern)
```

### Bitmap Row Command:
From code:
```java
bArr[i3]     = 81;    // 0x51
bArr[i3 + 1] = 120;   // 0x78  
bArr[i3 + 2] = -94;   // 0xA2 (CMD for bitmap row) - NOT 0x00!
bArr[i3 + 3] = 0;     // Separator
bArr[i3 + 4] = lenLo; // Length low byte
bArr[i3 + 5] = 0;     // Length high byte
// Then 48 bytes of bitmap data
// Then CRC8
// Then 0xFF
```

## Bitmap Bit Packing

From `eachLinePixToCmdB()`:
```java
byte b4 = (byte) (
    p0[src[i6 + 7]] +  // p0 = {0, 128} = bit 7 (MSB)
    p1[src[i6 + 6]] +  // p1 = {0, 64}  = bit 6
    p2[src[i6 + 5]] +  // p2 = {0, 32}  = bit 5
    p3[src[i6 + 4]] +  // p3 = {0, 16}  = bit 4
    p4[src[i6 + 3]] +  // p4 = {0, 8}   = bit 3
    p5[src[i6 + 2]] +  // p5 = {0, 4}   = bit 2
    p6[src[i6 + 1]] +  // p6 = {0, 2}   = bit 1
    src[i6]            //      {0, 1}   = bit 0 (LSB)
);
```

**This packs bits MSB-FIRST!** Not LSB-first.
- Pixel 0 → bit 0 (LSB)
- Pixel 7 → bit 7 (MSB)

## CRC8 Calculation

From `ConvertUtils.calcCrc8()`:
```java
public static byte calcCrc8(byte[] data, int offset, int length) {
    byte crc = 0;
    for (int i = offset; i < offset + length; i++) {
        crc ^= data[i];
        for (int j = 0; j < 8; j++) {
            if ((crc & 0x80) != 0) {
                crc = (byte) ((crc << 1) ^ 0x07);
            } else {
                crc = (byte) (crc << 1);
            }
        }
    }
    return crc;
}
```

**CRC8 is calculated on DATA ONLY** (not including header, CMD, length, or footer).

## Print Sequence

From `getPrintData()`:
```java
1. Quality command (0x51 0x78 0xA2 ...)
2. Print Lattice init (0x51 0x78 0xA6 ...)
3. [Optional] Energy command if eneragy != 0
4. Print Model command
5. Print Speed command
6. FOR EACH ROW:
   - Bitmap command (0x51 0x78 0xA2 0x00 [len] [48 bytes] [CRC8] 0xFF)
7. Paper feed commands (multiple based on paperNum)
8. Finish Lattice (0x51 0x78 0xA6 ...)
9. Get Device State (0x51 0x78 0xA3 ...)
```

## Length Encoding

**Little-endian 16-bit:**
```python
length = 48  # for bitmap row
LEN_LO = 0x30  # 48 & 0xFF
LEN_HI = 0x00  # (48 >> 8) & 0xFF
```

## Example Packets

**Quality 1:**
```
51 78 A2 00 01 00 31 97 FF
```

**Bitmap Row (48 bytes of data):**
```
51 78 A2 00 30 00 [48 bytes bitmap data] [CRC8] FF
```

**Feed Paper:**
```
51 78 A1 00 02 00 30 00 F9 FF
```

## Key Errors in Our Implementation:

1. ❌ **CMD 0x10**: Should be 0xA2 for quality/bitmap  
2. ❌ **CMD 0xA8**: Doesn't exist in protocol
3. ❌ **CMD 0xA3**: Correct, but used wrong context
4. ❌ **CMD 0x00**: Should be 0xA2 for bitmap rows
5. ❌ **CMD 0xB1**: Should be 0xA1 for paper feed
6. ✅ **CRC8 algorithm**: Correct
7. ❌ **Bit packing**: Changed to LSB-first but should stay MSB-first!
8. ✅ **Packet structure**: Correct

## Notifications Explained

From `ytbBleFastV3Module.java`:
```java
// Flow control ON (stop sending):
"5178ae0101001070ff"  // CMD 0xAE, data 0x01, 0x10, 0x70

// Flow control OFF (resume sending):  
"5178ae0101000000ff"  // CMD 0xAE, data 0x01, 0x00, 0x00
```

The printer uses CMD 0xAE for flow control notifications.
