from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys
from goatshell.ui import getLayout
from goatshell.confirm import run_prompt_in_thread
from goatshell.switch_profile import select_profile as select_profile
import os
from configstore.configstore import Config

class CustomKeyBindings(KeyBindings):
    def __init__(self, app, goatshell_instance):
        super().__init__()
        self.app = app  # Store the Application reference
        self.goatshell_instance = goatshell_instance

        @self.add(Keys.F6)
        def _(event):
            if self.goatshell_instance.prefix == 'goat':
                # No need to assign here if toggle_config_store_profile updates the Goatshell instance directly
                self.profile = self.goatshell_instance.toggle_config_store_profile()
                self.goatshell_instance.profile = self.profile
                update_latest_profile(self.goatshell_instance.current_config_store, self.goatshell_instance.profile)
            # Ensure getLayout() and prompt regeneration use the updated Goatshell state
            getLayout()
            self.app.invalidate()
            event.app.exit(result='re-prompt')

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
                data = f'extracting command tree for {cloud_provider}'
                confirmation = run_prompt_in_thread(data)
                if confirmation is True:
                    print("User confirmed:", confirmation)
                    directory = os.path.dirname(os.path.abspath(__file__))
                    os_command = f"python3 {directory}/fetch_goat.py"
                    try:
                        os.system(os_command)
                    except Exception as e:
                       print(f"Failed to execute command: {e}")
                else:
                    print("Action cancelled by user.")

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
                # Call the method on the Goatshell instance to switch Azure subscriptions
                self.goatshell_instance.switch_to_next_subscription()
            elif self.goatshell_instance.prefix == 'goat':
                # Cycle through config stores and update the profile with the returned name
                new_config_store_name = self.goatshell_instance.cycle_config_store()
                # Update the profile to reflect the name of the current config store
                self.goatshell_instance.profile = select_profile(new_config_store_name)
                update_latest_profile(new_config_store_name, self.goatshell_instance.profile)
            else:
                # For other prefixes, cycle through their profiles as before
                self.goatshell_instance.profile = self.goatshell_instance.get_profile(self.goatshell_instance.prefix)
    
            # Refresh UI components to reflect changes
            getLayout()
            self.app.invalidate()
            event.app.exit(result='re-prompt')
    
        @self.add(Keys.F10)
        def handle_f10(event):
            self.goatshell_instance.toggle_vi_mode()
            self.app.invalidate()
            event.app.exit(result='re-prompt')  # Signal to reprompt.

        @self.add(Keys.F12)
        def handle_f12(event):
            self.goatshell_instance.toggle_safety_mode()
            self.app.invalidate()
            event.app.exit(result='re-prompt')  # Signal to reprompt.

def update_latest_profile(config_store, profile_name):
    BASICS = Config(config_store)
    LATEST = BASICS.get_profile('latest')
    if LATEST is None:
        BASICS.create_profile('latest')
        BASICS.update_config(profile_name, 'role', 'latest')
    else:
        BASICS.update_config(profile_name, 'role', 'latest')
