import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def send_verification_email(to_email: str, verification_url: str):
    # Your Gmail credentials
    gmail_user = '20it099@gmail.com'  # Your Gmail address
    gmail_password = 'Aayush@*1@*#'  # App password generated for your application

    # Email content
    subject = 'Verify Your Email'
    body = f'Click <a href="{verification_url}">here</a> to verify your email.'

    msg = MIMEMultipart()
    msg['From'] = gmail_user
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'html'))

    try:
        # Establish a secure session with Gmail's outgoing SMTP server using your Gmail account
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.ehlo()
        server.login(gmail_user, gmail_password)
        server.sendmail(gmail_user, to_email, msg.as_string())
        server.close()
        print('Email sent successfully')
    except Exception as e:
        print(f'Failed to send email: {str(e)}')
