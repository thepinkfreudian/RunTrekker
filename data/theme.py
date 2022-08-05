

class Theme:

    def __init__(self, theme_data: dict):
        self.fonts = theme_data["fonts"]
        self.colors = theme_data["colors"]
        self.sizes = theme_data["sizes"]