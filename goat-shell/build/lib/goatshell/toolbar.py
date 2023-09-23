from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.styles import Style
from goatshell.style import styles

def create_toolbar(profile, prefix, vi_mode_enabled, safety_mode_enabled, last_executed_command=None, status_text="", warning_message=None):
    upper_profile = profile.upper()
    upper_prefix = prefix.upper()
    vi_mode_text = "ON" if vi_mode_enabled else "OFF"
    safety_mode_text = "ON" if safety_mode_enabled else "OFF"


    toolbar_class = 'bottom-toolbar-red' if warning_message else 'bottom-toolbar'

    if warning_message:
        toolbar_parts = [ 
               ('class:' + toolbar_class, f'WARNING: {warning_message}')
        ]
    else:
        toolbar_parts = [
                ('class:' + toolbar_class, f'F8 Cloud: {upper_prefix}   F9 Profile: {upper_profile}   F10 VIM {vi_mode_text}   F12 Safe Mode: {safety_mode_text}')
        ]

    if last_executed_command:
        if status_text == "failure":
            toolbar_parts.append(('class:bottom-toolbar', f' | Last Executed: {status_text} => '))
            toolbar_parts.append(('class:failure-text', f'{last_executed_command}'))
        else:
            toolbar_parts.append(('class:bottom-toolbar', ' | Last Executed: '))
            toolbar_parts.append(('class:success-text', f'{last_executed_command}'))

    return FormattedText(toolbar_parts)

