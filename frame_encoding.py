"""Panel-independent encoding. Candidate profiles are not hardware certification."""
from dataclasses import dataclass

@dataclass(frozen=True)
class FrameFormat:
    width: int
    height: int
    planes: tuple[tuple[int, ...], ...]
    bits: int = 2
    msb_first: bool = True
    pad_code: int = 0
    flip_x: bool = False
    flip_y: bool = False

    def encode(self, indices: bytes) -> tuple[bytes, ...]:
        w, h, b = self.width, self.height, self.bits
        if w <= 0 or h <= 0 or b not in (1, 2) or len(indices) != w*h:
            raise ValueError("invalid frame dimensions or length")
        if not self.planes or not self.planes[0]:
            raise ValueError("empty color mapping")
        n = len(self.planes[0])
        if any(len(p) != n or any(not 0 <= c < 2**b for c in p) for p in self.planes):
            raise ValueError("invalid color mapping")
        if not 0 <= self.pad_code < 2**b or max(indices) >= n:
            raise ValueError("invalid padding or pixel index")
        stride = (w*b+7)//8
        slots = 8//b
        pad = sum(self.pad_code << (i*b) for i in range(slots))
        result = []
        for codes in self.planes:
            out = bytearray([pad])*(stride*h)
            for y in range(h):
                sy = h-1-y if self.flip_y else y
                for x in range(w):
                    sx = w-1-x if self.flip_x else x
                    slot = x % slots
                    shift = (slots-1-slot if self.msb_first else slot)*b
                    pos = y*stride+x//slots
                    mask = ((1<<b)-1)<<shift
                    out[pos] = (out[pos] & ~mask) | (codes[indices[sy*w+sx]]<<shift)
            result.append(bytes(out))
        return tuple(result)

def four_color(width, height, codes, **options):
    """Explicit black/white/red/yellow mapping; no guessed hardware defaults."""
    if len(codes) != 4 or set(codes) != {0,1,2,3}:
        raise ValueError("four distinct two-bit codes required")
    return FrameFormat(width, height, (tuple(codes),), bits=2, **options)

def three_color(width, height, *, active_low=True, **options):
    """Logical black and accent planes, indices black/white/accent."""
    a, i = (0,1) if active_low else (1,0)
    return FrameFormat(width, height, ((a,i,i),(i,i,a)), bits=1, **options)

# Candidate dimensions only; wire mappings require panel-specific evidence.
CANDIDATE_SIZES = {
    "JD79665-800x480": (800,480),
    "SSD2677-960x672": (960,672),
    "SSD2677-960x640": (960,640),
    "SSD2677-960x680": (960,680),
}
