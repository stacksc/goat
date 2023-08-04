"""Library containing the PasswordstateLookup class"""

import requests


class PasswordstateLookup:
    """
    Class to look up passwords from the passwordstate API
    """

    def __init__(self, api_base_url, api_secret):
        self.api_base_url = api_base_url.rstrip("/")
        self.api_secret = api_secret

    class PasswordNotFoundError(Exception):
        """
        Exception raised when a password is not found
        """
        pass

    def get_pw_by_title(self, pw_list_id: str, title: str):
        """
        Retrieve a password from the passwordstate API by title
        or raises PasswordNotFoundError
        :param str pw_list_id: The id of the password list to look up
        :param str title: The title of the password to look up
        :returns str: The password from the passwordstate API
        """
        url = (f"{self.api_base_url}/api/searchpasswords/"
               f"{pw_list_id}"
               f"?title={title}")
        headers = {"APIKey": self.api_secret}
        response = requests.get(url, headers=headers).json()[0]
        try:
            return response["Password"]
        except KeyError:
            raise self.PasswordNotFoundError(
                f"No password found with title {title}"
            )

    def get_login_by_title(self, pw_list_id: str, title: str):
        """
        Retrieve username and password from the passwordstate API by title
        or raises PasswordNotFoundError
        :param str pw_list_id: The id of the password list to look up
        :param str title: The title of the login to look up
        :returns dict: keys "username" and "password"
        """
        url = (f"{self.api_base_url}/api/searchpasswords/"
               f"{pw_list_id}"
               f"?title={title}")
        headers = {"APIKey": self.api_secret}
        response = requests.get(url, headers=headers).json()[0]
        try:
            return {
                "username": response["UserName"],
                "password": response["Password"],
            }
        except KeyError:
            raise self.PasswordNotFoundError(
                f"No login found with title {title}"
            )

    def get_pw(self, pw_id):
        """
        Retrieve a password from the passwordstate API by its ID
        :param str pw_id: The id of the password to look up
        :returns str or None: The password from the passwordstate API
        """
        url = f"{self.api_base_url}/api/passwords/{pw_id}"
        headers = {"APIKey": self.api_secret}
        response = requests.get(url, headers=headers).json()[0]
        if "Password" in response:
            return response["Password"]
        raise self.PasswordNotFoundError(
            f"No password found with ID {pw_id}"
        )

    def get_login(self, pw_id):
        """
        Retrieve a login from the passwordstate API by its ID
        :param str pw_id: The id of the login to look up
        :returns dict: keys "username" and "password"
        """
        url = f"{self.api_base_url}/api/passwords/{pw_id}"
        headers = {"APIKey": self.api_secret}
        response = requests.get(url, headers=headers).json()[0]
        try:
            return {
                "username": response["UserName"],
                "password": response["Password"],
            }
        except KeyError:
            raise self.PasswordNotFoundError(
                f"No login found with ID {pw_id}"
            )

    def get_pw_list(self, pw_list_id):
        """
        Retrieve a list of passwords from the passwordstate API
        :param str pw_list_id: The id of the password list to look up
        :returns list: A list of passwords from the passwordstate API
        """
        url = f"{self.api_base_url}/api/searchpasswords/{pw_list_id}"
        headers = {"APIKey": self.api_secret}
        response = requests.get(url, headers=headers).json()
        try:
            return [
                {
                    "PasswordID": item["PasswordID"],
                    "Title"     : item["Title"],
                    "Password"  : item["Password"],
                    "UserName"  : item["UserName"],
                }
                for item in response
            ]
        except KeyError:
            raise self.PasswordNotFoundError(
                f"No password list found with ID {pw_list_id}"
            )
