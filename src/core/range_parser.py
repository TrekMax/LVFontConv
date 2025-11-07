"""
Unicode range parser for LVFontConv
Parses various Unicode range formats for character selection
"""

import re
from typing import List, Tuple, Set

from utils.logger import get_logger

logger = get_logger()


class RangeParser:
    """
    Parser for Unicode character ranges
    
    Supports multiple input formats:
    - Single character: 0x1F450 or 128080
    - Range: 0x20-0x7F
    - Mapped character: 0x1F450=>0xF005
    - Mapped range: 0x1F450-0x1F470=>0xF005
    - Symbol list: ABC123
    - Mixed: 0x20-0x7F,0x1F450
    """
    
    @staticmethod
    def parse_unicode_point(s: str) -> int:
        """
        Parse a single Unicode code point
        
        Args:
            s: String representation (hex or decimal)
            
        Returns:
            Unicode code point as integer
            
        Raises:
            ValueError: If string is not a valid Unicode point
        """
        s = s.strip()
        
        # Try hex format (0x...)
        hex_match = re.match(r'^0x([0-9a-fA-F]+)$', s)
        if hex_match:
            value = int(hex_match.group(1), 16)
        else:
            # Try decimal format
            try:
                value = int(s, 10)
            except ValueError:
                raise ValueError(f"'{s}' is not a valid number")
        
        # Check Unicode range
        if value < 0 or value > 0x10FFFF:
            raise ValueError(f"'{s}' (0x{value:X}) is out of Unicode range (0x0-0x10FFFF)")
        
        return value
    
    @staticmethod
    def parse_range(range_str: str) -> List[Tuple[int, int, int]]:
        """
        Parse a Unicode range string
        
        Args:
            range_str: Range string (e.g., "0x20-0x7F", "0x1F450=>0xF005")
            
        Returns:
            List of tuples (start, end, mapped_start)
            - start: Start code point
            - end: End code point (inclusive)
            - mapped_start: Mapped start code point (for remapping)
            
        Examples:
            "0x20" -> [(0x20, 0x20, 0x20)]
            "0x20-0x7F" -> [(0x20, 0x7F, 0x20)]
            "0x1F450=>0xF005" -> [(0x1F450, 0x1F450, 0xF005)]
            "0x20-0x7F=>0x100" -> [(0x20, 0x7F, 0x100)]
            "0x20-0x7F,0x1F450" -> [(0x20, 0x7F, 0x20), (0x1F450, 0x1F450, 0x1F450)]
        """
        result = []
        
        # Split by comma for multiple ranges
        parts = [p.strip() for p in range_str.split(',')]
        
        for part in parts:
            if not part:
                continue
            
            # Match pattern: start[-end][=>mapped_start]
            match = re.match(
                r'^([^-=>]+)(?:-([^=>]+))?(?:=>(.+))?$',
                part
            )
            
            if not match:
                raise ValueError(f"Invalid range format: '{part}'")
            
            start_str, end_str, mapped_str = match.groups()
            
            # Parse start
            start = RangeParser.parse_unicode_point(start_str)
            
            # Parse end (default to start if not specified)
            end = RangeParser.parse_unicode_point(end_str) if end_str else start
            
            # Parse mapped start (default to start if not specified)
            mapped_start = RangeParser.parse_unicode_point(mapped_str) if mapped_str else start
            
            # Validate range
            if start > end:
                raise ValueError(f"Invalid range: start (0x{start:X}) > end (0x{end:X})")
            
            result.append((start, end, mapped_start))
        
        logger.debug(f"Parsed range '{range_str}' -> {result}")
        return result
    
    @staticmethod
    def parse_symbols(symbols: str) -> List[Tuple[int, int, int]]:
        """
        Parse a symbol string into character ranges
        
        Args:
            symbols: String of symbols (e.g., "ABC123")
            
        Returns:
            List of tuples (char_code, char_code, char_code) for each character
            
        Example:
            "ABC" -> [(65, 65, 65), (66, 66, 66), (67, 67, 67)]
        """
        result = []
        
        for char in symbols:
            code = ord(char)
            result.append((code, code, code))
        
        logger.debug(f"Parsed symbols '{symbols}' -> {len(result)} characters")
        return result
    
    @staticmethod
    def expand_ranges(ranges: List[Tuple[int, int, int]]) -> List[Tuple[int, int]]:
        """
        Expand ranges to individual (source, mapped) pairs
        
        Args:
            ranges: List of (start, end, mapped_start) tuples
            
        Returns:
            List of (source_code, mapped_code) tuples
            
        Example:
            [(0x20, 0x22, 0x100)] -> [(0x20, 0x100), (0x21, 0x101), (0x22, 0x102)]
        """
        result = []
        
        for start, end, mapped_start in ranges:
            offset = 0
            for code in range(start, end + 1):
                result.append((code, mapped_start + offset))
                offset += 1
        
        return result
    
    @staticmethod
    def get_character_set(ranges: List[Tuple[int, int, int]]) -> Set[int]:
        """
        Get set of all source character codes in the ranges
        
        Args:
            ranges: List of (start, end, mapped_start) tuples
            
        Returns:
            Set of character codes
        """
        char_set = set()
        
        for start, end, _ in ranges:
            char_set.update(range(start, end + 1))
        
        return char_set
    
    @staticmethod
    def validate_ranges(ranges: List[Tuple[int, int, int]]) -> List[str]:
        """
        Validate ranges for potential issues
        
        Args:
            ranges: List of (start, end, mapped_start) tuples
            
        Returns:
            List of warning messages (empty if no issues)
        """
        warnings = []
        
        # Check for overlapping source ranges
        all_chars = []
        for start, end, _ in ranges:
            all_chars.extend(range(start, end + 1))
        
        if len(all_chars) != len(set(all_chars)):
            warnings.append("Warning: Overlapping source character ranges detected")
        
        # Check for very large ranges
        total_chars = len(set(all_chars))
        if total_chars > 10000:
            warnings.append(f"Warning: Large character set ({total_chars} characters)")
        
        return warnings


