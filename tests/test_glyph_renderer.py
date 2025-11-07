"""
Unit tests for glyph_renderer module
"""

import pytest
import numpy as np
import sys
from pathlib import Path
import freetype

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from core.glyph_renderer import GlyphRenderer, GlyphData


class TestGlyphData:
    """Test cases for GlyphData dataclass"""
    
    def test_glyph_data_creation(self):
        """Test creating GlyphData object"""
        bitmap = np.array([[0, 1], [2, 3]], dtype=np.uint8)
        
        glyph = GlyphData(
            char_code=0x41,
            mapped_code=0x41,
            width=2,
            height=2,
            offset_x=1,
            offset_y=10,
            advance_width=8,
            bitmap=bitmap
        )
        
        assert glyph.char_code == 0x41
        assert glyph.mapped_code == 0x41
        assert glyph.width == 2
        assert glyph.height == 2
        assert glyph.advance_width == 8
        assert glyph.bitmap.shape == (2, 2)
        assert "U+0041" in str(glyph)
    
    def test_glyph_data_with_mapping(self):
        """Test GlyphData with character mapping"""
        bitmap = np.zeros((5, 5), dtype=np.uint8)
        
        glyph = GlyphData(
            char_code=0x1F450,
            mapped_code=0xF005,
            width=5,
            height=5,
            offset_x=0,
            offset_y=8,
            advance_width=6,
            bitmap=bitmap
        )
        
        assert glyph.char_code == 0x1F450
        assert glyph.mapped_code == 0xF005


class TestGlyphRenderer:
    """Test cases for GlyphRenderer class"""
    
    def test_renderer_initialization(self):
        """Test GlyphRenderer initialization"""
        renderer = GlyphRenderer()
        assert renderer is not None
        assert len(renderer._faces) == 0
        assert renderer._current_size == 16
        assert renderer._current_bpp == 4
    
    def test_set_size(self):
        """Test setting font size"""
        renderer = GlyphRenderer()
        
        renderer.set_size(24)
        assert renderer._current_size == 24
        
        renderer.set_size(12)
        assert renderer._current_size == 12
    
    def test_set_size_invalid(self):
        """Test setting invalid font size"""
        renderer = GlyphRenderer()
        
        with pytest.raises(ValueError, match="Invalid font size"):
            renderer.set_size(5)  # Too small
        
        with pytest.raises(ValueError, match="Invalid font size"):
            renderer.set_size(300)  # Too large
    
    def test_set_bpp(self):
        """Test setting bits per pixel"""
        renderer = GlyphRenderer()
        
        for bpp in [1, 2, 3, 4]:
            renderer.set_bpp(bpp)
            assert renderer._current_bpp == bpp
    
    def test_set_bpp_invalid(self):
        """Test setting invalid bpp"""
        renderer = GlyphRenderer()
        
        with pytest.raises(ValueError, match="Invalid bpp"):
            renderer.set_bpp(5)
        
        with pytest.raises(ValueError, match="Invalid bpp"):
            renderer.set_bpp(0)
    
    def test_convert_to_1bit(self):
        """Test 1-bit conversion"""
        renderer = GlyphRenderer()
        
        # Test with various inputs
        bitmap = np.array([[0, 64, 127, 128, 192, 255]], dtype=np.uint8)
        result = renderer._convert_to_1bit(bitmap)
        
        # Values < 128 should be 0, >= 128 should be 1
        expected = np.array([[0, 0, 0, 1, 1, 1]], dtype=np.uint8)
        assert np.array_equal(result, expected)
    
    def test_convert_to_2bit(self):
        """Test 2-bit conversion"""
        renderer = GlyphRenderer()
        
        bitmap = np.array([[0, 63, 64, 127, 128, 191, 192, 255]], dtype=np.uint8)
        result = renderer._convert_to_2bit(bitmap)
        
        # 0-63->0, 64-127->1, 128-191->2, 192-255->3
        expected = np.array([[0, 0, 1, 1, 2, 2, 3, 3]], dtype=np.uint8)
        assert np.array_equal(result, expected)
    
    def test_convert_to_3bit(self):
        """Test 3-bit conversion"""
        renderer = GlyphRenderer()
        
        bitmap = np.array([[0, 32, 64, 96, 128, 160, 192, 224, 255]], dtype=np.uint8)
        result = renderer._convert_to_3bit(bitmap)
        
        # Should map to 0-7
        assert result.max() <= 7
        assert result.min() >= 0
    
    def test_convert_to_4bit(self):
        """Test 4-bit conversion"""
        renderer = GlyphRenderer()
        
        bitmap = np.array([[0, 16, 32, 64, 128, 192, 240, 255]], dtype=np.uint8)
        result = renderer._convert_to_4bit(bitmap)
        
        # Should map to 0-15
        assert result.max() <= 15
        assert result.min() >= 0
    
    def test_clear(self):
        """Test clearing font faces"""
        renderer = GlyphRenderer()
        renderer.clear()
        assert len(renderer._faces) == 0


