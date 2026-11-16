import tempfile
import unittest
from pathlib import Path

from video_converter import codec_arguments, unique_output_path


class ConversionHelpersTests(unittest.TestCase):
    def test_webm_uses_webm_codecs(self):
        args = codec_arguments("WEBM", "Balanced")
        self.assertIn("libvpx-vp9", args)
        self.assertIn("libopus", args)

    def test_mp4_uses_broadly_playable_codecs(self):
        args = codec_arguments("MP4", "High")
        self.assertIn("mpeg4", args)
        self.assertIn("aac", args)

    def test_unique_outputs_do_not_overwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            source = folder / "clip.webm"
            source.touch()
            first = unique_output_path(folder, source, "MP4")
            self.assertEqual(first.name, "clip_converted.mp4")
            first.touch()
            self.assertEqual(unique_output_path(folder, source, "MP4").name, "clip_converted_2.mp4")


if __name__ == "__main__":
    unittest.main()
