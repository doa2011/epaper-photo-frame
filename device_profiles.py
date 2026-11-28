"""Candidate panel registry. No candidate is certified for hardware refresh."""
from dataclasses import dataclass
from frame_encoding import four_color

@dataclass(frozen=True)
class PanelCandidate:
    driver: str
    width: int
    height: int
    reference: str
    verified: bool = False

    @property
    def frame_bytes(self):
        return ((self.width * 2 + 7) // 8) * self.height

    def encoder(self, *, codes, msb_first, flip_x, flip_y, pad_code):
        """Offline encoding only; caller must supply panel-specific parameters."""
        return four_color(self.width, self.height, codes,
                          msb_first=msb_first, flip_x=flip_x,
                          flip_y=flip_y, pad_code=pad_code)

SSD_REFERENCE = "https://files.waveshare.com/wiki/common/SSD2677_1.0.pdf"
PANELS = {
    "gdem0397f81": PanelCandidate("SSD2677", 800, 480, "https://www.good-display.com/product/577.html"),
    "jd79665-800x480": PanelCandidate("JD79665", 800, 480, ""),
    "gdey097f91": PanelCandidate("SSD2677", 960, 672, SSD_REFERENCE),
    "waveshare-10.2-g": PanelCandidate("SSD2677", 960, 640, SSD_REFERENCE),
    "gdey116f51": PanelCandidate("SSD2677", 960, 640, SSD_REFERENCE),
    "gdey116f91": PanelCandidate("SSD2677", 960, 640, SSD_REFERENCE),
    "gdey133f91": PanelCandidate("SSD2677", 960, 680, SSD_REFERENCE),
}
# References are research leads, not proof of the exact panel/controller pairing.
