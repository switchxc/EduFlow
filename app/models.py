from . import db
from flask_login import UserMixin
from datetime import datetime, timedelta
import secrets
from typing import Optional

class Group(db.Model):
    """Модель для хранения групп пользователей"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Связи
    users = db.relationship('User', backref='group', lazy=True)
    subjects = db.relationship('SubjectGroup', backref='group', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self) -> str:
        return f'<Group {self.name}>'

class SubjectGroup(db.Model):
    """Модель для связи предметов с группами (многие-ко-многим)"""
    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Уникальность комбинации
    __table_args__ = (db.UniqueConstraint('subject_id', 'group_id'),)
    
    def __repr__(self) -> str:
        return f'<SubjectGroup subject_id={self.subject_id} group_id={self.group_id}>'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_subscribed = db.Column(db.Boolean, default=False)
    subscription_expires = db.Column(db.DateTime)
    is_manual_subscription = db.Column(db.Boolean, default=False)  # Подписка выдана вручную администратором
    is_verified = db.Column(db.Boolean, default=False)  # Подтверждение email
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=True)  # Новая связь с группой
    submissions = db.relationship('Submission', backref='user', lazy=True, cascade='all, delete-orphan')
    payments = db.relationship('Payment', backref='user', lazy=True, cascade='all, delete-orphan')
    tickets = db.relationship('Ticket', foreign_keys='Ticket.user_id', backref='user', lazy=True, cascade='all, delete-orphan')
    notifications = db.relationship('Notification', backref='user', lazy=True, cascade='all, delete-orphan')

class EmailVerification(db.Model):
    """Модель для хранения кодов подтверждения email"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # Может быть NULL для временных кодов
    email = db.Column(db.String(120), nullable=True)  # Email для временных кодов
    code = db.Column(db.String(6), nullable=False)  # 6-значный код
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    is_used = db.Column(db.Boolean, default=False)
    
    # Связь с пользователем
    user = db.relationship('User', backref=db.backref('email_verifications', cascade='all, delete-orphan'))
    
    def __repr__(self) -> str:
        return f'<EmailVerification {self.id}: {self.user.email if self.user else "Unknown"}>'
    
    @classmethod
    def generate_code(cls) -> str:
        """Генерирует 6-значный код подтверждения"""
        import logging
        logger = logging.getLogger(__name__)
        
        code = ''.join(secrets.choice('0123456789') for _ in range(6))
        logger.info(f"Generated verification code: '{code}' (type: {type(code)}, length: {len(code)})")
        return code
    
    @classmethod
    def create_verification(cls, user_id: int = None, email: str = None, expires_in_minutes: int = 15) -> 'EmailVerification':
        """Создает новый код подтверждения для пользователя или email"""
        code = cls.generate_code()
        expires_at = datetime.utcnow() + timedelta(minutes=expires_in_minutes)
        
        return cls(
            user_id=user_id,
            email=email,
            code=code,
            expires_at=expires_at
        )


class PasswordReset(db.Model):
    """Модель для хранения кодов восстановления пароля"""
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)  # Email пользователя
    code = db.Column(db.String(8), nullable=False)  # 8-символьный код
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    is_used = db.Column(db.Boolean, default=False)
    
    def __repr__(self) -> str:
        return f'<PasswordReset {self.id}: {self.email}>'
    
    @classmethod
    def generate_code(cls) -> str:
        """Генерирует 8-символьный код восстановления"""
        import string
        import logging
        logger = logging.getLogger(__name__)
        
        code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
        logger.info(f"Generated password reset code: '{code}' (type: {type(code)}, length: {len(code)})")
        return code
    
    @classmethod
    def create_reset(cls, email: str, expires_in_minutes: int = 15) -> 'PasswordReset':
        """Создает новый код восстановления для email"""
        code = cls.generate_code()
        expires_at = datetime.utcnow() + timedelta(minutes=expires_in_minutes)
        
        return cls(
            email=email,
            code=code,
            expires_at=expires_at
        )

class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    materials = db.relationship('Material', backref='subject', lazy=True)
    # Связь с группами через SubjectGroup
    groups = db.relationship('SubjectGroup', backref='subject', lazy=True, cascade='all, delete-orphan')

class Material(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    file = db.Column(db.String(255))
    type = db.Column(db.String(20))  # 'lecture' or 'assignment'
    solution_file = db.Column(db.String(255))  # Готовое задание (только для практик)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    submissions = db.relationship('Submission', backref='material', lazy=True, cascade="all, delete-orphan")

class Submission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    material_id = db.Column(db.Integer, db.ForeignKey('material.id'), nullable=False)
    file = db.Column(db.String(255))
    text = db.Column(db.Text)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)

