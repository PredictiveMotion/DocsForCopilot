def read_links_from_file(file_path):
    """Read links from a file and return them as a list."""
    with open(file_path, 'r') as file:
        return [line.strip() for line in file if line.strip()]



# def read_links_from_file(file_path):
#     """Read links from a file and return a list of non-empty links."""
#     with open(file_path, "r", encoding="utf-8") as file:
#         return [link.strip() for link in file.readlines() if link.strip()]
