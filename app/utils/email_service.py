from flask_mail import Message
from .. import mail
import logging
from flask import current_app

logger = logging.getLogger(__name__)


class EmailService:
    """
    Сервис для отправки email сообщений (вертикальный современный шаблон)
    """

    @staticmethod
    def send_verification_email(user_email: str, verification_code: str) -> bool:
        """
        Отправляет email с кодом подтверждения

        Args:
            user_email: Email пользователя
            verification_code: Код подтверждения

        Returns:
            bool: True если email отправлен успешно, False в противном случае
        """
        try:
            subject = "Добро пожаловать в cysu! Подтвердите ваш email"
            current_app.logger.info(f"Sending verification email to {user_email} with code: '{verification_code}' (type: {type(verification_code)}, length: {len(verification_code)})")
            html_body = f"""
            <!DOCTYPE html>
            <html lang="ru">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Подтверждение регистрации - cysu</title>
                <style>
                    body {{
                        margin: 0;
                        padding: 20px;
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                        background-color: #0e0e0f;
                        color: #ffffff;
                    }}
                    .container {{
                        max-width: 600px;
                        margin: 0 auto;
                        background: #1a1a1a;
                        border-radius: 12px;
                        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
                        overflow: hidden;
                    }}
                    .header {{
                        background: linear-gradient(135deg, #007bff 0%, #0056b3 100%);
                        padding: 25px 30px;
                        text-align: center;
                        color: white;
                    }}
                    .header h1 {{
                        margin: 0;
                        font-size: 24px;
                        font-weight: 600;
                    }}
                    .header p {{
                        margin: 8px 0 0 0;
                        opacity: 0.9;
                        font-size: 14px;
                    }}
                    .content {{
                        padding: 40px 30px;
                        text-align: center;
                    }}
                    .verification-title {{
                        font-size: 22px;
                        font-weight: 600;
                        color: #ffffff;
                        margin-bottom: 10px;
                    }}
                    .verification-desc {{
                        color: #b0b0b0;
                        font-size: 16px;
                        margin-bottom: 30px;
                        line-height: 1.5;
                    }}
                    .code-container {{
                        background: linear-gradient(135deg, #2a2a2a 0%, #1a1a1a 100%);
                        border: 2px solid #3a3a3a;
                        border-radius: 12px;
                        padding: 30px;
                        margin: 20px 0;
                        display: inline-block;
                    }}
                    .verification-code {{
                        font-size: 36px;
                        font-weight: 700;
                        font-family: 'Courier New', monospace;
                        color: #ffffff;
                        letter-spacing: 8px;
                        margin: 0;
                    }}
                    .code-info {{
                        color: #b0b0b0;
                        font-size: 14px;
                        margin-top: 15px;
                    }}
                    .footer {{
                        background: #0e0e0f;
                        padding: 30px;
                        text-align: center;
                        border-top: 1px solid #2a2a2a;
                    }}
                    .footer p {{
                        margin: 5px 0;
                        color: #b0b0b0;
                        font-size: 14px;
                    }}
                    .warning {{
                        background: rgba(255, 193, 7, 0.1);
                        border: 1px solid #ffc107;
                        border-radius: 8px;
                        padding: 15px;
                        margin: 20px 0;
                        color: #ffc107;
                        font-size: 14px;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>Добро пожаловать в cysu</h1>
                        <p>Современная образовательная платформа нового поколения</p>
                    </div>
                    <div class="content">
                        <div class="verification-title">Подтвердите ваш email!</div>
                        <div class="verification-desc">
                            Для завершения регистрации введите код<br>
                            подтверждения ниже
                        </div>
                        <div class="code-container">
                            <div class="verification-code">{' '.join(verification_code)}</div>
                            <div class="code-info">Код действителен в течение 15 минут</div>
                        </div>
                        <div class="warning">
                            Если вы не регистрировались в cysu, просто проигнорируйте это письмо.
                        </div>
                    </div>
                    <div class="footer">
                        <p>© 2025 cysu. Все права защищены.</p>
                        <p>Современная образовательная платформа</p>
                    </div>
                </div>
            </body>
            </html>
            """
            text_body = f"""
            Добро пожаловать в cysu!
            
            Для завершения регистрации введите следующий код подтверждения:
            
            {' '.join(verification_code)}
            
            Код действителен в течение 15 минут.
            
            Если вы не регистрировались в cysu, просто проигнорируйте это письмо.
            
            © 2025 cysu. Все права защищены.
            """
            msg = Message(
                subject=subject, recipients=[user_email], html=html_body, body=text_body
            )
            mail.send(msg)
            logger.info(
                f"Verification email sent successfully to {user_email} with code: {' '.join(verification_code)}"
            )
            return True
        except Exception as e:
            logger.error(f"Failed to send verification email to {user_email}: {str(e)}")
            return False

    @staticmethod
    def send_resend_verification_email(user_email: str, verification_code: str) -> bool:
        """
        Отправляет повторный email с кодом подтверждения

        Args:
            user_email: Email пользователя
            verification_code: Код подтверждения

        Returns:
            bool: True если email отправлен успешно, False в противном случае
        """
        try:
            subject = "Новый код подтверждения - cysu"
            current_app.logger.info(f"Sending resend verification email to {user_email} with code: '{verification_code}' (type: {type(verification_code)}, length: {len(verification_code)})")
            html_body = f"""
            <!DOCTYPE html>
            <html lang="ru">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Новый код подтверждения - cysu</title>
                <style>
                    body {{
                        margin: 0;
                        padding: 20px;
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                        background-color: #0e0e0f;
                        color: #ffffff;
                    }}
                    .container {{
                        max-width: 600px;
                        margin: 0 auto;
                        background: #1a1a1a;
                        border-radius: 12px;
                        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
                        overflow: hidden;
                    }}
                    .header {{
                        background: linear-gradient(135deg, #28a745 0%, #218838 100%);
                        padding: 25px 30px;
                        text-align: center;
                        color: white;
                    }}
                    .header h1 {{
                        margin: 0;
                        font-size: 24px;
                        font-weight: 600;
                    }}
                    .header p {{
                        margin: 8px 0 0 0;
                        opacity: 0.9;
                        font-size: 14px;
                    }}
                    .content {{
                        padding: 40px 30px;
                        text-align: center;
                    }}
                    .verification-title {{
                        font-size: 22px;
                        font-weight: 600;
                        color: #ffffff;
                        margin-bottom: 10px;
                    }}
                    .verification-desc {{
                        color: #b0b0b0;
                        font-size: 16px;
                        margin-bottom: 30px;
                        line-height: 1.5;
                    }}
                    .code-container {{
                        background: linear-gradient(135deg, #2a2a2a 0%, #1a1a1a 100%);
                        border: 2px solid #3a3a3a;
                        border-radius: 12px;
                        padding: 30px;
                        margin: 20px 0;
                        display: inline-block;
                    }}
                    .verification-code {{
                        font-size: 36px;
                        font-weight: 700;
                        font-family: 'Courier New', monospace;
                        color: #ffffff;
                        letter-spacing: 8px;
                        margin: 0;
                    }}
                    .code-info {{
                        color: #b0b0b0;
                        font-size: 14px;
                        margin-top: 15px;
                    }}
                    .footer {{
                        background: #0e0e0f;
                        padding: 30px;
                        text-align: center;
                        border-top: 1px solid #2a2a2a;
                    }}
                    .footer p {{
                        margin: 5px 0;
                        color: #b0b0b0;
                        font-size: 14px;
                    }}
                    .warning {{
                        background: rgba(255, 193, 7, 0.1);
                        border: 1px solid #ffc107;
                        border-radius: 8px;
                        padding: 15px;
                        margin: 20px 0;
                        color: #ffc107;
                        font-size: 14px;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>Новый код подтверждения</h1>
                        <p>Мы отправили вам новый код для завершения регистрации</p>
                    </div>
                    <div class="content">
                        <div class="verification-title">Подтвердите ваш email!</div>
                        <div class="verification-desc">
                            Для завершения регистрации введите новый код<br>
                            подтверждения ниже
                        </div>
                        <div class="code-container">
                            <div class="verification-code">{' '.join(verification_code)}</div>
                            <div class="code-info">Код действителен в течение 15 минут</div>
                        </div>
                        <div class="warning">
                            Если вы не регистрировались в cysu, просто проигнорируйте это письмо.
                        </div>
                    </div>
                    <div class="footer">
                        <p>© 2025 cysu. Все права защищены.</p>
                        <p>Современная образовательная платформа</p>
                    </div>
                </div>
            </body>
            </html>
            """
            text_body = f"""
            Новый код подтверждения - cysu
            
            Для завершения регистрации введите следующий код подтверждения:
            
            {' '.join(verification_code)}
            
            Код действителен в течение 15 минут.
            
            Если вы не регистрировались в cysu, просто проигнорируйте это письмо.
            
            © 2025 cysu. Все права защищены.
            """
            msg = Message(
                subject=subject, recipients=[user_email], html=html_body, body=text_body
            )
            mail.send(msg)
            logger.info(
                f"Resend verification email sent successfully to {user_email} with code: {' '.join(verification_code)}"
            )
            return True
        except Exception as e:
            logger.error(
                f"Failed to send resend verification email to {user_email}: {str(e)}"
            )
            return False

    @staticmethod
    def send_password_reset_email(user_email: str, reset_code: str) -> bool:
        """
        Отправляет email с кодом восстановления пароля

        Args:
            user_email: Email пользователя
            reset_code: Код восстановления пароля

        Returns:
            bool: True если email отправлен успешно, False в противном случае
        """
        try:
            subject = "Восстановление пароля - cysu"
            current_app.logger.info(f"Sending password reset email to {user_email} with code: '{reset_code}' (type: {type(reset_code)}, length: {len(reset_code)})")
            
            html_body = f"""
            <!DOCTYPE html>
            <html lang="ru">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Восстановление пароля - cysu</title>
                <style>
                    body {{
                        margin: 0;
                        padding: 20px;
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                        background-color: #0e0e0f;
                        color: #ffffff;
                    }}
                    .container {{
                        max-width: 600px;
                        margin: 0 auto;
                        background: #1a1a1a;
                        border-radius: 12px;
                        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
                        overflow: hidden;
                    }}
                    .header {{
                        background: linear-gradient(135deg, #dc3545 0%, #c82333 100%);
                        padding: 25px 30px;
                        text-align: center;
                        color: white;
                    }}
                    .header h1 {{
                        margin: 0;
                        font-size: 24px;
                        font-weight: 600;
                    }}
                    .header p {{
                        margin: 8px 0 0 0;
                        opacity: 0.9;
                        font-size: 14px;
                    }}
                    .content {{
                        padding: 40px 30px;
                        text-align: center;
                    }}
                    .verification-title {{
                        font-size: 22px;
                        font-weight: 600;
                        color: #ffffff;
                        margin-bottom: 10px;
                    }}
                    .verification-desc {{
                        color: #b0b0b0;
                        font-size: 16px;
                        margin-bottom: 30px;
                        line-height: 1.5;
                    }}
                    .code-container {{
                        background: linear-gradient(135deg, #2a2a2a 0%, #1a1a1a 100%);
                        border: 2px solid #3a3a3a;
                        border-radius: 12px;
                        padding: 30px;
                        margin: 20px 0;
                        display: inline-block;
                    }}
                    .verification-code {{
                        font-size: 36px;
                        font-weight: 700;
                        font-family: 'Courier New', monospace;
                        color: #ffffff;
                        letter-spacing: 8px;
                        margin: 0;
                    }}
                    .code-info {{
                        color: #b0b0b0;
                        font-size: 14px;
                        margin-top: 15px;
                    }}
                    .footer {{
                        background: #0e0e0f;
                        padding: 30px;
                        text-align: center;
                        border-top: 1px solid #2a2a2a;
                    }}
                    .footer p {{
                        margin: 5px 0;
                        color: #b0b0b0;
                        font-size: 14px;
                    }}
                    .warning {{
                        background: rgba(220, 53, 69, 0.1);
                        border: 1px solid #dc3545;
                        border-radius: 8px;
                        padding: 15px;
                        margin: 20px 0;
                        color: #dc3545;
                        font-size: 14px;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>Восстановление пароля</h1>
                        <p>Безопасное восстановление доступа к вашему аккаунту</p>
                    </div>
                    <div class="content">
                        <div class="verification-title">Создайте новый пароль</div>
                        <div class="verification-desc">
                            Введите код ниже для создания нового пароля
                        </div>
                        <div class="code-container">
                            <div class="verification-code">{' '.join(reset_code)}</div>
                            <div class="code-info">Код действителен в течение 15 минут</div>
                        </div>
                        <div class="warning">
                            Если вы не запрашивали восстановление пароля, просто проигнорируйте это письмо.
                        </div>
                    </div>
                    <div class="footer">
                        <p>© 2025 cysu. Все права защищены.</p>
                        <p>Современная образовательная платформа</p>
                    </div>
                </div>
            </body>
            </html>
            """
            text_body = f"""
            Восстановление пароля - cysu
            
            Вы запросили восстановление пароля. Введите следующий код для создания нового пароля:
            
            {' '.join(reset_code)}
            
            Код действителен в течение 15 минут.
            
            Важно: Если вы не запрашивали восстановление пароля, просто проигнорируйте это письмо.
            
            © 2025 cysu. Все права защищены.
            """
            msg = Message(
                subject=subject, recipients=[user_email], html=html_body, body=text_body
            )
            mail.send(msg)
            logger.info(
                f"Password reset email sent successfully to {user_email} with code: {' '.join(reset_code)}"
            )
            return True
        except Exception as e:
            logger.error(
                f"Failed to send password reset email to {user_email}: {str(e)}"
            )
            return False
