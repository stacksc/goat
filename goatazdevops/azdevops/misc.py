from configstore.configstore import Config

def get_default_profile():
    PROFILE = 'default'
    try:
        CONFIG = Config('azdev')
        for PROFILE in CONFIG.PROFILES:
            VAL = CONFIG.get_config('default', PROFILE)
            if VAL == 'Y' or VAL == 'y':
                return PROFILE
    except:
        pass
    return PROFILE

def get_default_url():
    URL = 'default'
    try:
        CONFIG = Config('azdev')
        for PROFILE in CONFIG.PROFILES:
            VAL = CONFIG.get_config('default', PROFILE)
            if VAL == 'Y' or VAL == 'y':
                URL = CONFIG.get_config('url', PROFILE)
                if URL:
                    return URL.upper()  # Ensure URL is not None and convert to uppercase
    except Exception as e:
        print(f"Error in get_default_url: {str(e)}")

    # Check if URL is not None before calling upper()
    if URL is not None:
        return URL.upper()
    else:
        return 'DEFAULT'
