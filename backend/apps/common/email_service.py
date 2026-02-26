"""
Nova — Email Service
======================
Sends transactional emails using SMTP settings stored in SystemSetting.
Falls back gracefully if SMTP is not configured.
"""

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger('nova.email')


def _get_smtp_settings() -> dict | None:
    """Fetch SMTP configuration from the database SystemSetting table."""
    from apps.common.domain.settings_model import SystemSetting

    host = SystemSetting.get('smtp.host', '')
    port = SystemSetting.get('smtp.port', 587)
    username = SystemSetting.get('smtp.username', '')
    password = SystemSetting.get('smtp.password', '')
    from_email = SystemSetting.get('smtp.from_email', '')
    from_name = SystemSetting.get('smtp.from_name', 'Nova Library')
    use_tls = SystemSetting.get('smtp.use_tls', True)

    if not host or not from_email:
        return None

    return {
        'host': host,
        'port': int(port) if isinstance(port, str) else port,
        'username': username,
        'password': password,
        'from_email': from_email,
        'from_name': from_name,
        'use_tls': use_tls if isinstance(use_tls, bool) else str(use_tls).lower() in ('true', '1', 'yes'),
    }


def send_email(to_email: str, subject: str, html_body: str, text_body: str = '') -> tuple[bool, str]:
    """
    Send an email via SMTP using DB-stored settings.
    Returns (True, '') on success, (False, error_detail) on failure.
    """
    settings = _get_smtp_settings()
    if not settings:
        msg = 'SMTP not configured. Please set at least the SMTP host and from-email address.'
        logger.warning('SMTP not configured — email not sent to %s', to_email)
        return False, msg

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{settings['from_name']} <{settings['from_email']}>"
        msg['To'] = to_email

        if text_body:
            msg.attach(MIMEText(text_body, 'plain'))
        msg.attach(MIMEText(html_body, 'html'))

        with smtplib.SMTP(settings['host'], settings['port'], timeout=15) as server:
            server.ehlo()
            if settings['use_tls']:
                server.starttls()
                server.ehlo()
            if settings['username'] and settings['password']:
                server.login(settings['username'], settings['password'])
            server.sendmail(settings['from_email'], to_email, msg.as_string())

        logger.info('Email sent to %s: %s', to_email, subject)
        return True, ''

    except smtplib.SMTPAuthenticationError as exc:
        detail = f'Authentication failed: {exc.smtp_error.decode("utf-8", errors="replace") if isinstance(exc.smtp_error, bytes) else exc.smtp_error}. Check your username and password (use an App Password for Gmail with 2FA).'
        logger.error('SMTP auth error for %s: %s', to_email, exc)
        return False, detail

    except smtplib.SMTPRecipientsRefused as exc:
        detail = f'Recipient refused: The server rejected the recipient address {to_email}.'
        logger.error('SMTP recipient refused for %s: %s', to_email, exc)
        return False, detail

    except smtplib.SMTPSenderRefused as exc:
        detail = f'Sender refused: The server rejected the from-address. Make sure your SMTP username matches or is authorized to send from {settings["from_email"]}.'
        logger.error('SMTP sender refused for %s: %s', to_email, exc)
        return False, detail

    except (smtplib.SMTPConnectError, ConnectionRefusedError, OSError) as exc:
        detail = f'Connection failed: Could not connect to {settings["host"]}:{settings["port"]}. Verify the host and port are correct.'
        logger.error('SMTP connection error for %s: %s', to_email, exc)
        return False, detail

    except TimeoutError:
        detail = f'Connection timed out: The server {settings["host"]}:{settings["port"]} did not respond. Check if TLS setting is correct for your port.'
        logger.error('SMTP timeout for %s', to_email)
        return False, detail

    except Exception as exc:
        detail = f'Unexpected error: {type(exc).__name__}: {exc}'
        logger.error('Failed to send email to %s: %s', to_email, exc)
        return False, detail


