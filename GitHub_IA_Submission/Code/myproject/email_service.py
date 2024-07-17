import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def send_email(subject, sender, recipients, text_body):
    # The email account 
    email = 'Desksbookingsystem@gmail.com'
    # Your app password
    password = 'eelueqxkeprztech'

    #set up of smtplib
    msg = MIMEMultipart()
    msg['From'] = sender
    msg['To'] = ', '.join(recipients)
    msg['Subject'] = subject
    msg.attach(MIMEText(text_body))
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(email, password)
        server.send_message(msg)
        server.quit()
        print('Email sent!')
    except Exception as e:
        print('Something went wrong...', e)
