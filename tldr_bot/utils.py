from typing import Optional, Tuple


def parse_and_validate_n(command_text: str) -> Tuple[Optional[int], Optional[str]]:
    """
    Parses the N parameter from `/tldr [N]` and validates boundaries.
    Returns:
        (valid_n, error_or_boundary_response)
    """
    parts = command_text.strip().split()
    if len(parts) == 1:
        # Default value if N is omitted
        n = 100
    else:
        try:
            n = int(parts[1])
        except ValueError:
            return None, "Please provide a valid integer for N, e.g. `/tldr 100`"

    if n < 50:
        return None, "Just read it, bro"

    if n > 1000:
        return None, "It's too much, pay for my tokens first!"

    return n, None
