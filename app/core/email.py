from fastapi_mail import ConnectionConfig

def get_email_conf(settings):
    return ConnectionConfig(
        MAIL_USERNAME="hoanglinh6794@gmail.com",
        MAIL_PASSWORD="exjckevdixmdjbab",  # no spaces
        MAIL_FROM="hoanglinh6794@gmail.com",
        MAIL_SERVER="smtp.gmail.com",
        MAIL_PORT=587,
        MAIL_STARTTLS=True,
        MAIL_SSL_TLS=False,
        USE_CREDENTIALS=True,
        VALIDATE_CERTS=False,
    )