""" Send a text message via GMail SMTP server.
    Password is a Google App password, not personal Google account password.
    See https://support.google.com/accounts/answer/185833 for instructions."""

import smtplib

 
CARRIERS = {
    "att": "@mms.att.net",
    "tmobile": "@tmomail.net",
    "verizon": "@vtex.com",
    "sprint": "@page.nextel.com"
}


def authorize_email(email, app_password):
    return email, app_password


def send_message(auth, phone_number, carrier, message):
    recipient = phone_number + CARRIERS[carrier]
 
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(auth[0], auth[1])
 
    server.sendmail(auth[0], recipient, message)

