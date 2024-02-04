import threading
from prompt_toolkit import prompt

def run_prompt_in_thread(data):
    result = None

    def target():
        nonlocal result
        result = prompt(f"Are you sure you want to continue with {data}? [y/n]: ")

    thread = threading.Thread(target=target)
    thread.start()
    thread.join()

    return result.lower() in ['y', 'yes']


