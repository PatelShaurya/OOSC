"""
Text cleaning module to normalize extracted PDF text while preserving legal meaning.
"""
import re


class TextCleaner:
    """Normalizes whitespace, line endings, and layout artifacts without altering content."""

    @staticmethod
    def clean_text(text: str) -> str:
        """
        Cleans extracted text by normalizing whitespace while keeping structure.

        Rules:
        - Normalize line endings (\r\n -> \n)
        - Strip trailing whitespace from each line
        - Collapse multiple consecutive blank lines into max 2 blank lines (preserving paragraph structure)
        - Collapse multiple spaces/tabs within lines
        - Strip leading/trailing space from overall string

        Args:
            text: Raw extracted text string.

        Returns:
            Cleaned text string.
        """
        if not text:
            return ""

        # Normalize line endings
        text = text.replace("\r\n", "\n").replace("\r", "\n")

        # Replace non-breaking spaces with standard space
        text = text.replace("\xa0", " ")

        # Clean line by line
        lines = text.split("\n")
        cleaned_lines = []
        for line in lines:
            # Replace multiple internal whitespaces (tabs, multiple spaces) with single space
            cleaned_line = re.sub(r"[ \t]+", " ", line).strip()
            cleaned_lines.append(cleaned_line)

        # Rejoin with newlines
        cleaned_text = "\n".join(cleaned_lines)

        # Reduce 3 or more consecutive newlines down to 2 newlines (preserving double newline paragraph breaks)
        cleaned_text = re.sub(r"\n{3,}", "\n\n", cleaned_text)

        return cleaned_text.strip()
