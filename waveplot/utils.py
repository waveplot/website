# -*- coding: utf8 -*-

import smtplib

from waveplot.passwords import passwords

def SendEmail(recipient, subject, message):
    session = smtplib.SMTP('smtp.gmail.com', 587)
    session.ehlo()
    session.starttls()
    session.ehlo()
    session.login(passwords['email']['username'], passwords['email']['password'])

    headers = ["from: " + passwords['email']['username'],
               "subject: " + subject,
               "to: " + recipient,
               "mime-version: 1.0",
               "content-type: text/html"]

    headers = "\r\n".join(headers)

    session.sendmail(passwords['email']['username'], recipient, headers + "\r\n\r\n" + message)
    session.quit()
