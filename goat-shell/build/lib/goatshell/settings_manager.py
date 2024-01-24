import configparser
import os

class SettingsManager:
    def __init__(self):
        self.shell_dir = os.path.expanduser("~/goat/shell/")
        self.config_path = os.path.join(self.shell_dir, 'config.ini')
        self.config = configparser.ConfigParser()
        self._load_config()

    def _load_config(self):
        # Load existing settings if they exist
        if os.path.exists(self.config_path):
            self.config.read(self.config_path)
        else:
            # Create default settings section if it doesn't exist
            self.config['Settings'] = {}

    def save_setting(self, setting_key, setting_value):
        """Save a setting to config.ini."""
        self.config['Settings'][setting_key] = str(setting_value)
        self._save_config()

    def load_setting(self, setting_key, default_value=None):
        """Load a setting from config.ini."""
        return self.config['Settings'].get(setting_key, default_value)

    def _save_config(self):
        # Create directory if it doesn't exist
        if not os.path.exists(self.shell_dir):
            os.makedirs(self.shell_dir)

        # Save the configuration file
        with open(self.config_path, 'w') as configfile:
            self.config.write(configfile)

