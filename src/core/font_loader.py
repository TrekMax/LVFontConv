"""
Font loader module for LVFontConv
Loads and parses font files (TTF, OTF, WOFF, WOFF2)
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Set, Optional, Dict, Any
import freetype

from fontTools.ttLib import TTFont
from fontTools.pens.boundsPen import BoundsPen

from utils.logger import get_logger

logger = get_logger()


@dataclass
class FontInfo:
    """
    Font information data class
    
    Contains metadata and metrics extracted from a font file.
    """
    file_path: str
    family_name: str
    style_name: str
    full_name: str
    glyph_count: int
    supported_chars: Set[int]
    ascent: int
    descent: int
    units_per_em: int
    has_kerning: bool = False
    is_fixed_pitch: bool = False
    
    def __str__(self) -> str:
        return (
            f"FontInfo(family='{self.family_name}', "
            f"style='{self.style_name}', "
            f"glyphs={self.glyph_count}, "
            f"chars={len(self.supported_chars)})"
        )


class FontLoader:
    """
    Font file loader and parser
    
    Supports TTF, OTF, WOFF, WOFF2 formats using fontTools and freetype-py.
    """
    
    def __init__(self):
        """Initialize font loader"""
        self._loaded_fonts: Dict[str, TTFont] = {}
        self._freetype_faces: Dict[str, freetype.Face] = {}
    
    def load_font(self, font_path: str) -> FontInfo:
        """
        Load a font file and extract information
        
        Args:
            font_path: Path to font file
            
        Returns:
            FontInfo object with font metadata
            
        Raises:
            FileNotFoundError: If font file doesn't exist
            ValueError: If font file is invalid or unsupported
        """
        path = Path(font_path)
        
        # Check file exists
        if not path.exists():
            raise FileNotFoundError(f"Font file not found: {font_path}")
        
        # Check file extension
        valid_extensions = {'.ttf', '.otf', '.woff', '.woff2'}
        if path.suffix.lower() not in valid_extensions:
            raise ValueError(
                f"Unsupported font format: {path.suffix}. "
                f"Supported formats: {', '.join(valid_extensions)}"
            )
        
        logger.info(f"Loading font: {font_path}")
        
        try:
            # Load with fontTools
            font = TTFont(font_path)
            self._loaded_fonts[font_path] = font
            
            # Load with freetype
            face = freetype.Face(font_path)
            self._freetype_faces[font_path] = face
            
            # Extract font information
            info = self._extract_font_info(font_path, font, face)
            
            logger.info(f"Successfully loaded font: {info}")
            return info
            
        except Exception as e:
            logger.error(f"Failed to load font {font_path}: {e}")
            raise ValueError(f"Failed to load font: {e}")
    
    def _extract_font_info(self, font_path: str, font: TTFont, face: freetype.Face) -> FontInfo:
        """
        Extract font information from loaded font
        
        Args:
            font_path: Path to font file
            font: Loaded TTFont object
            face: Loaded FreeType face
            
        Returns:
            FontInfo object
        """
        # Get name table
        name_table = font['name']
        
        # Extract names (prefer Unicode names)
        family_name = self._get_name(name_table, 1) or face.family_name.decode('utf-8')
        style_name = self._get_name(name_table, 2) or face.style_name.decode('utf-8')
        full_name = self._get_name(name_table, 4) or f"{family_name} {style_name}"
        
        # Get head table for metrics
        head = font['head']
        units_per_em = head.unitsPerEm
        
        # Get hhea table for ascent/descent
        hhea = font['hhea']
        ascent = hhea.ascent
        descent = hhea.descent
        
        # Get glyph count
        glyph_count = font['maxp'].numGlyphs
        
        # Get supported characters
        supported_chars = self._get_supported_chars(font)
        
        # Check for kerning
        has_kerning = 'kern' in font or 'GPOS' in font
        
        # Check if fixed pitch
        post = font.get('post')
        is_fixed_pitch = post.isFixedPitch if post else False
        
        return FontInfo(
            file_path=font_path,
            family_name=family_name,
            style_name=style_name,
            full_name=full_name,
            glyph_count=glyph_count,
            supported_chars=supported_chars,
            ascent=ascent,
            descent=descent,
            units_per_em=units_per_em,
            has_kerning=has_kerning,
            is_fixed_pitch=is_fixed_pitch
        )
    
    def _get_name(self, name_table, name_id: int) -> Optional[str]:
        """
        Get name from name table
        
        Args:
            name_table: Font name table
            name_id: Name ID (1=family, 2=style, 4=full name, etc.)
            
        Returns:
            Name string or None if not found
        """
        try:
            # Try to get Unicode name first (platform 3, encoding 1)
            name_record = name_table.getName(name_id, 3, 1)
            if name_record:
                return name_record.toUnicode()
            
            # Fallback to first available name
            for record in name_table.names:
                if record.nameID == name_id:
                    return record.toUnicode()
        except Exception as e:
            logger.warning(f"Failed to get name {name_id}: {e}")
        
        return None
    
    def _get_supported_chars(self, font: TTFont) -> Set[int]:
        """
        Get set of supported Unicode characters
        
        Args:
            font: Loaded TTFont object
            
        Returns:
            Set of Unicode code points
        """
        supported = set()
        
        # Get cmap table
        if 'cmap' not in font:
            logger.warning("Font has no cmap table")
            return supported
        
        cmap = font['cmap']
        
        # Try to find best Unicode cmap
        # Prefer format 12 (full Unicode), then format 4 (BMP only)
        unicode_cmap = None
        
        for table in cmap.tables:
            # Format 12: Unicode full repertoire
            if table.format == 12 and table.platformID == 3:
                unicode_cmap = table
                break
            # Format 4: Unicode BMP
            elif table.format == 4 and table.platformID == 3:
                if unicode_cmap is None or unicode_cmap.format != 12:
                    unicode_cmap = table
        
        if unicode_cmap:
            supported = set(unicode_cmap.cmap.keys())
            logger.debug(f"Found {len(supported)} supported characters")
        else:
            logger.warning("No suitable Unicode cmap table found")
        
        return supported
    
    def char_exists(self, font_path: str, char_code: int) -> bool:
        """
        Check if a character exists in the font
        
        Args:
            font_path: Path to font file
            char_code: Unicode code point
            
        Returns:
            True if character exists, False otherwise
        """
        if font_path not in self._freetype_faces:
            raise ValueError(f"Font not loaded: {font_path}")
        
        face = self._freetype_faces[font_path]
        
        try:
            glyph_index = face.get_char_index(char_code)
            return glyph_index != 0
        except Exception as e:
            logger.warning(f"Error checking char 0x{char_code:X}: {e}")
            return False
    
    def get_font(self, font_path: str) -> Optional[TTFont]:
        """
        Get loaded TTFont object
        
        Args:
            font_path: Path to font file
            
        Returns:
            TTFont object or None if not loaded
        """
        return self._loaded_fonts.get(font_path)
    
    def get_freetype_face(self, font_path: str) -> Optional[freetype.Face]:
        """
        Get loaded FreeType face
        
        Args:
            font_path: Path to font file
            
        Returns:
            FreeType Face object or None if not loaded
        """
        return self._freetype_faces.get(font_path)
    
    def unload_font(self, font_path: str) -> None:
        """
        Unload a font from memory
        
        Args:
            font_path: Path to font file
        """
        if font_path in self._loaded_fonts:
            self._loaded_fonts[font_path].close()
            del self._loaded_fonts[font_path]
        
        if font_path in self._freetype_faces:
            del self._freetype_faces[font_path]
        
        logger.info(f"Unloaded font: {font_path}")
    
    def unload_all(self) -> None:
        """Unload all fonts from memory"""
        for font_path in list(self._loaded_fonts.keys()):
            self.unload_font(font_path)
        
        logger.info("Unloaded all fonts")
    
    def __del__(self):
        """Cleanup when object is destroyed"""
        self.unload_all()


if __name__ == "__main__":
    # Test the font loader
    import sys
    
    if len(sys.argv) > 1:
        font_path = sys.argv[1]
        
        loader = FontLoader()
        try:
            info = loader.load_font(font_path)
            print(f"\nFont Information:")
            print(f"  Family: {info.family_name}")
            print(f"  Style: {info.style_name}")
            print(f"  Full Name: {info.full_name}")
            print(f"  Glyphs: {info.glyph_count}")
            print(f"  Supported Characters: {len(info.supported_chars)}")
            print(f"  Units per EM: {info.units_per_em}")
            print(f"  Ascent: {info.ascent}")
            print(f"  Descent: {info.descent}")
            print(f"  Has Kerning: {info.has_kerning}")
            print(f"  Fixed Pitch: {info.is_fixed_pitch}")
            
            # Test some common characters
            test_chars = [0x41, 0x61, 0x30, 0x20]  # A, a, 0, space
            print(f"\nCharacter existence test:")
            for char in test_chars:
                exists = loader.char_exists(font_path, char)
                print(f"  U+{char:04X} ({chr(char)}): {exists}")
        except Exception as e:
            print(f"Error: {e}")
    else:
        print("Usage: python font_loader.py <font_file>")
