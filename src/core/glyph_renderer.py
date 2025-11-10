"""
Glyph renderer module for LVFontConv
Renders font glyphs to bitmaps with various bit depths
"""

from dataclasses import dataclass
from typing import Optional, Tuple, Dict
import numpy as np
import freetype

from utils.logger import get_logger

logger = get_logger()


@dataclass
class GlyphData:
    """
    Glyph rendering data
    
    Contains the rendered bitmap and metrics for a single glyph.
    """
    char_code: int
    mapped_code: int
    width: int
    height: int
    offset_x: int
    offset_y: int
    advance_width: int
    bitmap: np.ndarray  # 2D array of pixel values
    
    def __str__(self) -> str:
        return (
            f"GlyphData(U+{self.char_code:04X}->'U+{self.mapped_code:04X}', "
            f"size={self.width}x{self.height}, "
            f"offset=({self.offset_x},{self.offset_y}), "
            f"advance={self.advance_width})"
        )


class GlyphRenderer:
    """
    Glyph renderer using FreeType
    
    Renders font glyphs to bitmaps with support for:
    - Multiple font sizes
    - Different bit depths (1, 2, 3, 4 bits per pixel)
    - Anti-aliasing
    - Hinting options
    """
    
    def __init__(self):
        """Initialize glyph renderer"""
        self._faces: Dict[str, freetype.Face] = {}
        self._current_size: int = 16
        self._current_bpp: int = 4
    
    def set_font_face(self, font_path: str, face: freetype.Face) -> None:
        """
        Set a font face for rendering
        
        Args:
            font_path: Path to font file (used as identifier)
            face: FreeType Face object
        """
        self._faces[font_path] = face
        logger.debug(f"Set font face: {font_path}")
    
    def set_size(self, size: int) -> None:
        """
        Set font size for rendering
        
        Args:
            size: Font size in pixels
        """
        if size < 8 or size > 200:
            raise ValueError(f"Invalid font size: {size}. Must be between 8 and 200.")
        
        self._current_size = size
        
        # Update all loaded faces
        for face in self._faces.values():
            face.set_pixel_sizes(0, size)
        
        logger.debug(f"Set font size to {size}px")
    
    def set_bpp(self, bpp: int) -> None:
        """
        Set bits per pixel for rendering
        
        Args:
            bpp: Bits per pixel (1, 2, 3, or 4)
        """
        if bpp not in [1, 2, 3, 4]:
            raise ValueError(f"Invalid bpp: {bpp}. Must be 1, 2, 3, or 4.")
        
        self._current_bpp = bpp
        logger.debug(f"Set BPP to {bpp}")
    
    def render_glyph(
        self,
        font_path: str,
        char_code: int,
        mapped_code: Optional[int] = None,
        autohint: bool = True
    ) -> Optional[GlyphData]:
        """
        Render a single glyph
        
        Args:
            font_path: Path to font file
            char_code: Source Unicode code point
            mapped_code: Mapped code point (for output), defaults to char_code
            autohint: Enable autohinting
            
        Returns:
            GlyphData object or None if glyph doesn't exist
        """
        if font_path not in self._faces:
            raise ValueError(f"Font face not set: {font_path}")
        
        if mapped_code is None:
            mapped_code = char_code
        
        face = self._faces[font_path]
        
        # Load glyph
        # 使用与原版 lv_font_conv 相同的加载标志:
        # - FT_LOAD_RENDER: 直接渲染为位图
        # - FT_LOAD_TARGET_LIGHT: 轻度 hinting (只影响水平线)
        # - FT_LOAD_FORCE_AUTOHINT: 强制使用自动 hinting
        flags = freetype.FT_LOAD_RENDER | freetype.FT_LOAD_TARGET_LIGHT
        if autohint:
            flags |= freetype.FT_LOAD_FORCE_AUTOHINT
        
        try:
            face.load_char(char_code, flags)
        except Exception as e:
            logger.warning(f"Failed to load glyph U+{char_code:04X}: {e}")
            return None
        
        # Get glyph slot
        glyph = face.glyph
        bitmap = glyph.bitmap
        
        # Extract metrics
        width = bitmap.width
        height = bitmap.rows
        offset_x = glyph.bitmap_left
        offset_y = glyph.bitmap_top
        advance_width = glyph.advance.x >> 6  # Convert from 26.6 fixed point
        
        # Extract bitmap data
        if width > 0 and height > 0:
            # Convert buffer to numpy array
            bitmap_data = np.array(bitmap.buffer, dtype=np.uint8).reshape(height, width)
            
            # Convert to target bit depth
            bitmap_data = self._convert_bit_depth(bitmap_data, self._current_bpp)
        else:
            # Empty glyph (e.g., space)
            bitmap_data = np.zeros((0, 0), dtype=np.uint8)
        
        glyph_data = GlyphData(
            char_code=char_code,
            mapped_code=mapped_code,
            width=width,
            height=height,
            offset_x=offset_x,
            offset_y=offset_y,
            advance_width=advance_width,
            bitmap=bitmap_data
        )
        
        logger.debug(f"Rendered glyph: {glyph_data}")
        return glyph_data
    
    def _convert_bit_depth(self, bitmap: np.ndarray, target_bpp: int) -> np.ndarray:
        """
        Convert bitmap to target bit depth
        
        Args:
            bitmap: Input bitmap (8-bit grayscale, 0-255)
            target_bpp: Target bits per pixel (1, 2, 3, or 4)
            
        Returns:
            Converted bitmap with values in target bit depth range
        """
        if target_bpp == 1:
            # 1-bit: threshold at 50%
            return self._convert_to_1bit(bitmap)
        elif target_bpp == 2:
            # 2-bit: 4 levels (0, 85, 170, 255 -> 0, 1, 2, 3)
            return self._convert_to_2bit(bitmap)
        elif target_bpp == 3:
            # 3-bit: 8 levels (0-255 -> 0-7)
            return self._convert_to_3bit(bitmap)
        elif target_bpp == 4:
            # 4-bit: 16 levels (0-255 -> 0-15)
            return self._convert_to_4bit(bitmap)
        else:
            return bitmap
    
    def _convert_to_1bit(self, bitmap: np.ndarray, threshold: int = 128) -> np.ndarray:
        """
        Convert to 1-bit (binary)
        
        Args:
            bitmap: Input bitmap (8-bit)
            threshold: Threshold value (0-255)
            
        Returns:
            1-bit bitmap (values: 0 or 1)
        """
        return (bitmap >= threshold).astype(np.uint8)
    
    def _convert_to_2bit(self, bitmap: np.ndarray) -> np.ndarray:
        """
        Convert to 2-bit (4 levels)
        
        Args:
            bitmap: Input bitmap (8-bit)
            
        Returns:
            2-bit bitmap (values: 0-3)
        """
        # Map 0-255 to 0-3
        # 0-63 -> 0, 64-127 -> 1, 128-191 -> 2, 192-255 -> 3
        return (bitmap >> 6).astype(np.uint8)
    
    def _convert_to_3bit(self, bitmap: np.ndarray) -> np.ndarray:
        """
        Convert to 3-bit (8 levels)
        
        Args:
            bitmap: Input bitmap (8-bit)
            
        Returns:
            3-bit bitmap (values: 0-7)
        """
        # Map 0-255 to 0-7
        return (bitmap >> 5).astype(np.uint8)
    
    def _convert_to_4bit(self, bitmap: np.ndarray) -> np.ndarray:
        """
        Convert to 4-bit (16 levels)
        
        Args:
            bitmap: Input bitmap (8-bit)
            
        Returns:
            4-bit bitmap (values: 0-15)
        """
        # Map 0-255 to 0-15
        return (bitmap >> 4).astype(np.uint8)
    
    def get_kerning(
        self,
        font_path: str,
        left_char: int,
        right_char: int
    ) -> Tuple[int, int]:
        """
        Get kerning adjustment between two characters
        
        Args:
            font_path: Path to font file
            left_char: Left character code
            right_char: Right character code
            
        Returns:
            Tuple of (x_adjust, y_adjust) in pixels
        """
        if font_path not in self._faces:
            raise ValueError(f"Font face not set: {font_path}")
        
        face = self._faces[font_path]
        
        # Check if font has kerning
        if not face.has_kerning:
            return (0, 0)
        
        try:
            # Get glyph indices
            left_glyph = face.get_char_index(left_char)
            right_glyph = face.get_char_index(right_char)
            
            # Get kerning vector
            kerning = face.get_kerning(left_glyph, right_glyph)
            
            # Convert from 26.6 fixed point to pixels
            x_adjust = kerning.x >> 6
            y_adjust = kerning.y >> 6
            
            return (x_adjust, y_adjust)
        except Exception as e:
            logger.warning(f"Failed to get kerning for U+{left_char:04X} + U+{right_char:04X}: {e}")
            return (0, 0)
    
    def measure_text(
        self,
        font_path: str,
        text: str,
        use_kerning: bool = True
    ) -> Tuple[int, int]:
        """
        Measure text dimensions
        
        Args:
            font_path: Path to font file
            text: Text to measure
            use_kerning: Apply kerning adjustments
            
        Returns:
            Tuple of (width, height) in pixels
        """
        if not text:
            return (0, 0)
        
        total_width = 0
        max_height = 0
        prev_char = None
        
        for char in text:
            char_code = ord(char)
            
            # Apply kerning
            if use_kerning and prev_char is not None:
                kern_x, _ = self.get_kerning(font_path, prev_char, char_code)
                total_width += kern_x
            
            # Render glyph to get metrics
            glyph = self.render_glyph(font_path, char_code)
            if glyph:
                total_width += glyph.advance_width
                max_height = max(max_height, glyph.height)
            
            prev_char = char_code
        
        return (total_width, max_height)
    
    def clear(self) -> None:
        """Clear all loaded font faces"""
        self._faces.clear()
        logger.debug("Cleared all font faces")


