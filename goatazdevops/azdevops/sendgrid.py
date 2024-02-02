import sendgrid
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from python_http_client.exceptions import ForbiddenError
from tabulate import tabulate
from toolbox.getpass import getOtherToken

def send_email(to_email, subject, report_data):
    """
    Sends an email with a report formatted as an HTML table using SendGrid.
    It prompts for 'from_email' and 'SENDGRID_API_KEY' if they are not found in the environment or config store.

    Parameters:
    to_email (str): The recipient's email address.
    subject (str): The subject of the email.
    report_data (list of lists): The report data to be formatted and sent.
    """

    from configstore.configstore import Config
    CONFIG = Config('azdev')
    user_profile = 'sendgrid'

    if user_profile not in CONFIG.PROFILES:
        CONFIG.create_profile(user_profile)
    PROFILE = CONFIG.get_profile(user_profile)

    # Check and get 'from_email' from config
    try:
        from_email = PROFILE.get('config', {}).get('email')
    except:
        pass # fix in a second

    if not from_email:
        from_email = input("INFO: enter the sender's email address (registered w/ SendGrid): ")
        PROFILE.setdefault('config', {})['email'] = from_email
        CONFIG.update_profile(PROFILE)

    # Convert report data to an HTML table
    html_content = generate_html_table(report_data)

    message = Mail(
        from_email=from_email,
        to_emails=to_email,
        subject=subject,
        html_content=html_content)

    # Token retrieval and SendGrid client initialization
    try:
        TOKEN = os.environ.get('SENDGRID_API_KEY')
        if not TOKEN:
            TOKEN = PROFILE.get('config', {}).get('pass')
            if not TOKEN:
                from azdevops.azdevclient import AzDevClient
                AZDEV = AzDevClient()
                auth_mode = 'pass'
                try:
                    TOKEN = AZDEV.get_access_token(user_profile=user_profile)
                except:
                    TOKEN = input("Enter your SendGrid API Key: ")
                    PROFILE.setdefault('config', {})['pass'] = TOKEN
                    CONFIG.update_profile(PROFILE)

        sg = SendGridAPIClient(TOKEN)
        response = sg.send(message)
        print("Email sent successfully.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

def generate_html_table(data):
    """
    Generates an HTML table dynamically from a list of dictionaries.

    Parameters:
    data (list of dict): Each dictionary represents a row in the table.

    Returns:
    str: HTML string representing the table.
    """
    if not data:
        return "No data provided."

    # Dynamically determine headers from keys in the dictionaries
    headers = set()
    for row in data:
        headers.update(row.keys())
    headers = sorted(headers)  # Sort the headers for consistent ordering

    # Start building the table
    html = '<table style="border-collapse: collapse; width: 100%;">'
    html += '<thead><tr style="background-color: #f2f2f2;">'
    for header in headers:
        html += f'<th style="border: 1px solid #dddddd; text-align: left; padding: 8px;">{header}</th>'
    html += '</tr></thead><tbody>'

    # Add rows based on the headers
    for row in data:
        html += '<tr>'
        for header in headers:
            html += f'<td style="border: 1px solid #dddddd; text-align: left; padding: 8px;">{row.get(header, "")}</td>'
        html += '</tr>'

    # Close the table tags
    html += '</tbody></table>'

    return html