class TestGlyphRendererWithFont:
    """Test cases that require a real font"""
    
    @pytest.fixture
    def system_font_path(self):
        """Find a system font for testing"""
        possible_fonts = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/TTF/DejaVuSans.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "/Library/Fonts/Arial.ttf",
            "/mnt/c/Windows/Fonts/arial.ttf",
        ]
        
        for font_path in possible_fonts:
            if Path(font_path).exists():
                return font_path
        
        return None
    
    @pytest.fixture
    def renderer_with_font(self, system_font_path):
        """Create renderer with loaded font"""
        if system_font_path is None:
            pytest.skip("No suitable system font found")
        
        renderer = GlyphRenderer()
        face = freetype.Face(system_font_path)
        renderer.set_font_face(system_font_path, face)
        renderer.set_size(16)
        renderer.set_bpp(4)
        
        return renderer, system_font_path
    
    def test_render_simple_glyph(self, renderer_with_font):
        """Test rendering a simple glyph"""
        renderer, font_path = renderer_with_font
        
        # Render 'A'
        glyph = renderer.render_glyph(font_path, 0x41)
        
        assert glyph is not None
        assert glyph.char_code == 0x41
        assert glyph.width > 0
        assert glyph.height > 0
        assert glyph.advance_width > 0
        assert glyph.bitmap.shape == (glyph.height, glyph.width)
    
    def test_render_with_different_sizes(self, renderer_with_font):
        """Test rendering with different font sizes"""
        renderer, font_path = renderer_with_font
        
        sizes = [12, 16, 24, 32]
        glyphs = []
        
        for size in sizes:
            renderer.set_size(size)
            glyph = renderer.render_glyph(font_path, 0x41)
            glyphs.append(glyph)
        
        # Glyphs should generally get larger with size
        for i in range(len(glyphs) - 1):
            assert glyphs[i].height <= glyphs[i + 1].height
    
    def test_render_with_different_bpp(self, renderer_with_font):
        """Test rendering with different bit depths"""
        renderer, font_path = renderer_with_font
        
        for bpp in [1, 2, 3, 4]:
            renderer.set_bpp(bpp)
            glyph = renderer.render_glyph(font_path, 0x41)
            
            assert glyph is not None
            
            # Check bitmap value range
            if glyph.bitmap.size > 0:
                max_value = (2 ** bpp) - 1
                assert glyph.bitmap.max() <= max_value
    
    def test_render_space(self, renderer_with_font):
        """Test rendering space character (should have no visible pixels)"""
        renderer, font_path = renderer_with_font
        
        glyph = renderer.render_glyph(font_path, 0x20)  # space
        
        assert glyph is not None
        assert glyph.advance_width > 0
        # Space may have zero or very small dimensions
    
    def test_render_with_mapping(self, renderer_with_font):
        """Test rendering with character code mapping"""
        renderer, font_path = renderer_with_font
        
        glyph = renderer.render_glyph(font_path, 0x41, mapped_code=0xF000)
        
        assert glyph is not None
        assert glyph.char_code == 0x41
        assert glyph.mapped_code == 0xF000
    
    def test_get_kerning(self, renderer_with_font):
        """Test getting kerning information"""
        renderer, font_path = renderer_with_font
        
        # Test common kerning pair 'AV'
        kern = renderer.get_kerning(font_path, 0x41, 0x56)
        
        # Kerning should be a tuple of two integers
        assert isinstance(kern, tuple)
        assert len(kern) == 2
        assert isinstance(kern[0], int)
        assert isinstance(kern[1], int)
    
    def test_measure_text(self, renderer_with_font):
        """Test measuring text dimensions"""
        renderer, font_path = renderer_with_font
        
        text = "Hello"
        width, height = renderer.measure_text(font_path, text)
        
        assert width > 0
        assert height > 0
        
        # Longer text should be wider
        width2, _ = renderer.measure_text(font_path, text * 2)
        assert width2 > width
    
    def test_measure_empty_text(self, renderer_with_font):
        """Test measuring empty text"""
        renderer, font_path = renderer_with_font
        
        width, height = renderer.measure_text(font_path, "")
        assert width == 0
        assert height == 0


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
