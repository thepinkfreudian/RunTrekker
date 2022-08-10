import smtplib
import sys
 
CARRIERS = {
    "att": "@mms.att.net",
    "tmobile": "@tmomail.net",
    "verizon": "@vtex.com",
    "sprint": "@page.nextel.com"
}


def authorize_email(email, password):
    return email, password


def send_message(auth, phone_number, carrier, message):
    recipient = phone_number + CARRIERS[carrier]
 
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(auth[0], auth[1])
 
    server.sendmail(auth[0], recipient, message)

