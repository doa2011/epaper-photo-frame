"""Local image conversion; wire encoding is explicitly configurable."""
import argparse
from pathlib import Path
from PIL import Image, ImageOps

PALETTES = {"bw": [(0,0,0),(255,255,255)], "bwr": [(0,0,0),(255,255,255),(220,0,0)], "bwy": [(0,0,0),(255,255,255),(255,220,0)], "bwry": [(0,0,0),(255,255,255),(220,0,0),(255,220,0)]}
KERNELS = {"floyd": (16, [(1,0,7),(-1,1,3),(0,1,5),(1,1,1)]), "atkinson": (8, [(1,0,1),(2,0,1),(-1,1,1),(0,1,1),(1,1,1),(0,2,1)])}
BAYER = ((0,8,2,10),(12,4,14,6),(3,11,1,9),(15,7,13,5))

def convert(image, size, palette="bwr", method="floyd"):
    if min(size) <= 0 or method not in ("none","bayer",*KERNELS):
        raise ValueError("invalid size or method")
    colors = PALETTES[palette]
    im = ImageOps.fit(ImageOps.exif_transpose(image).convert("RGB"), size, Image.Resampling.LANCZOS)
    w,h = size
    pixels = [list(map(float,p)) for p in im.getdata()]
    indices = bytearray(w*h)
    for y in range(h):
        for x in range(w):
            i = y*w+x
            p = [max(0,min(255,v)) for v in pixels[i]]
            if method == "bayer":
                delta = (BAYER[y%4][x%4]-7.5)*8
                p = [max(0,min(255,v+delta)) for v in p]
            k = min(range(len(colors)), key=lambda j: sum((a-b)**2 for a,b in zip(p,colors[j])))
            indices[i] = k
            if method in KERNELS:
                divisor, kernel = KERNELS[method]
                err = [a-b for a,b in zip(p,colors[k])]
                for dx,dy,weight in kernel:
                    if 0 <= x+dx < w and y+dy < h:
                        q = pixels[(y+dy)*w+x+dx]
                        for c in range(3):
                            q[c] += err[c]*weight/divisor
    preview = Image.new("RGB",size)
    preview.putdata([colors[k] for k in indices])
    return preview, bytes(indices)

def pack(indices, size, codes, bits):
    """MSB first, row padded with zero bits. Codes must be panel-specific."""
    w,h = size
    if bits not in (1,2) or min(size)<=0 or len(indices)!=w*h or any(c<0 or c>=2**bits for c in codes):
        raise ValueError("invalid packing parameters")
    stride = (w*bits+7)//8
    out = bytearray(stride*h)
    for y in range(h):
        for x in range(w):
            bit = x*bits
            out[y*stride+bit//8] |= codes[indices[y*w+x]] << (8-bits-bit%8)
    return bytes(out)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("source")
    p.add_argument("output")
    p.add_argument("--width",type=int,default=800)
    p.add_argument("--height",type=int,default=480)
    p.add_argument("--palette",choices=PALETTES,default="bwr")
    p.add_argument("--method",choices=["none","bayer",*KERNELS],default="floyd")
    a = p.parse_args()
    with Image.open(a.source) as im:
        preview, indices = convert(im,(a.width,a.height),a.palette,a.method)
    preview.save(a.output+".png")
    Path(a.output+".indices").write_bytes(indices)

if __name__ == "__main__":
    main()
