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

### Key Differences from Our Original Implementation:
1. ✅ Magic Header: `0x51 0x78` (correct)
2. ✅ **Separator**: `0x00` after CMD (correct)
3. ✅ **Bit Ordering**: LSB-first for bitmap packing (correct - see explanation below)
4. ❌ **Command Codes**: Were using wrong codes (now fixed)

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

**IMPORTANT: This is LSB-first packing!**
- **src[i6]** (first array element / pixel 0) → **bit 0 (LSB)**
- **src[i6+7]** (8th array element / pixel 7) → **bit 7 (MSB)**

**For Flutter/Mobile implementation:**
```dart
// Pack 8 pixels into 1 byte (LSB-first)
int packByte(List<int> pixels, int startIndex) {
  int byte = 0;
  for (int i = 0; i < 8; i++) {
    if (pixels[startIndex + i] > 0) {  // if black pixel
      byte |= (1 << i);  // set bit i (LSB-first)
    }
  }
  return byte;
}
```

In Python we use: `np.packbits(row, bitorder='little')` which does exactly this.

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

## What We Fixed (Reference for Flutter Implementation):

1. ✅ **CMD 0xA2**: For quality AND bitmap rows (was using 0x10, 0x00)
2. ✅ **CMD 0xA1**: For paper feed (was using 0xB1)
3. ✅ **CMD 0xA6**: For print lattice init/finish (was using 0xA8, 0xA3)
4. ✅ **CMD 0xA3**: For get device state (correct usage)
5. ✅ **CRC8 algorithm**: Polynomial 0x07, correct from the start
6. ✅ **Bit packing**: LSB-first (pixel 0 → bit 0)
7. ✅ **Packet structure**: [0x51][0x78][CMD][0x00][LEN_LO][LEN_HI][DATA][CRC8][0xFF]
8. ✅ **Print sequence**: Quality → Lattice Init → Bitmap Rows → Feed → Lattice Finish → Get State

## Notifications Explained

From `ytbBleFastV3Module.java`:
```java
// Flow control ON (stop sending):
"5178ae0101001070ff"  // CMD 0xAE, data 0x01, 0x10, 0x70

// Flow control OFF (resume sending):  
"5178ae0101000000ff"  // CMD 0xAE, data 0x01, 0x00, 0x00
```

The printer uses CMD 0xAE for flow control notifications.

---

## Flutter Implementation Guide

### BLE Service & Characteristics
```dart
final serviceUuid = "0000ae30-0000-1000-8000-00805f9b34fb";
final writeCharUuid = "0000ae01-0000-1000-8000-00805f9b34fb";  // Write without response
final notifyCharUuid = "0000ae02-0000-1000-8000-00805f9b34fb"; // Optional notifications
```

### Print Receipt Workflow
```dart
// 1. Connect to PD01 printer via BLE
// 2. Resize receipt image to 384px width
// 3. Convert to grayscale
// 4. Apply dithering (Floyd-Steinberg recommended)
// 5. Convert to 1-bit bitmap (48 bytes per row)
// 6. Pack bits LSB-first
// 7. Send print sequence:

List<List<int>> buildPrintJob(List<int> imageData, int quality) {
  List<List<int>> packets = [];
  
  // 1. Quality command
  packets.add([0x51, 0x78, 0xA2, 0x00, 0x01, 0x00, 0x30 + quality, crc, 0xFF]);
  
  // 2. Lattice init
  packets.add([0x51, 0x78, 0xA6, 0x00, 0x0B, 0x00, 
               0xAA, 0x55, 0x17, 0x38, 0x44, 0x5F, 0x5F, 0x5F, 0x44, 0x38, 0x2C, crc, 0xFF]);
  
  // 3. Bitmap rows (48 bytes each)
  for (int i = 0; i < imageData.length; i += 48) {
    List<int> row = imageData.sublist(i, i + 48);
    packets.add([0x51, 0x78, 0xA2, 0x00, 0x30, 0x00, ...row, crc, 0xFF]);
  }
  
  // 4. Feed paper
  packets.add([0x51, 0x78, 0xA1, 0x00, 0x02, 0x00, 0x30, 0x00, crc, 0xFF]);
  
  // 5. Lattice finish  
  packets.add([0x51, 0x78, 0xA6, 0x00, 0x0B, 0x00,
               0xAA, 0x55, 0x17, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x17, crc, 0xFF]);
  
  // 6. Get state
  packets.add([0x51, 0x78, 0xA3, 0x00, 0x01, 0x00, 0x00, crc, 0xFF]);
  
  return packets;
}
```

### Flutter Packages Needed
```yaml
dependencies:
  flutter_blue_plus: ^1.14.0  # For BLE communication
  image: ^4.0.0                # For image processing
```

### Key Implementation Notes
1. **Write without response**: Use `writeWithoutResponse` for better performance
2. **MTU**: Negotiate MTU to 248 bytes for faster transmission
3. **Delay**: Add 10ms delay between packets
4. **Image width**: Always resize to exactly 384 pixels
5. **Quality**: 1-5 (1=lightest, 5=darkest), use 2-3 for receipts
