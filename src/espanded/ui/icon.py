"""Application icon generation for Espanded."""

from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QLinearGradient, QPen, QFont
from PySide6.QtCore import Qt, QRect


def create_app_icon(size: int = 256) -> QIcon:
    """Create the Espanded application icon.

    Creates a modern, gradient-based icon with the letter 'E' for Espanded.
    The icon uses a blue gradient background with white text.

    Args:
        size: Icon size in pixels (default: 256 for high quality)

    Returns:
        QIcon with multiple sizes for different display contexts
    """
    # Create multiple sizes for better display at different resolutions
    icon = QIcon()
    for icon_size in [16, 24, 32, 48, 64, 128, 256]:
        pixmap = _create_icon_pixmap(icon_size)
        icon.addPixmap(pixmap)

    return icon


def _create_icon_pixmap(size: int) -> QPixmap:
    """Create a single size icon pixmap.

    Args:
        size: Icon size in pixels

    Returns:
        QPixmap with the rendered icon
    """
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

    # Define gradient colors (modern blue gradient)
    gradient = QLinearGradient(0, 0, size, size)
    gradient.setColorAt(0.0, QColor(59, 130, 246))   # Primary blue
    gradient.setColorAt(0.5, QColor(37, 99, 235))    # Deeper blue
    gradient.setColorAt(1.0, QColor(29, 78, 216))    # Even deeper blue

    # Draw rounded rectangle background
    padding = 0
    painter.setBrush(gradient)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawRoundedRect(
        padding,
        padding,
        size - 2 * padding,
        size - 2 * padding,
        size * 0.2,  # Corner radius (20% of size)
        size * 0.2
    )

    # Draw subtle border for depth
    border_color = QColor(255, 255, 255, 40)  # Semi-transparent white
    border_pen = QPen(border_color)
    border_pen.setWidth(max(1, size // 64))
    painter.setPen(border_pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawRoundedRect(
        padding + 1,
        padding + 1,
        size - 2 * padding - 2,
        size - 2 * padding - 2,
        size * 0.2,
        size * 0.2
    )

    # Draw letter 'E' in white
    painter.setPen(QColor(255, 255, 255))
    font = QFont("Segoe UI", int(size * 0.5), QFont.Weight.Bold)
    painter.setFont(font)

    # Center the text
    text_rect = QRect(0, 0, size, size)
    painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, "E")

    painter.end()
    return pixmap


def save_icon_file(filepath: str, size: int = 256):
    """Save the application icon to a file.

    Args:
        filepath: Path where to save the icon (supports .png, .ico, etc.)
        size: Icon size in pixels
    """
    pixmap = _create_icon_pixmap(size)
    pixmap.save(filepath)
