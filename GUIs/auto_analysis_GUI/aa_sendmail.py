import smtplib
import ssl

port = 465 # For SSL
sender_email   = "astroqopt@gmail.com"
password = "ecap_aqo"
# Create a secure SSL context
context = ssl.create_default_context()
message = """\
Subject: Correlation analysis

Excellent news: Your correlation analysis has finished!"""

def send_email(receiver_email):
	print ("Send finishing mail to {}".format(receiver_email))
	with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
		server.login("astroqopt@gmail.com", password)
		server.sendmail(sender_email, receiver_email, message)