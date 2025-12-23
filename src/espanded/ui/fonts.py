"""Font loading and management."""

from pathlib import Path
from PySide6.QtGui import QFontDatabase, QFont


def load_custom_fonts():
    """Load custom fonts for the application."""
    font_db = QFontDatabase()

    # Load Lexend variable font
    lexend_path = Path(__file__).parent.parent.parent.parent / "assets" / "fonts" / "Lexend-VariableFont_wght.ttf"

    if lexend_path.exists():
        font_id = font_db.addApplicationFont(str(lexend_path))
        if font_id != -1:
            families = font_db.applicationFontFamilies(font_id)
            if families:
                return families[0]  # Return the Lexend family name

    # Fallback to system fonts
    return None


def get_app_font(size: int = 10, weight: int = QFont.Weight.Normal) -> QFont:
    """Get the application font with specified size and weight.

    Args:
        size: Font size in points
        weight: Font weight (use QFont.Weight enums)

    Returns:
        QFont instance
    """
    # Try to use Lexend if available
    font_db = QFontDatabase()
    families = font_db.families()

    if "Lexend" in families:
        font = QFont("Lexend", size)
        font.setWeight(weight)
        return font

    # Fallback to system default
    font = QFont()
    font.setPointSize(size)
    font.setWeight(weight)
    return font


# Global font family name (set after loading)
APP_FONT_FAMILY = None