class Payment(db.Model):
    """Модель для хранения информации о платежах"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    yookassa_payment_id = db.Column(db.String(255), unique=True, nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(3), default='RUB')
    status = db.Column(db.String(20), default='pending')  # pending, succeeded, canceled, failed
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self) -> str:
        return f'<Payment {self.yookassa_payment_id}: {self.status}>'

class ChatMessage(db.Model):
    """Модель для хранения сообщений чата"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    file_path = db.Column(db.String(255))  # Путь к загруженному файлу
    file_name = db.Column(db.String(255))  # Оригинальное имя файла
    file_type = db.Column(db.String(50))   # Тип файла (image, document, etc.)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Связь с пользователем
    user = db.relationship('User', backref=db.backref('chat_messages', cascade='all, delete-orphan'))
    
    def __repr__(self) -> str:
        return f'<ChatMessage {self.id}: {self.user.username if self.user else "Unknown"}>' 

class Ticket(db.Model):
    """Модель для хранения тикетов поддержки"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subject = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, accepted, rejected, closed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    admin_response = db.Column(db.Text)  # Ответ администратора
    admin_response_at = db.Column(db.DateTime)
    admin_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # ID администратора, который обработал тикет
    user_response = db.Column(db.Text)  # Ответ пользователя на ответ администратора
    user_response_at = db.Column(db.DateTime)  # Время ответа пользователя
    
    # Связь с файлами тикета
    files = db.relationship('TicketFile', backref='ticket', lazy=True, cascade='all, delete-orphan')
    
    # Связь с администратором
    admin = db.relationship('User', foreign_keys=[admin_id], backref='administered_tickets')
    
    def __repr__(self) -> str:
        return f'<Ticket {self.id}: {self.subject}>'

class TicketFile(db.Model):
    """Модель для хранения файлов, прикрепленных к тикетам"""
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('ticket.id'), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.Integer)  # Размер файла в байтах
    file_type = db.Column(db.String(50))  # MIME тип файла
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self) -> str:
        return f'<TicketFile {self.id}: {self.file_name}>'

class TicketMessage(db.Model):
    """Модель для хранения сообщений в тикетах"""
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('ticket.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_admin = db.Column(db.Boolean, default=False)  # True если сообщение от администратора
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Связи
    ticket = db.relationship('Ticket', backref='messages')
    user = db.relationship('User', backref='ticket_messages')
    
    def __repr__(self) -> str:
        return f'<TicketMessage {self.id}: {"Admin" if self.is_admin else "User"}>'

class Notification(db.Model):
    """Модель для хранения уведомлений пользователей"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(20), default='info')  # info, success, warning, error
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    link = db.Column(db.String(255))  # Ссылка для перехода
    
    def __repr__(self) -> str:
        return f'<Notification {self.id}: {self.title}>' 


class ShortLink(db.Model):
    """Модель для хранения сокращённых ссылок"""
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(16), unique=True, nullable=False, index=True)
    original_url = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    clicks = db.Column(db.Integer, default=0, nullable=False)

    def __repr__(self) -> str:
        return f'<ShortLink {self.code} -> {self.original_url}>'

    @staticmethod
    def generate_code(length: int = 3) -> str:
        """Генерирует короткий код длиной length"""
        alphabet = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        return ''.join(secrets.choice(alphabet) for _ in range(length))

    @classmethod
    def create_unique(cls, original_url: str, max_tries: int = 5) -> 'ShortLink':
        """Создаёт уникальную запись с новым кодом"""
        for _ in range(max_tries):
            code = cls.generate_code()
            if not cls.query.filter_by(code=code).first():
                link = cls(code=code, original_url=original_url)
                db.session.add(link)
                db.session.commit()
                return link
        # Если по каким-то причинам код не удалось сгенерировать
        # увеличиваем длину и пробуем ещё раз
        code = cls.generate_code(8)
        link = cls(code=code, original_url=original_url)
        db.session.add(link)
        db.session.commit()
        return link


class ShortLinkRule(db.Model):
    """Политика ограничения для короткой ссылки (время/количество кликов)."""
    id = db.Column(db.Integer, primary_key=True)
    short_link_id = db.Column(db.Integer, db.ForeignKey('short_link.id'), nullable=False, unique=True)
    expires_at = db.Column(db.DateTime, nullable=True)
    max_clicks = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Связь
    short_link = db.relationship('ShortLink', backref=db.backref('rule', uselist=False, cascade='all, delete-orphan'))

    def __repr__(self) -> str:
        return f'<ShortLinkRule link_id={self.short_link_id} expires_at={self.expires_at} max_clicks={self.max_clicks}>'