if __name__ == "__main__":
    # Test the glyph renderer
    import sys
    from pathlib import Path
    
    if len(sys.argv) > 1:
        font_path = sys.argv[1]
        
        if not Path(font_path).exists():
            print(f"Font file not found: {font_path}")
            sys.exit(1)
        
        # Create renderer
        renderer = GlyphRenderer()
        
        # Load font face
        face = freetype.Face(font_path)
        renderer.set_font_face(font_path, face)
        
        # Set parameters
        renderer.set_size(24)
        renderer.set_bpp(4)
        
        # Test rendering
        test_chars = [0x41, 0x61, 0x30]  # A, a, 0
        
        print("\nGlyph Rendering Test:")
        for char_code in test_chars:
            glyph = renderer.render_glyph(font_path, char_code)
            if glyph:
                print(f"\n{glyph}")
                print(f"  Bitmap shape: {glyph.bitmap.shape}")
                if glyph.bitmap.size > 0:
                    print(f"  Value range: {glyph.bitmap.min()}-{glyph.bitmap.max()}")
        
        # Test kerning
        print("\nKerning Test:")
        pairs = [(0x41, 0x56), (0x54, 0x6F)]  # AV, To
        for left, right in pairs:
            kern = renderer.get_kerning(font_path, left, right)
            print(f"  U+{left:04X} + U+{right:04X}: {kern}")
        
        # Test text measurement
        print("\nText Measurement Test:")
        test_text = "Hello"
        width, height = renderer.measure_text(font_path, test_text)
        print(f"  '{test_text}': {width}x{height} pixels")
    else:
        print("Usage: python glyph_renderer.py <font_file>")
