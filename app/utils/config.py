import json
import os

class AppConfig:
    # Defaults
    WINDOW_WIDTH = 1200
    WINDOW_HEIGHT = 900
    FONT_FAMILY = 'Helvetica'
    FONT_SIZE_BASE = 13
    FONT_SIZE_HEADER = 24
    FONT_SIZE_STATUS = 13
    
    # Determine config path relative to this file: e.g. .../app/utils/config.py -> .../app/config/config.json
    _utils_dir = os.path.dirname(os.path.abspath(__file__))
    _app_dir = os.path.dirname(_utils_dir)
    _config_dir = os.path.join(_app_dir, 'config')
    _config_path = os.path.join(_config_dir, 'config.json')

    @classmethod
    def load(cls):
        if os.path.exists(cls._config_path):
            try:
                with open(cls._config_path, 'r') as f:
                    data = json.load(f)
                    cls.WINDOW_WIDTH = data.get('width', cls.WINDOW_WIDTH)
                    cls.WINDOW_HEIGHT = data.get('height', cls.WINDOW_HEIGHT)
                    cls.FONT_SIZE_BASE = data.get('font_base', cls.FONT_SIZE_BASE)
                    cls.FONT_SIZE_HEADER = data.get('font_header', cls.FONT_SIZE_HEADER)
                    cls.FONT_SIZE_STATUS = data.get('font_status', cls.FONT_SIZE_STATUS)
            except:
                pass # Ignore errors, use defaults

    @classmethod
    def save(cls):
        # Ensure directory exists
        if not os.path.exists(cls._config_dir):
            os.makedirs(cls._config_dir, exist_ok=True)
            
        data = {
            'width': cls.WINDOW_WIDTH,
            'height': cls.WINDOW_HEIGHT,
            'font_base': cls.FONT_SIZE_BASE,
            'font_header': cls.FONT_SIZE_HEADER,
            'font_status': cls.FONT_SIZE_STATUS
        }
        with open(cls._config_path, 'w') as f:
            json.dump(data, f, indent=4)
            
    # Helper to get dynamic style tuples (though we will prefer named styles)
    @classmethod
    def get_header_font(cls):
        return (cls.FONT_FAMILY, cls.FONT_SIZE_HEADER, 'bold')
        
    @classmethod
    def get_status_font(cls):
        return (cls.FONT_FAMILY, cls.FONT_SIZE_STATUS, 'bold')
