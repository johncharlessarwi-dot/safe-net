"""Outgoing email (verification, password reset, team invites) over SMTP."""
import logging
import smtplib
import ssl
from email.message import EmailMessage

from config import Config

log = logging.getLogger('safenet.mail')


def send_mail(to, subject, body):
    """Returns True if sent. Without MAIL_SERVER the message is only logged."""
    if not Config.MAIL_SERVER:
        log.warning('MAIL_SERVER not set; email to %s not sent: %s\n%s', to, subject, body)
        return False
    msg = EmailMessage()
    msg['From'] = Config.MAIL_DEFAULT_SENDER or Config.MAIL_USERNAME
    msg['To'] = to
    msg['Subject'] = subject
    msg.set_content(body)
    try:
        if Config.MAIL_USE_SSL:
            server = smtplib.SMTP_SSL(Config.MAIL_SERVER, Config.MAIL_PORT, timeout=20,
                                      context=ssl.create_default_context())
        else:
            server = smtplib.SMTP(Config.MAIL_SERVER, Config.MAIL_PORT, timeout=20)
            server.starttls(context=ssl.create_default_context())
        with server:
            if Config.MAIL_USERNAME:
                server.login(Config.MAIL_USERNAME, Config.MAIL_PASSWORD)
            server.send_message(msg)
        return True
    except (OSError, smtplib.SMTPException) as e:
        log.error('sending email to %s failed: %s', to, e)
        return False
