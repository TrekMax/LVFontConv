"""
Project management module for LVFontConv

Handles project file save/load operations with JSON serialization.
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict

from utils.logger import get_logger

logger = get_logger()


@dataclass
class FontSource:
    """Font source configuration"""
    path: str
    ranges: List[str]
    symbols: str
    display_name: str = ""
    
    @property
    def char_count(self) -> int:
        """估算字符数"""
        count = len(self.symbols)
        for r in self.ranges:
            if '-' in r:
                parts = r.split('-')
                if len(parts) == 2:
                    try:
                        start = int(parts[0], 0)
                        end = int(parts[1], 0)
                        count += (end - start + 1)
                    except:
                        pass
        return count
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "path": self.path,
            "ranges": self.ranges,
            "symbols": self.symbols,
            "display_name": self.display_name or Path(self.path).stem
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FontSource':
        """Create from dictionary (JSON deserialization)"""
        return cls(
            path=data["path"],
            ranges=data.get("ranges", []),
            symbols=data.get("symbols", ""),
            display_name=data.get("display_name", "")
        )


class Project:
    """LVFontConv project"""
    
    VERSION = "1.0"
    
    def __init__(self):
        # Import here to avoid circular dependency
        from ui.config_widget import ConvertConfig
        
        self.file_path: Optional[str] = None
        self.fonts: List[FontSource] = []
        self.config: ConvertConfig = ConvertConfig()
        self.modified = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert project to dictionary for JSON serialization"""
        return {
            "version": self.VERSION,
            "fonts": [font.to_dict() for font in self.fonts],
            "config": self.config.to_dict()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Project':
        """Create project from dictionary (JSON deserialization)"""
        # Import here to avoid circular dependency
        from ui.config_widget import ConvertConfig
        
        project = cls()
        
        # Check version
        version = data.get("version", "1.0")
        if version != cls.VERSION:
            logger.warning(f"Project version mismatch: {version} != {cls.VERSION}")
        
        # Load fonts
        fonts_data = data.get("fonts", [])
        project.fonts = [FontSource.from_dict(f) for f in fonts_data]
        
        # Load config
        config_data = data.get("config", {})
        project.config = ConvertConfig.from_dict(config_data)
        
        project.modified = False
        return project
    
    def save(self, file_path: str) -> bool:
        """
        Save project to file
        
        Args:
            file_path: Path to save project file (.lvfc)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure .lvfc extension
            path = Path(file_path)
            if path.suffix != '.lvfc':
                path = path.with_suffix('.lvfc')
            
            # Convert to JSON
            data = self.to_dict()
            
            # Write to file
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            self.file_path = str(path)
            self.modified = False
            
            logger.info(f"Project saved: {path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save project: {e}")
            return False
    
    def load(self, file_path: str) -> bool:
        """
        Load project from file
        
        Args:
            file_path: Path to project file (.lvfc)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            path = Path(file_path)
            
            # Check file exists
            if not path.exists():
                logger.error(f"Project file not found: {path}")
                return False
            
            # Read JSON
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Parse project
            loaded_project = Project.from_dict(data)
            
            # Update current project
            self.fonts = loaded_project.fonts
            self.config = loaded_project.config
            self.file_path = str(path)
            self.modified = False
            
            logger.info(f"Project loaded: {path} ({len(self.fonts)} fonts)")
            return True
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid project file format: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to load project: {e}")
            return False
    
    def new(self):
        """Create new empty project"""
        # Import here to avoid circular dependency
        from ui.config_widget import ConvertConfig
        
        self.file_path = None
        self.fonts = []
        self.config = ConvertConfig()
        self.modified = False
        logger.info("New project created")
    
    def mark_modified(self):
        """Mark project as modified"""
        self.modified = True
    
    @property
    def is_modified(self) -> bool:
        """Check if project has unsaved changes"""
        return self.modified
    
    @property
    def display_name(self) -> str:
        """Get display name for window title"""
        if self.file_path:
            name = Path(self.file_path).stem
            return f"{name}{'*' if self.modified else ''}"
        return f"Untitled{'*' if self.modified else ''}"