def send_password_reset_otp(to_email: str, otp_code: str, user_first_name: str = '') -> bool:
    """Send the 6-digit OTP for password reset."""
    greeting = f'Hi {user_first_name},' if user_first_name else 'Hi,'

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8"/>
      <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f4f7fa; margin: 0; padding: 40px 20px; }}
        .container {{ max-width: 480px; margin: 0 auto; background: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 24px rgba(0,0,0,0.08); }}
        .header {{ background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%); padding: 32px 32px 24px; text-align: center; }}
        .header h1 {{ color: #fff; margin: 0; font-size: 22px; font-weight: 700; }}
        .header p {{ color: rgba(255,255,255,0.8); margin: 8px 0 0; font-size: 13px; }}
        .body {{ padding: 32px; }}
        .otp-box {{ background: #f0f4ff; border: 2px dashed #2563eb; border-radius: 12px; padding: 24px; text-align: center; margin: 24px 0; }}
        .otp-code {{ font-size: 36px; font-weight: 800; letter-spacing: 8px; color: #1e40af; font-family: 'Courier New', monospace; }}
        .warning {{ background: #fffbeb; border-left: 4px solid #f59e0b; padding: 12px 16px; border-radius: 0 8px 8px 0; font-size: 13px; color: #92400e; margin-top: 20px; }}
        .footer {{ padding: 20px 32px; background: #f9fafb; text-align: center; font-size: 12px; color: #6b7280; }}
      </style>
    </head>
    <body>
      <div class="container">
        <div class="header">
          <h1>🔐 Password Reset</h1>
          <p>Nova Smart Library</p>
        </div>
        <div class="body">
          <p style="color:#374151; font-size:15px;">{greeting}</p>
          <p style="color:#6b7280; font-size:14px;">
            We received a request to reset your password. Use the verification code below to proceed:
          </p>
          <div class="otp-box">
            <div class="otp-code">{otp_code}</div>
            <p style="color:#6b7280; font-size:13px; margin:12px 0 0;">
              This code expires in <strong>10 minutes</strong>
            </p>
          </div>
          <div class="warning">
            ⚠️ If you didn't request this, please ignore this email. Your password will remain unchanged.
          </div>
        </div>
        <div class="footer">
          &copy; Nova Smart Library &middot; This is an automated message
        </div>
      </div>
    </body>
    </html>
    """

    text = f"""{greeting}

Your password reset verification code is: {otp_code}

This code expires in 10 minutes.

If you didn't request this, please ignore this email.

— Nova Smart Library
"""

    success, _ = send_email(to_email, 'Password Reset Code — Nova Library', html, text)
    return success


def send_test_email(to_email: str) -> tuple[bool, str]:
    """Send a test email to verify SMTP configuration."""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8"/>
      <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f4f7fa; margin: 0; padding: 40px 20px; }
        .container { max-width: 480px; margin: 0 auto; background: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 24px rgba(0,0,0,0.08); }
        .header { background: linear-gradient(135deg, #059669 0%, #10b981 100%); padding: 32px 32px 24px; text-align: center; }
        .header h1 { color: #fff; margin: 0; font-size: 22px; font-weight: 700; }
        .body { padding: 32px; text-align: center; }
        .check { font-size: 48px; margin-bottom: 16px; }
        .footer { padding: 20px 32px; background: #f9fafb; text-align: center; font-size: 12px; color: #6b7280; }
      </style>
    </head>
    <body>
      <div class="container">
        <div class="header">
          <h1>SMTP Configuration Test</h1>
        </div>
        <div class="body">
          <div class="check">✅</div>
          <h2 style="color:#059669; margin:0 0 8px;">It works!</h2>
          <p style="color:#6b7280; font-size:14px;">
            Your SMTP settings are configured correctly.<br/>
            Nova Smart Library can now send emails.
          </p>
        </div>
        <div class="footer">
          &copy; Nova Smart Library &middot; SMTP Test Email
        </div>
      </div>
    </body>
    </html>
    """
    text = "SMTP Test — Your Nova Smart Library email configuration is working correctly!"
    return send_email(to_email, 'SMTP Test — Nova Smart Library', html, text)  # Returns (bool, str)
