"""PWA 아이콘 생성 (192x192, 512x512 PNG)"""
import struct, zlib, base64

def make_png(size):
    # 인디고 배경 + 흰색 글자 "성장" 아이콘 (순수 Python PNG 생성)
    w = h = size
    bg = (99, 102, 241)   # indigo-500

    # 단색 PNG 생성
    raw = b''
    for y in range(h):
        raw += b'\x00'  # filter type none
        for x in range(w):
            # 둥근 모서리 마스크
            rx, ry = x - w/2, y - h/2
            r = (w * 0.45)
            if rx*rx + ry*ry > r*r:
                raw += bytes([240, 240, 248])  # 바깥 배경
            else:
                raw += bytes(bg)

    def chunk(name, data):
        c = zlib.crc32(name + data) & 0xffffffff
        return struct.pack('>I', len(data)) + name + data + struct.pack('>I', c)

    sig = b'\x89PNG\r\n\x1a\n'
    ihdr = chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0))
    idat = chunk(b'IDAT', zlib.compress(raw))
    iend = chunk(b'IEND', b'')
    return sig + ihdr + idat + iend

for size, name in [(192, 'icon-192.png'), (512, 'icon-512.png')]:
    with open(name, 'wb') as f:
        f.write(make_png(size))
    print(f"✅ {name} 생성 완료 ({size}x{size})")

print("\n아이콘 생성 완료!")
