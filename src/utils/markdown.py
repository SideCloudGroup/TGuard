"""MarkdownV2 formatting utilities."""


def escape_markdown_v2(text: str) -> str:
    """Escape special characters for MarkdownV2 format.
    
    MarkdownV2 requires escaping these characters outside of code entities:
    _ * [ ] ( ) ~ ` > # + - = | { } . !
    """
    if not text:
        return ""

    # List of characters that need to be escaped in MarkdownV2
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']

    for char in special_chars:
        text = text.replace(char, f'\\{char}')

    return text


def format_user_mention(username: str, first_name: str) -> str:
    """Format user mention for MarkdownV2."""
    if username:
        return f"@{escape_markdown_v2(username)}"
    else:
        return escape_markdown_v2(first_name)


def format_code_inline(text: str) -> str:
    """Format text as inline code for MarkdownV2."""
    return f"`{text}`"


def format_bold(text: str) -> str:
    """Format text as bold for MarkdownV2."""
    return f"*{escape_markdown_v2(text)}*"


def format_italic(text: str) -> str:
    """Format text as italic for MarkdownV2."""
    return f"_{escape_markdown_v2(text)}_"


def format_link(text: str, url: str) -> str:
    """Format text as link for MarkdownV2."""
    return f"[{escape_markdown_v2(text)}]({url})"
