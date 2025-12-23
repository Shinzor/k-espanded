"""Tag color management for visual organization."""

from typing import Dict


# Predefined color palette for tags
TAG_COLORS = {
    "blue": {"bg": "#3b82f6", "text": "#ffffff"},
    "indigo": {"bg": "#6366f1", "text": "#ffffff"},
    "purple": {"bg": "#a855f7", "text": "#ffffff"},
    "pink": {"bg": "#ec4899", "text": "#ffffff"},
    "red": {"bg": "#ef4444", "text": "#ffffff"},
    "orange": {"bg": "#f97316", "text": "#ffffff"},
    "amber": {"bg": "#f59e0b", "text": "#ffffff"},
    "yellow": {"bg": "#eab308", "text": "#000000"},
    "lime": {"bg": "#84cc16", "text": "#000000"},
    "green": {"bg": "#22c55e", "text": "#ffffff"},
    "emerald": {"bg": "#10b981", "text": "#ffffff"},
    "teal": {"bg": "#14b8a6", "text": "#ffffff"},
    "cyan": {"bg": "#06b6d4", "text": "#ffffff"},
    "sky": {"bg": "#0ea5e9", "text": "#ffffff"},
    "gray": {"bg": "#6b7280", "text": "#ffffff"},
    "slate": {"bg": "#64748b", "text": "#ffffff"},
}


class TagColorManager:
    """Manages tag color assignments and persistence."""

    def __init__(self):
        """Initialize tag color manager."""
        # Map tag names to color keys
        self._tag_colors: Dict[str, str] = {}
        # Default color for unassigned tags
        self._default_color = "blue"

    def get_color(self, tag: str) -> dict:
        """Get the color scheme for a tag.

        Args:
            tag: Tag name

        Returns:
            Dict with 'bg' and 'text' color values
        """
        color_key = self._tag_colors.get(tag, self._default_color)
        return TAG_COLORS.get(color_key, TAG_COLORS[self._default_color])

    def set_color(self, tag: str, color_key: str):
        """Set the color for a tag.

        Args:
            tag: Tag name
            color_key: Color key from TAG_COLORS
        """
        if color_key in TAG_COLORS:
            self._tag_colors[tag] = color_key

    def get_tag_color_key(self, tag: str) -> str:
        """Get the color key for a tag.

        Args:
            tag: Tag name

        Returns:
            Color key (e.g., "blue", "green")
        """
        return self._tag_colors.get(tag, self._default_color)

    def remove_color(self, tag: str):
        """Remove color assignment for a tag (revert to default).

        Args:
            tag: Tag name
        """
        if tag in self._tag_colors:
            del self._tag_colors[tag]

    def get_all_colors(self) -> Dict[str, str]:
        """Get all tag color assignments.

        Returns:
            Dict mapping tag names to color keys
        """
        return self._tag_colors.copy()

    def load_from_dict(self, data: Dict[str, str]):
        """Load tag colors from a dictionary.

        Args:
            data: Dict mapping tag names to color keys
        """
        self._tag_colors = {
            tag: color
            for tag, color in data.items()
            if color in TAG_COLORS
        }

    def to_dict(self) -> Dict[str, str]:
        """Convert tag colors to dictionary for persistence.

        Returns:
            Dict mapping tag names to color keys
        """
        return self._tag_colors.copy()


# Singleton instance
_tag_color_manager: TagColorManager | None = None


def get_tag_color_manager() -> TagColorManager:
    """Get the global tag color manager instance."""
    global _tag_color_manager

    if _tag_color_manager is None:
        _tag_color_manager = TagColorManager()

    return _tag_color_manager
