"""
Configuration management module for LVFontConv
Handles application settings and project configurations
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional, List
from dataclasses import dataclass, asdict, field

from utils.logger import get_logger

logger = get_logger()


@dataclass
class FontConfig:
    """Configuration for a single font"""
    path: str
    ranges: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FontConfig':
        """Create from dictionary"""
        return cls(**data)


@dataclass
class ConversionParams:
    """Font conversion parameters"""
    size: int = 16
    bpp: int = 4
    format: str = 'lvgl'
    compress: bool = True
    kerning: bool = True
    lcd: bool = False
    lcd_v: bool = False
    use_color_info: bool = False
    no_prefilter: bool = False
    byte_align: bool = False
    force_fast_kern: bool = False
    autohint_off: bool = False
    autohint_strong: bool = False
    lv_include: str = ''
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversionParams':
        """Create from dictionary"""
        return cls(**data)


@dataclass
class ProjectConfig:
    """Complete project configuration"""
    version: str = "1.0"
    fonts: List[FontConfig] = field(default_factory=list)
    params: ConversionParams = field(default_factory=ConversionParams)
    output: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'version': self.version,
            'fonts': [f.to_dict() for f in self.fonts],
            'params': self.params.to_dict(),
            'output': self.output
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProjectConfig':
        """Create from dictionary"""
        return cls(
            version=data.get('version', '1.0'),
            fonts=[FontConfig.from_dict(f) for f in data.get('fonts', [])],
            params=ConversionParams.from_dict(data.get('params', {})),
            output=data.get('output', '')
        )


class Config:
    """
    Configuration manager for LVFontConv
    
    Manages application settings and project configurations.
    """
    
    def __init__(self):
        """Initialize configuration manager"""
        self.config_dir = Path.home() / '.lvfontconv'
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self.settings_file = self.config_dir / 'settings.json'
        self.settings: Dict[str, Any] = {}
        
        self._load_settings()
    
    def _load_settings(self) -> None:
        """Load application settings from file"""
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    self.settings = json.load(f)
                logger.info(f"Loaded settings from {self.settings_file}")
            except Exception as e:
                logger.error(f"Failed to load settings: {e}")
                self.settings = {}
        else:
            # Initialize default settings
            self.settings = self._get_default_settings()
            self._save_settings()
    
    def _get_default_settings(self) -> Dict[str, Any]:
        """Get default application settings"""
        return {
            'window': {
                'width': 1200,
                'height': 800,
                'maximized': False,
                'splitter_sizes': [300, 900]
            },
            'theme': 'light',
            'last_directory': str(Path.home()),
            'recent_projects': [],
            'max_recent_projects': 10,
            'preview': {
                'background_type': 'checkerboard',
                'background_color': '#FFFFFF',
                'grid_size': 8,
                'color_depth': 32,
                'zoom_level': 100
            },
            'conversion': {
                'default_size': 16,
                'default_bpp': 4,
                'default_format': 'lvgl',
                'default_compress': True,
                'default_kerning': True
            }
        }
    
    def _save_settings(self) -> None:
        """Save application settings to file"""
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2)
            logger.info(f"Saved settings to {self.settings_file}")
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a setting value
        
        Args:
            key: Setting key (supports dot notation, e.g., 'window.width')
            default: Default value if key doesn't exist
            
        Returns:
            Setting value or default
        """
        keys = key.split('.')
        value = self.settings
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """
        Set a setting value
        
        Args:
            key: Setting key (supports dot notation, e.g., 'window.width')
            value: Setting value
        """
        keys = key.split('.')
        settings = self.settings
        
        # Navigate to the parent dict
        for k in keys[:-1]:
            if k not in settings:
                settings[k] = {}
            settings = settings[k]
        
        # Set the value
        settings[keys[-1]] = value
        self._save_settings()
    
    def add_recent_project(self, project_path: str) -> None:
        """
        Add a project to recent projects list
        
        Args:
            project_path: Path to the project file
        """
        recent = self.get('recent_projects', [])
        
        # Remove if already exists
        if project_path in recent:
            recent.remove(project_path)
        
        # Add to beginning
        recent.insert(0, project_path)
        
        # Limit to max recent projects
        max_recent = self.get('max_recent_projects', 10)
        recent = recent[:max_recent]
        
        self.set('recent_projects', recent)
    
    def get_recent_projects(self) -> List[str]:
        """
        Get list of recent project files
        
        Returns:
            List of recent project file paths
        """
        recent = self.get('recent_projects', [])
        # Filter out non-existent files
        return [p for p in recent if Path(p).exists()]
    
    def save_project(self, project: ProjectConfig, filepath: str) -> bool:
        """
        Save project configuration to file
        
        Args:
            project: Project configuration
            filepath: Path to save file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            filepath = Path(filepath)
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(project.to_dict(), f, indent=2)
            
            logger.info(f"Saved project to {filepath}")
            self.add_recent_project(str(filepath))
            return True
        except Exception as e:
            logger.error(f"Failed to save project: {e}")
            return False
    
    def load_project(self, filepath: str) -> Optional[ProjectConfig]:
        """
        Load project configuration from file
        
        Args:
            filepath: Path to project file
            
        Returns:
            ProjectConfig if successful, None otherwise
        """
        try:
            filepath = Path(filepath)
            if not filepath.exists():
                logger.error(f"Project file not found: {filepath}")
                return None
            
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            project = ProjectConfig.from_dict(data)
            logger.info(f"Loaded project from {filepath}")
            self.add_recent_project(str(filepath))
            return project
        except Exception as e:
            logger.error(f"Failed to load project: {e}")
            return None


# Global config instance
_config = Config()


def get_config() -> Config:
    """Get the global configuration instance"""
    return _config


if __name__ == "__main__":
    # Test the config module
    config = get_config()
    
    # Test settings
    print(f"Window width: {config.get('window.width')}")
    print(f"Theme: {config.get('theme')}")
    
    config.set('test.value', 123)
    print(f"Test value: {config.get('test.value')}")
    
    # Test project config
    project = ProjectConfig()
    project.fonts.append(FontConfig(path="/path/to/font.ttf", ranges=["0x20-0x7F"]))
    project.params.size = 24
    project.output = "/path/to/output.c"
    
    print(f"Project dict: {json.dumps(project.to_dict(), indent=2)}")