# Preset ranges
PRESET_RANGES = {
    'ASCII': '0x20-0x7F',
    'ASCII_PRINTABLE': '0x21-0x7E',
    'DIGITS': '0x30-0x39',
    'UPPERCASE': '0x41-0x5A',
    'LOWERCASE': '0x61-0x7A',
    'NUMBERS_PUNCTUATION': '0123456789.,+-*/=()[]{}',
    'LATIN_EXTENDED_A': '0x100-0x17F',
    'LATIN_EXTENDED_B': '0x180-0x24F',
    'CYRILLIC': '0x400-0x4FF',
    'GREEK': '0x370-0x3FF',
    # Chinese common characters (simplified)
    'CJK_UNIFIED_COMMON': '0x4E00-0x9FFF',
}


def get_preset_ranges() -> dict:
    """Get dictionary of preset ranges"""
    return PRESET_RANGES.copy()


def get_preset_range(name: str) -> str:
    """Get a preset range by name"""
    return PRESET_RANGES.get(name, '')


if __name__ == "__main__":
    # Test the range parser
    parser = RangeParser()
    
    # Test single character
    print("\nTest single character:")
    ranges = parser.parse_range("0x41")
    print(f"0x41 -> {ranges}")
    print(f"Expanded: {parser.expand_ranges(ranges)}")
    
    # Test range
    print("\nTest range:")
    ranges = parser.parse_range("0x41-0x43")
    print(f"0x41-0x43 -> {ranges}")
    print(f"Expanded: {parser.expand_ranges(ranges)}")
    
    # Test mapped character
    print("\nTest mapped character:")
    ranges = parser.parse_range("0x1F450=>0xF005")
    print(f"0x1F450=>0xF005 -> {ranges}")
    print(f"Expanded: {parser.expand_ranges(ranges)}")
    
    # Test mapped range
    print("\nTest mapped range:")
    ranges = parser.parse_range("0x41-0x43=>0x100")
    print(f"0x41-0x43=>0x100 -> {ranges}")
    print(f"Expanded: {parser.expand_ranges(ranges)}")
    
    # Test multiple ranges
    print("\nTest multiple ranges:")
    ranges = parser.parse_range("0x20-0x7F,0x1F450")
    print(f"0x20-0x7F,0x1F450 -> {ranges}")
    print(f"Total characters: {len(parser.get_character_set(ranges))}")
    
    # Test symbols
    print("\nTest symbols:")
    ranges = parser.parse_symbols("ABC123")
    print(f"ABC123 -> {ranges}")
    print(f"Expanded: {parser.expand_ranges(ranges)}")
    
    # Test validation
    print("\nTest validation:")
    ranges = parser.parse_range("0x20-0x7F,0x30-0x39")
    warnings = parser.validate_ranges(ranges)
    print(f"Warnings: {warnings}")
    
    # Test presets
    print("\nPreset ranges:")
    for name, range_str in get_preset_ranges().items():
        print(f"{name}: {range_str}")
