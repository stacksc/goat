import random
import string

def get_random_password(length):
    random_source = string.ascii_letters + string.digits
    # select 1 lowercase
    password = random.choice(string.ascii_lowercase)
    # select 1 uppercase
    password += random.choice(string.ascii_uppercase)
    # select 1 digit
    password += random.choice(string.digits)

    # generate other characters
    for i in range(length):
        password += random.choice(random_source)

    password_list = list(password)
    # shuffle all characters
    random.SystemRandom().shuffle(password_list)
    password = ''.join(password_list)
    return password

def get_latest_region(profile_name):
    CONFIG = AWSConfig()
    REGION = CONFIG.get_from_config('creds', 'region', profile_name=profile_name)
    if REGION is None:
        return 'us-east-1'
    return REGION
