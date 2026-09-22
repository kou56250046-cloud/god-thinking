"""アイコンを生成する。依存ゼロ。

    python scripts/make_icons.py

図案はこの工房そのもの。**一部が埋まり、大半が空いたマトリクス。**
64 マス中 25 マスという実際の比率に近づけて、4×4 のうち 6 マスを埋める。

PNG は zlib と struct で直接書く。外部ライブラリを入れない、という
プロジェクトの制約を画像生成でも守るため（Pillow を使わない）。
"""

import io
import os
import struct
import zlib
from binascii import crc32

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "icons")

# assets/css/tokens.css のダークモードの値から採る
BG      = (0x17, 0x18, 0x1a, 255)   # 地
EMPTY   = (0x30, 0x33, 0x38, 255)   # 該当なしのマス
FILLED  = (0x9d, 0xb8, 0xe0, 255)   # 記事のあるマス
ACCENT  = (0xd9, 0xb6, 0x78, 255)   # 比喩のマス（金）

# 4×4。■ が記事あり、★ が比喩、· が空。
PATTERN = [
    "·■··",
    "■··■",
    "··★·",
    "·■··",
]


def png_bytes(size, buf):
    """RGBA のバイト列を PNG にする。"""
    raw = bytearray()
    stride = size * 4
    for y in range(size):
        raw.append(0)                      # フィルタ種別 0（なし）
        raw += buf[y * stride:(y + 1) * stride]

    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", crc32(tag + data) & 0xFFFFFFFF))

    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + chunk(b"IEND", b""))


def fill_rect(buf, size, x0, y0, x1, y1, color):
    """矩形を塗る。行ごとのスライス代入なので画素ループより速い。"""
    x0 = max(0, int(round(x0))); x1 = min(size, int(round(x1)))
    y0 = max(0, int(round(y0))); y1 = min(size, int(round(y1)))
    if x1 <= x0 or y1 <= y0:
        return
    row = bytes(color) * (x1 - x0)
    for y in range(y0, y1):
        off = (y * size + x0) * 4
        buf[off:off + len(row)] = row


def round_corners(buf, size, radius):
    """角を丸める。角の内側だけ 4×4 で細分して被覆率をアルファにする。"""
    r = int(round(radius))
    if r <= 0:
        return
    for cx, cy, sx, sy in ((r, r, -1, -1), (size - r, r, 1, -1),
                           (r, size - r, -1, 1), (size - r, size - r, 1, 1)):
        for y in range(r):
            py = cy + sy * y if sy > 0 else cy - r + y
            for x in range(r):
                px = cx + sx * x if sx > 0 else cx - r + x
                covered = 0
                for sub_y in range(4):
                    for sub_x in range(4):
                        dx = (px + (sub_x + 0.5) / 4) - cx
                        dy = (py + (sub_y + 0.5) / 4) - cy
                        if dx * dx + dy * dy <= r * r:
                            covered += 1
                if covered < 16:
                    off = (py * size + px) * 4 + 3
                    buf[off] = int(buf[off] * covered / 16)


def draw(size, radius_frac, content_frac):
    """1 枚描く。radius_frac=0 なら角を丸めない（maskable / apple 用）。"""
    buf = bytearray(size * size * 4)
    fill_rect(buf, size, 0, 0, size, size, BG)
    if radius_frac > 0:
        round_corners(buf, size, size * radius_frac)

    # 4×4 のマス。隙間はマスの 1/5
    content = size * content_frac
    cell = content / (4 + 3 / 5.0)
    gap = cell / 5.0
    origin = (size - content) / 2.0

    for row, line in enumerate(PATTERN):
        for col, ch in enumerate(line):
            color = FILLED if ch == "■" else ACCENT if ch == "★" else EMPTY
            x = origin + col * (cell + gap)
            y = origin + row * (cell + gap)
            fill_rect(buf, size, x, y, x + cell, y + cell, color)
    return buf


# 出力: (ファイル名, 辺, 角丸の割合, 中身の割合)
# maskable は OS が円で切り抜くので、中身を安全域に収める。
# apple は透過を扱えないので角を丸めず、iOS 側の丸めに任せる。
TARGETS = [
    ("icon-192.png",             192, 0.22, 0.58),
    ("icon-512.png",             512, 0.22, 0.58),
    ("icon-maskable-512.png",    512, 0.00, 0.55),
    ("apple-touch-icon-180.png", 180, 0.00, 0.62),
    ("favicon-32.png",            32, 0.18, 0.74),
]


def main():
    if not os.path.isdir(OUT):
        os.makedirs(OUT)
    for name, size, radius, content in TARGETS:
        data = png_bytes(size, draw(size, radius, content))
        with io.open(os.path.join(OUT, name), "wb") as fh:
            fh.write(data)
        print("  %-28s %4dpx  %6d bytes" % (name, size, len(data)))
    print("アイコン %d 枚を assets/icons/ に生成した（依存ゼロ）" % len(TARGETS))


if __name__ == "__main__":
    main()
