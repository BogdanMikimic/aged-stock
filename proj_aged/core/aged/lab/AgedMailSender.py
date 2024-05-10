class MailSender():
    def __init__(self, recipient, titlu, continut, numeAtasament1, numeAtasament2):
        # se asteapta ca recipientul sa fie da la BC - asa ca completeaza el de la @ incolo inclusiv
        # continut e textul mailului
        # numeAtasament1 si numeAtasament2 asteapt asa primeasca numele fisierelor csv, fara mexia/ - asta o adauga el
        import smtplib, ssl
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        from email.mime.base import MIMEBase
        from email import encoders

        # email server stuff
        server_mail = 'smtp.gmail.com'
        port = 465

        # user (sender) & parola & receiver
        sender = 'dome_gmail_email@gmail.com'
        parola = 'mypassword'
        receiver = f'{recipient}@choco_lux.com'

        # mail content (from/to/title)
        message = MIMEMultipart()
        message['Subject'] = titlu
        message['From'] = sender
        message['To'] = receiver

        # text email (write text and type it into email)
        mail_ca_text = continut
        part1 = MIMEText(mail_ca_text, 'plain')
        message.attach(part1)

        # attachment 1 - csv log
        attach1 = MIMEBase('application', "octet-stream")
        attach1.set_payload(open(f'media/{numeAtasament1}', "rb").read())
        encoders.encode_base64(attach1)
        attach1.add_header('Content-Disposition', f'attachment; filename="{numeAtasament1}"')
        message.attach(attach1)

        # attachment 2 - csv stocuri
        attach2 = MIMEBase('application', "octet-stream")
        attach2.set_payload(open(f'media/{numeAtasament2}', "rb").read())
        encoders.encode_base64(attach2)
        attach2.add_header('Content-Disposition', f'attachment; filename="{numeAtasament2}"')
        message.attach(attach2)

        # trimite mail
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(server_mail, port, context = context) as server:
            server.login(sender, parola)
            server.sendmail(sender, receiver, message.as_string())

