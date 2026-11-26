import unittest

from frame_encoding import FrameFormat, four_color, three_color, CANDIDATE_SIZES


class FrameEncodingTests(unittest.TestCase):
    def test_four_color_mapping(self):
        self.assertEqual(four_color(4, 1, (3, 0, 2, 1)).encode(bytes(range(4))), (b'\xc9',))

    def test_lsb_order(self):
        self.assertEqual(four_color(4, 1, (0, 1, 2, 3), msb_first=False).encode(bytes(range(4))), (b'\xe4',))

    def test_row_padding(self):
        f = four_color(3, 2, (0, 1, 2, 3), pad_code=3)
        self.assertEqual(f.encode(bytes([0, 1, 2, 2, 1, 0])), (b'\x1b\x93',))

    def test_flips(self):
        data = bytes([0, 1, 2, 3])
        for x, y, expected in [(True, False, b'\x40\xe0'), (False, True, b'\xb0\x10'), (True, True, b'\xe0\x40')]:
            with self.subTest(x=x, y=y):
                self.assertEqual(four_color(2, 2, (0, 1, 2, 3), flip_x=x, flip_y=y).encode(data), (expected,))

    def test_three_color_polarity(self):
        data = bytes([0, 1, 2])
        self.assertEqual(three_color(3, 1, pad_code=1).encode(data), (b'\x7f', b'\xdf'))
        self.assertEqual(three_color(3, 1, active_low=False).encode(data), (b'\x80', b'\x20'))

    def test_invalid_inputs(self):
        for f, data in [(FrameFormat(0, 1, ((0,),)), b''), (FrameFormat(1, 1, ()), b'\0'), (FrameFormat(1, 1, ((4,),)), b'\0'), (four_color(1, 1, (0, 1, 2, 3)), b'\x04'), (four_color(1, 1, (0, 1, 2, 3)), b''), (four_color(1, 1, (0, 1, 2, 3), pad_code=4), b'\0')]:
            with self.subTest(format=f, data=data):
                with self.assertRaises(ValueError):
                    f.encode(data)
        with self.assertRaises(ValueError):
            four_color(1, 1, (0, 0, 2, 3))

    def test_candidate_full_frames(self):
        for name, (w, h) in CANDIDATE_SIZES.items():
            with self.subTest(panel=name):
                data = bytes([2]) * (w*h)
                (frame,) = four_color(w, h, (0, 1, 2, 3)).encode(data)
                self.assertEqual(len(frame), w*h//4)
                self.assertEqual(frame, b'\xaa' * (w*h//4))
                black, accent = three_color(w, h).encode(data)
                self.assertEqual(black, b'\xff' * (w*h//8))
                self.assertEqual(accent, b'\x00' * (w*h//8))


if __name__ == '__main__':
    unittest.main()
