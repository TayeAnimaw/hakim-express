import re
from typing import List

def extract_pages_from_activity(activity: str) -> List[str]:
    """
    Extracts the list of accessed pages from the activity string.
    Example input: "Admin accessed Dashboard, Users, and Permissions pages."
    Output: ['Dashboard', 'Users', 'Permissions']
    """
    # Normalize the text to remove 'pages' or 'page' suffixes
    activity = activity.replace('pages', '').replace('page', '')

    # Extract words with capital first letters, usually names of pages
    matches = re.findall(r'\b[A-Z][a-zA-Z]+\b', activity)

    # Remove generic words like "Admin", "Accessed", etc.
    ignore_words = {"Admin", "Accessed", "accessed", "And", "and"}
    pages = [word for word in matches if word not in ignore_words]

    return pages
