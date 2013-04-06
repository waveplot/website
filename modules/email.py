import smtplib
import passwords

def SendEmail(sender, recipient, subject, body):
    pass_file = open(passwords.EMAIL_PASSWORD_FILE,"r")
    username,password = pass_file.read().split(":")
    pass_file.close()
    password = password.strip('\n')

    session = smtplib.SMTP('smtp.gmail.com', 587)
    session.ehlo()
    session.starttls()
    session.ehlo()
    print "Username: {} Password: {}".format(username,password)
    session.login(username, password)

    headers = ["from: " + sender,
               "subject: " + subject,
               "to: " + recipient,
               "mime-version: 1.0",
               "content-type: text/html"]

    headers = "\r\n".join(headers)

    session.sendmail(sender, recipient, headers + "\r\n\r\n" + body)
    session.quit()
