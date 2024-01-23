from prompt_toolkit.key_binding import KeyBindings
from goatshell.ui import getLayout
from prompt_toolkit.keys import Keys

class CustomKeyBindings(KeyBindings):
    def __init__(self, app, goatshell_instance):
        super().__init__()
        self.app = app  # Store the Application reference
        self.goatshell_instance = goatshell_instance

        @self.add(Keys.F7)
        def handle_f7(event):
            print()
            cloud_provider = self.goatshell_instance.prefix
            if cloud_provider != 'goat':
                os_command = f"goat {cloud_provider} extract commands"
                try:
                    result = self.goatshell_instance.execute_os_command(os_command)
                    if result == "failure":
                        print("INFO: failed to execute the command.")
                    else:
                        print(f"INFO: executed the command {os_command}")
                except:
                    pass
            else:
                directory = os.path.dirname(os.path.abspath(__file__))
                os_command = f"python3 {directory}/fetch_goat.py"
                try:
                    os.system(os_command)
                except:
                    pass

            event.app.invalidate()
            event.app.exit(result='re-prompt')  # Signal to re-prompt.

        @self.add(Keys.F8)
        def handle_f8(event):
            goatshell_instance.switch_to_next_provider()
            if self.goatshell_instance.prefix == 'az':
                sub_id, sub_name = self.goatshell_instance.fetch_current_azure_subscription()
                if sub_id and sub_name:
                    self.goatshell_instance.profile = sub_name
                else:
                    self.profile = 'DEFAULT'
            else:
                self.profile = self.goatshell_instance.get_profile(self.goatshell_instance.prefix)
            getLayout()
            self.app.invalidate()
            event.app.exit(result='re-prompt')  # Signal to reprompt.

        @self.add(Keys.F9)
        def handle_f9(event):
            if self.goatshell_instance.prefix == 'az':
                self.goatshell_instance.switch_to_next_subscription()  # Call the method on the Goatshell instance
