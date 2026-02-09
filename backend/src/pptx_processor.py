from markitdown import MarkItDown
from typing import Dict
import os
import logging

logger = logging.getLogger(__name__)


class PPTXProcessor:
    """
    PPTX processor using Microsoft MarkItDown for text extraction.
    Preserves structure: tables, lists, headers, formatting.
    """

    def __init__(self):
        # Initialize MarkItDown converter
        self.converter = MarkItDown()

    def _count_slides(self, markdown_text: str) -> int:
        """Count slides using multiple detection patterns."""
        import re
        # Pattern 1: MarkItDown HTML comments (<!-- Slide number: N -->)
        slide_count = len(re.findall(r'<!-- Slide number: \d+ -->', markdown_text))
        if slide_count > 0:
            return slide_count
        # Pattern 2: ## Slide N headers
        slide_count = markdown_text.count("## Slide")
        if slide_count > 0:
            return slide_count
        # Pattern 3: Any level-2 headers as fallback
        slide_count = markdown_text.count("\n## ")
        return max(slide_count, 1)  # At least 1

    def extract_to_markdown(self, pptx_path: str) -> Dict:
        """
        Extract PPTX to markdown using Microsoft MarkItDown.
        Preserves structure: tables, lists, headers, formatting.

        Args:
            pptx_path: Absolute path to the PPTX file

        Returns:
            {
                "markdown_content": str,  # Full markdown text
                "slide_count": int,       # Number of slides
                "has_tables": bool,       # Contains tables
                "has_images": bool,       # Contains images
                "text_length": int,       # Character count
                "structure_preserved": bool  # True (MarkItDown preserves structure)
            }

        Raises:
            FileNotFoundError: If PPTX file doesn't exist
            ValueError: If file is not a valid PPTX or conversion fails
        """
        # Validate file extension first
        if not pptx_path.lower().endswith('.pptx'):
            raise ValueError(f"File must be a PPTX file: {pptx_path}")

        # Validate file exists
        if not os.path.exists(pptx_path):
            raise FileNotFoundError(f"PPTX file not found: {pptx_path}")

        try:
            # Convert PPTX to markdown
            result = self.converter.convert(pptx_path)
            markdown_text = result.text_content

            if not markdown_text or len(markdown_text.strip()) == 0:
                raise ValueError("PPTX file appears to be empty or unreadable")

        except Exception as e:
            logger.error(f"Error converting PPTX to markdown: {e}")
            raise ValueError(f"Failed to convert PPTX file: {str(e)}")

        # Analyze content
        slide_count = self._count_slides(markdown_text)

        # Detect tables (markdown table syntax: | ... | and ----)
        # More robust detection: look for pipe characters and dashes
        has_tables = ("|" in markdown_text and "---" in markdown_text) or \
                     ("|" in markdown_text and "|-" in markdown_text)

        # Detect images (markdown image syntax: ![...])
        has_images = "![" in markdown_text or "[image]" in markdown_text.lower()

        # Text length for analysis
        text_length = len(markdown_text)

        return {
            "markdown_content": markdown_text,
            "slide_count": slide_count,
            "has_tables": has_tables,
            "has_images": has_images,
            "text_length": text_length,
            "structure_preserved": True  # MarkItDown preserves structure
        }

    def analyze_visual_density(self, markdown_content: str) -> Dict:
        """
        Analyze visual density of the presentation.

        Args:
            markdown_content: Markdown text from extract_to_markdown()

        Returns:
            {
                "table_count": int,
                "image_count": int,
                "visual_density": float,  # Ratio of visual elements to slides
                "is_chart_heavy": bool    # >50% slides with visuals
            }
        """
        # Count tables
        table_count = markdown_content.count("|---")

        # Count images
        image_count = markdown_content.count("![")

        # Count slides
        slide_count = self._count_slides(markdown_content)

        # Calculate visual density
        total_visuals = table_count + image_count
        visual_density = total_visuals / slide_count

        # Flag as chart-heavy if >50% slides have visuals
        is_chart_heavy = visual_density > 0.5

        return {
            "table_count": table_count,
            "image_count": image_count,
            "visual_density": round(visual_density, 2),
            "is_chart_heavy": is_chart_heavy
        }
