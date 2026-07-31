import struct
import sys
import time

def convert_f16_to_f32(h):
    s = (h >> 15) & 1
    e = (h >> 10) & 0x1f
    m = h & 0x3ff
    if e == 0:
        if m == 0:
            return -0.0 if s else 0.0
        while not (m & 0x400):
            m <<= 1
            e -= 1
        e += 1
        m &= ~0x400
    elif e == 31:
        if m == 0:
            return float('-inf') if s else float('inf')
        return float('nan')
    e = e - 15 + 127
    m <<= 13
    bits = (s << 31) | (e << 23) | m
    return struct.unpack('f', struct.pack('I', bits))[0]

def main():
    input_path = '/Users/mac/ai-body-scan-saas/public/models/anny/anny_phenotype.bin'
    output_path = '/Users/mac/ai-body-scan-saas/public/models/anny/anny_phenotype_f32.bin'

    t0 = time.time()
    with open(input_path, 'rb') as f:
        buf = f.read()
    
    p = 0
    header = struct.unpack_from('<6I', buf, p)
    version, V, C, M, F, pad = header
    p += 24
    
    print(f"Header: V={V} C={C} M={M} F={F}")
    
    template = buf[p:p + V * 3 * 4]
    p += V * 3 * 4
    
    faces = buf[p:p + F * 3 * 4]
    p += F * 3 * 4
    
    mask = buf[p:p + C * M * 4]
    p += C * M * 4
    
    t1 = time.time()
    print(f"Header parse: {t1 - t0:.2f}s")
    
    bs16_count = C * V * 3
    bs16 = struct.unpack_from(f'<{bs16_count}H', buf, p)
    p += bs16_count * 2
    
    t2 = time.time()
    print(f"Read {bs16_count} float16 values in {t2 - t1:.2f}s")
    
    bs32 = struct.pack(f'<{bs16_count}f', *[convert_f16_to_f32(h) for h in bs16])
    
    t3 = time.time()
    print(f"Converted to float32 in {t3 - t2:.2f}s")
    
    with open(output_path, 'wb') as f:
        f.write(struct.pack('<6I', 7, V, C, M, F, pad))  # version=7 signals f32 blendshapes
        f.write(template)
        f.write(faces)
        f.write(mask)
        f.write(bs32)
    
    t4 = time.time()
    import os
    size = os.path.getsize(output_path)
    print(f"Written {output_path}: {size} bytes ({size/1024/1024:.1f}MB)")
    print(f"Total time: {t4 - t0:.2f}s")

if __name__ == '__main__':
    main()
