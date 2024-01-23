from prompt_toolkit import PromptSession

# Define a custom PromptSession class
class DynamicPromptSession(PromptSession):
    def __init__(self, vi_mode_enabled=True, *args, **kwargs):
        self.vi_mode_enabled = vi_mode_enabled
        super().__init__(*args, **kwargs)

    def prompt(self, *args, **kwargs):
        # Set the 'vi_mode' parameter based on 'vi_mode_enabled'
        kwargs['vi_mode'] = self.vi_mode_enabled
        return super().prompt(*args, **kwargs)
