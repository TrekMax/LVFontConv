"""
Unit tests for font_loader module
"""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from core.font_loader import FontLoader, FontInfo


class TestFontLoader:
    """Test cases for FontLoader class"""
    
    def test_font_loader_initialization(self):
        """Test FontLoader can be initialized"""
        loader = FontLoader()
        assert loader is not None
        assert len(loader._loaded_fonts) == 0
        assert len(loader._freetype_faces) == 0
    
    def test_load_nonexistent_font(self):
        """Test loading a non-existent font raises error"""
        loader = FontLoader()
        
        with pytest.raises(FileNotFoundError):
            loader.load_font("/nonexistent/path/font.ttf")
    
    def test_load_invalid_extension(self):
        """Test loading file with invalid extension raises error"""
        loader = FontLoader()
        
        # Create a temporary file with wrong extension
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            temp_path = f.name
        
        try:
            with pytest.raises(ValueError, match="Unsupported font format"):
                loader.load_font(temp_path)
        finally:
            Path(temp_path).unlink()
    
    def test_font_info_dataclass(self):
        """Test FontInfo dataclass"""
        info = FontInfo(
            file_path="/path/to/font.ttf",
            family_name="Test Family",
            style_name="Regular",
            full_name="Test Family Regular",
            glyph_count=100,
            supported_chars={0x41, 0x42, 0x43},
            ascent=800,
            descent=-200,
            units_per_em=1000,
            has_kerning=True,
            is_fixed_pitch=False
        )
        
        assert info.family_name == "Test Family"
        assert info.style_name == "Regular"
        assert len(info.supported_chars) == 3
        assert info.has_kerning is True
        assert "Test Family" in str(info)
    
    def test_unload_all(self):
        """Test unload_all method"""
        loader = FontLoader()
        loader.unload_all()
        assert len(loader._loaded_fonts) == 0
        assert len(loader._freetype_faces) == 0


class TestFontLoaderWithSystemFont:
    """
    Test cases that require a system font
    These tests will be skipped if no suitable font is found
    """
    
    @pytest.fixture
    def system_font_path(self):
        """Find a system font for testing"""
        # Common system font locations
        possible_fonts = [
            # Linux
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/TTF/DejaVuSans.ttf",
            # macOS
            "/System/Library/Fonts/Helvetica.ttc",
            "/Library/Fonts/Arial.ttf",
            # Windows (if running in WSL)
            "/mnt/c/Windows/Fonts/arial.ttf",
        ]
        
        for font_path in possible_fonts:
            if Path(font_path).exists():
                return font_path
        
        return None
    
    def test_load_real_font(self, system_font_path):
        """Test loading a real font file"""
        if system_font_path is None:
            pytest.skip("No suitable system font found")
        
        loader = FontLoader()
        info = loader.load_font(system_font_path)
        
        assert info is not None
        assert info.family_name
        assert info.style_name
        assert info.glyph_count > 0
        assert len(info.supported_chars) > 0
        assert info.units_per_em > 0
        assert info.ascent > 0
        assert info.descent < 0
    
    def test_char_exists(self, system_font_path):
        """Test checking if characters exist in font"""
        if system_font_path is None:
            pytest.skip("No suitable system font found")
        
        loader = FontLoader()
        loader.load_font(system_font_path)
        
        # Test common ASCII characters (should exist in most fonts)
        assert loader.char_exists(system_font_path, 0x41)  # 'A'
        assert loader.char_exists(system_font_path, 0x61)  # 'a'
        assert loader.char_exists(system_font_path, 0x30)  # '0'
        assert loader.char_exists(system_font_path, 0x20)  # space
        
        # Test rare character (might not exist)
        # This test is informational only
        exists = loader.char_exists(system_font_path, 0x1F600)  # emoji
        print(f"Font has emoji U+1F600: {exists}")
    
    def test_get_font(self, system_font_path):
        """Test getting loaded font object"""
        if system_font_path is None:
            pytest.skip("No suitable system font found")
        
        loader = FontLoader()
        loader.load_font(system_font_path)
        
        font = loader.get_font(system_font_path)
        assert font is not None
        
        freetype_face = loader.get_freetype_face(system_font_path)
        assert freetype_face is not None
    
    def test_unload_font(self, system_font_path):
        """Test unloading a specific font"""
        if system_font_path is None:
            pytest.skip("No suitable system font found")
        
        loader = FontLoader()
        loader.load_font(system_font_path)
        
        assert system_font_path in loader._loaded_fonts
        assert system_font_path in loader._freetype_faces
        
        loader.unload_font(system_font_path)
        
        assert system_font_path not in loader._loaded_fonts
        assert system_font_path not in loader._freetype_faces
    
    def test_multiple_fonts(self, system_font_path):
        """Test loading multiple fonts"""
        if system_font_path is None:
            pytest.skip("No suitable system font found")
        
        loader = FontLoader()
        
        # Load the same font (simulating multiple fonts)
        info1 = loader.load_font(system_font_path)
        assert info1 is not None
        
        # The second load should work (replace existing)
        info2 = loader.load_font(system_font_path)
        assert info2 is not None
        
        assert info1.family_name == info2.family_name


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
