from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    request,
    current_app,
    jsonify,
    session,
)
from flask_login import login_user, logout_user, login_required, current_user
from .models import (
    User,
    Material,
    Submission,
    Subject,
    Payment,
    ChatMessage,
    EmailVerification,
    PasswordReset,
    Ticket,
    TicketFile,
    TicketMessage,
    Notification,
    ShortLink,
    ShortLinkRule,
    Group,
    SubjectGroup,
)
from .forms import (
    LoginForm,
    RegistrationForm,
    AdminUserForm,
    MaterialForm,
    SubjectForm,
    PaymentStatusForm,
    EmailVerificationForm,
    PasswordResetRequestForm,
    PasswordResetForm,
    ShortenForm,
    GroupForm,
    SubjectGroupForm,
)
from . import db, login_manager
from .utils.payment_service import YooKassaService
from .utils.email_service import EmailService
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
import random
import string
from sqlalchemy.orm import joinedload
from datetime import datetime, timedelta
import json
import re
from .services.shortlink_service import (
    create_short_link,
    normalize_url,
    parse_ttl,
    parse_max_clicks,
    check_access,
    register_click,
    reset_clicks,
    update_rule,
    delete_short_link,
)

bp = Blueprint("main", __name__)


@bp.app_context_processor
def inject_json_parser():
    """Добавляет функцию для парсинга JSON в шаблоны"""

    def parse_json(json_string):
        try:
            return json.loads(json_string)
        except (json.JSONDecodeError, TypeError):
            return []

    return dict(parse_json=parse_json)


@bp.app_context_processor
def inject_timestamp():
    """Добавляет timestamp для предотвращения кэширования CSS/JS"""
    from time import time
    return dict(timestamp=int(time()))


@bp.app_context_processor
def inject_moment():
    """Добавляет функцию moment для форматирования дат"""
    from datetime import datetime
    import locale
    
    # Устанавливаем русскую локаль для дат
    try:
        locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
    except:
        try:
            locale.setlocale(locale.LC_TIME, 'ru_RU')
        except:
            pass  # Если русская локаль недоступна, используем системную
    
    def moment():
        return datetime.now()
    
    def format_date_russian():
        """Форматирует дату на русском языке с fallback"""
        now = datetime.now()
        try:
            return now.strftime('%d %B %Y')
        except:
            # Fallback на английский формат
            months_en = ['January', 'February', 'March', 'April', 'May', 'June',
                        'July', 'August', 'September', 'October', 'November', 'December']
            return f"{now.day} {months_en[now.month-1]} {now.year}"
    
    return dict(moment=moment, format_date_russian=format_date_russian)


@login_manager.user_loader
def load_user(user_id):
    try:
        return User.query.get(int(user_id))
    except Exception as e:
        current_app.logger.error(f"Error loading user {user_id}: {e}")
        return None


@bp.route("/", methods=["GET", "POST"])
def index():
    form = None
    is_subscribed = False

    if current_user.is_authenticated:
        # Проверяем подписку пользователя
        try:
            payment_service = YooKassaService()
            is_subscribed = payment_service.check_user_subscription(current_user)
        except Exception as e:
            current_app.logger.error(f"Error checking subscription in index: {e}")
            is_subscribed = False

        if current_user.is_admin:
            form = SubjectForm()
            if form.validate_on_submit():
                subject = Subject(
                    title=form.title.data,
                    description=form.description.data,
                    created_by=current_user.id,
                )
                db.session.add(subject)
                db.session.commit()
                flash("Предмет добавлен")
                return redirect(url_for("main.index"))

    try:
        if current_user.is_authenticated and not current_user.is_admin:
            # Для обычных пользователей показываем только предметы их группы
            if current_user.group:
                subjects = Subject.query.join(SubjectGroup).filter(
                    SubjectGroup.group_id == current_user.group.id
                ).all()
            else:
                subjects = []
                flash("У вас не назначена группа. Обратитесь к администратору.", "warning")
        else:
            # Для админов и неавторизованных пользователей показываем все предметы
            subjects = Subject.query.all()
    except Exception as e:
        current_app.logger.error(f"Error querying subjects: {e}")
        subjects = []
        flash("Ошибка загрузки предметов. Попробуйте обновить страницу.", "error")
    
    return render_template(
        "index.html", subjects=subjects, form=form, is_subscribed=is_subscribed
    )


# Инициализация сервиса платежей будет происходить внутри функций


@bp.route("/subscription", methods=["GET", "POST"])
@login_required
def subscription():
    """Страница оформления подписки с "Умным платежом" ЮKassa"""
    current_app.logger.info(
        f"Запрос страницы подписки для пользователя: {current_user.username}"
    )
    current_app.logger.info(f"Все параметры запроса: {dict(request.args)}")
    current_app.logger.info(f"URL запроса: {request.url}")
    current_app.logger.info(f"Метод запроса: {request.method}")

    try:
        prices = current_app.config["SUBSCRIPTION_PRICES"]
    except Exception as e:
        current_app.logger.error(f"Error getting subscription prices: {e}")
        prices = {}
        flash("Ошибка загрузки цен подписки.", "error")

    # Проверяем, есть ли параметры для создания платежа
    period = request.args.get("period")
    amount = request.args.get("amount")

    # Если параметры есть, создаем платеж
    if period and amount:
        try:
            current_app.logger.info(
                f"Создание платежа - period: {period}, amount: {amount}"
            )

            # Создаем сервис платежей
            payment_service = YooKassaService()
            current_app.logger.info("Сервис платежей создан")

            # Создаем "Умный платеж" с выбранной ценой
            return_url = url_for("main.payment_success", _external=True)
            current_app.logger.info(f"Return URL: {return_url}")
            
            # Добавляем параметр для отслеживания источника
            return_url += "?source=yookassa"
            current_app.logger.info(f"Return URL с параметром: {return_url}")

            current_app.logger.info(
                f"Передаем цену в payment_service: {amount} (тип: {type(amount)})"
            )
            payment_info = payment_service.create_smart_payment(
                current_user, return_url, float(amount)
            )
            current_app.logger.info(
                f"Платеж создан: {payment_info['payment_id']} с суммой: {payment_info.get('amount')}"
            )

            # Если есть URL для оплаты, перенаправляем на страницу ЮKassa
            if payment_info.get("payment_url"):
                current_app.logger.info(
                    f"Перенаправление на страницу оплаты: {payment_info['payment_url']}"
                )
                return redirect(payment_info["payment_url"])
            else:
                # Если URL нет, показываем ошибку
                current_app.logger.error("URL для оплаты не получен от ЮKassa")
                flash("Ошибка создания платежа. Попробуйте позже.", "error")
                return render_template(
                    "payment/subscription.html",
                    payment_url=None,
                    payment_id=None,
                    prices=prices,
                )

        except Exception as e:
            current_app.logger.error(f"Ошибка при создании платежа: {str(e)}")
            import traceback

            current_app.logger.error(f"Traceback: {traceback.format_exc()}")
            flash("Произошла ошибка при создании платежа. Попробуйте позже.", "error")
            return render_template(
                "payment/subscription.html", payment_url=None, prices=prices
            )

    # Если параметров нет, показываем страницу выбора подписки
    current_app.logger.info("Показываем страницу выбора подписки")
    return render_template(
        "payment/subscription.html", payment_url=None, payment_id=None, prices=prices
    )


@bp.route("/payment/webhook", methods=["POST"])
def payment_webhook():
    """Обработка webhook'ов от ЮKassa"""
    try:
        # Получаем данные от ЮKassa
        data = request.get_json()
        current_app.logger.info(f"Получен webhook от ЮKassa: {data}")

        if not data:
            current_app.logger.error("Пустые данные в webhook")
            return "OK", 200

        # Проверяем тип события
        event = data.get("event")
        payment_data = data.get("object", {})
        payment_id = payment_data.get("id")

        if not payment_id:
            current_app.logger.error("Payment ID не найден в webhook")
            return "OK", 200

        current_app.logger.info(
            f"Обработка webhook: event={event}, payment_id={payment_id}"
        )

        # Находим платеж в базе данных
        payment_record = Payment.query.filter_by(yookassa_payment_id=payment_id).first()

        if not payment_record:
            current_app.logger.error(f"Платеж {payment_id} не найден в базе данных")
            return "OK", 200

        # Обновляем статус платежа
        payment_record.status = payment_data.get("status", "pending")
        payment_record.updated_at = datetime.utcnow()

        # Если платеж успешен, активируем подписку
        if payment_data.get("status") == "succeeded" and payment_data.get(
            "paid", False
        ):
            current_app.logger.info(f"Платеж {payment_id} успешен, активируем подписку")

            user = User.query.get(payment_record.user_id)
            if user:
                user.is_subscribed = True

                # Определяем период подписки по сумме платежа
                payment_service = YooKassaService()
                subscription_days = payment_service._get_subscription_days(
                    payment_record.amount
                )
                user.subscription_expires = datetime.utcnow() + timedelta(
                    days=subscription_days
                )

                current_app.logger.info(
                    f"Подписка активирована для пользователя {user.username} на {subscription_days} дней"
                )
        
        # Если платеж отменен, сбрасываем подписку пользователя
        elif payment_data.get("status") == "canceled":
            current_app.logger.info(f"Платеж {payment_id} отменен, сбрасываем подписку")
            
            user = User.query.get(payment_record.user_id)
            if user:
                user.is_subscribed = False
                user.subscription_expires = None
                current_app.logger.info(
                    f"Подписка сброшена для пользователя {user.username}"
                )

        db.session.commit()
        current_app.logger.info(
            f"Webhook обработан успешно: payment_id={payment_id}, status={payment_data.get('status')}"
        )

        return "OK", 200

    except Exception as e:
        current_app.logger.error(f"Ошибка обработки webhook: {str(e)}")
        return "OK", 200  # Всегда возвращаем 200, чтобы ЮKassa не повторял запрос


@bp.route("/payment/success")
@login_required
def payment_success():
    """Обработка успешного платежа от ЮKassa"""
    current_app.logger.info(f"=== ВХОД В PAYMENT_SUCCESS ===")
    current_app.logger.info(f"Все параметры запроса: {dict(request.args)}")
    current_app.logger.info(f"Полный URL: {request.url}")
    
    payment_id = request.args.get("payment_id")
    source = request.args.get("source")
    
    current_app.logger.info(f"Обработка платежа: {payment_id}, источник: {source}")
    current_app.logger.info(f"Пользователь: {current_user.username}")
    
    # Если это возврат от ЮKassa, проверяем статус более тщательно
    if source == "yookassa":
        current_app.logger.info("Обнаружен возврат от ЮKassa - проверяем статус платежа")
        
        # Создаем сервис платежей для проверки статуса
        payment_service = YooKassaService()
        
        # Проверяем статус платежа
        if payment_id:
            payment_status = payment_service.get_payment_status(payment_id)
            current_app.logger.info(f"Статус платежа от ЮKassa: {payment_status}")
            
            # Если платеж отменен, перенаправляем на страницу отмены
            if payment_status.get("status") == "canceled":
                current_app.logger.info("Платеж отменен - перенаправляем на страницу отмены")
                return redirect(url_for("main.payment_cancel", payment_id=payment_id))
            
            # Если платеж в обработке, показываем страницу ожидания
            elif payment_status.get("status") == "pending":
                current_app.logger.info("Платеж в обработке - показываем страницу ожидания")
                flash("Платеж в обработке. Подписка будет активирована после подтверждения оплаты.", "info")
                return render_template("payment/pending.html")
    
    # Проверяем, не была ли отмена платежа через параметр cancel
    if request.args.get("cancel") == "true":
        current_app.logger.info("Обнаружена отмена платежа через параметр cancel")
        return redirect(url_for("main.payment_cancel", payment_id=payment_id))

    # Если payment_id не передан, ищем последний платеж пользователя
    if not payment_id:
        current_app.logger.info(
            "Payment ID не найден в параметрах, ищем последний платеж пользователя"
        )
        try:
            payment_record = (
                Payment.query.filter_by(user_id=current_user.id)
                .order_by(Payment.created_at.desc())
                .first()
            )

            if payment_record:
                payment_id = payment_record.yookassa_payment_id
                current_app.logger.info(f"Найден последний платеж: {payment_id}")
            else:
                current_app.logger.error("Платежи пользователя не найдены")
                # Попробуем найти платеж по email пользователя в ЮKassa
                current_app.logger.info("Попытка найти платеж по email пользователя")
                flash("Платеж не найден. Попробуйте оформить подписку снова.", "warning")
                return redirect(url_for("main.subscription"))
        except Exception as e:
            current_app.logger.error(f"Error searching for user payments: {e}")
            flash("Ошибка поиска платежей. Попробуйте оформить подписку снова.", "error")
            return redirect(url_for("main.subscription"))

    # Создаем сервис платежей
    payment_service = YooKassaService()
    current_app.logger.info("Обработка платежа")

    # Проверяем, что платеж существует и принадлежит текущему пользователю
    try:
        payment_record = Payment.query.filter_by(
            yookassa_payment_id=payment_id, user_id=current_user.id
        ).first()

        if not payment_record:
            current_app.logger.error(
                f"Платеж {payment_id} не найден для пользователя {current_user.id}"
            )
            # Попробуем найти платеж только по ID (возможно, проблема с user_id)
            payment_record = Payment.query.filter_by(yookassa_payment_id=payment_id).first()

            if payment_record:
                current_app.logger.warning(
                    f"Платеж найден, но принадлежит другому пользователю: {payment_record.user_id}"
                )
                flash("Платеж не принадлежит вам.", "error")
                return redirect(url_for("main.index"))
            else:
                current_app.logger.error(f"Платеж {payment_id} не найден в базе данных")
                flash("Платеж не найден. Попробуйте оформить подписку снова.", "warning")
                return redirect(url_for("main.subscription"))
    except Exception as e:
        current_app.logger.error(f"Error searching for payment {payment_id}: {e}")
        flash("Ошибка поиска платежа. Попробуйте позже.", "error")
        return redirect(url_for("main.index"))

    current_app.logger.info(f"Платеж найден: {payment_record.status}")

    # Проверяем статус платежа в ЮKassa
    payment_status = payment_service.get_payment_status(payment_id)
    current_app.logger.info(f"Статус платежа от ЮKassa: {payment_status}")

    if "error" in payment_status:
        current_app.logger.error(f"Ошибка получения статуса: {payment_status['error']}")

        # Если это режим симуляции или ошибка связана с API, обрабатываем платеж локально
        if payment_service.simulation_mode or "HTTP 401" in str(
            payment_status["error"]
        ):
            current_app.logger.info(
                "Обработка платежа в режиме симуляции или при ошибке API"
            )
            if payment_service.process_successful_payment(payment_id):
                current_app.logger.info("Подписка успешно активирована")
                flash("Платеж успешно обработан! Подписка активирована.", "success")
            else:
                current_app.logger.error("Ошибка при активации подписки")
                flash(
                    "Произошла ошибка при активации подписки. Обратитесь в поддержку.",
                    "error",
                )
        else:
            flash(
                f"Ошибка при проверке платежа: {payment_status['error']}. Обратитесь в поддержку.",
                "error",
            )
    elif payment_status.get("status") == "succeeded":
        current_app.logger.info("Платеж успешен, активируем подписку")
        # Обрабатываем успешный платеж
        if payment_service.process_successful_payment(payment_id):
            current_app.logger.info("Подписка успешно активирована")
            flash(
                "Подписка успешно оформлена! Теперь у вас есть доступ ко всем материалам.",
                "success",
            )
        else:
            current_app.logger.error("Ошибка при активации подписки")
            flash(
                "Произошла ошибка при активации подписки. Обратитесь в поддержку.",
                "error",
            )
    elif payment_status.get("status") == "pending":
        current_app.logger.info("Платеж в обработке")
        flash(
            "Платеж в обработке. Подписка будет активирована после подтверждения оплаты.",
            "info",
        )
    elif payment_status.get("status") == "canceled":
        current_app.logger.info("Платеж отменен - перенаправляем на страницу отмены")
        return redirect(url_for("main.payment_cancel", payment_id=payment_id))
    elif payment_status.get("status") == "waiting_for_capture":
        current_app.logger.info("Платеж ожидает подтверждения")
        flash(
            "Платеж ожидает подтверждения. Подписка будет активирована после подтверждения.",
            "info",
        )
    else:
        current_app.logger.warning(
            f"Неизвестный статус: {payment_status.get('status')}"
        )
        flash(
            f"Статус платежа: {payment_status.get('status', 'неизвестен')}. Обратитесь в поддержку.",
            "error",
        )

    return render_template("payment/success.html")





@bp.route("/payment/cancel")
@login_required
def payment_cancel():
    """Обработка отмены платежа"""
    payment_id = request.args.get("payment_id")
    
    current_app.logger.info(f"Отмена платежа: payment_id={payment_id}, пользователь={current_user.username}")
    
    if payment_id:
        # Находим платеж в базе данных и обновляем его статус
        try:
            payment_record = Payment.query.filter_by(yookassa_payment_id=payment_id).first()
            if payment_record:
                payment_record.status = "canceled"
                payment_record.updated_at = datetime.utcnow()
                db.session.commit()
                current_app.logger.info(f"Статус платежа {payment_id} обновлен на 'canceled'")
            else:
                current_app.logger.warning(f"Платеж {payment_id} не найден в базе данных")
        except Exception as e:
            current_app.logger.error(f"Ошибка при обновлении статуса платежа: {e}")
        
        flash("Платеж был отменен. Попробуйте оформить подписку снова.", "warning")
    else:
        current_app.logger.info("Отмена платежа без payment_id")
        flash("Информация о платеже не найдена.", "error")

    return render_template("payment/cancel.html")


@bp.route("/payment/status", methods=["GET", "POST"])
@login_required
def payment_status():
    """Проверка статуса платежа"""
    form = PaymentStatusForm()

    if form.validate_on_submit():
        payment_id = form.payment_id.data
        try:
            # Создаем сервис платежей
            payment_service = YooKassaService()
            status = payment_service.get_payment_status(payment_id)

            if "error" in status:
                flash(f"Ошибка при получении статуса: {status['error']}", "error")
            else:
                flash(f"Статус платежа: {status['status']}", "info")
        except Exception as e:
            current_app.logger.error(f"Error checking payment status: {e}")
            flash("Ошибка при проверке статуса платежа.", "error")

    return render_template("payment/payment_status.html", form=form)


@bp.route("/api/payment/status/<payment_id>")
@login_required
def api_payment_status(payment_id):
    """API для проверки статуса платежа"""
    try:
        payment_service = YooKassaService()
        status = payment_service.get_payment_status(payment_id)
        return jsonify(status)
    except Exception as e:
        current_app.logger.error(f"Error in api_payment_status: {e}")
        return jsonify({"error": "Internal server error"}), 500


@bp.route("/profile")
@login_required
def profile():
    """Страница профиля пользователя"""
    try:
        # Создаем сервис платежей
        payment_service = YooKassaService()
        # Проверяем актуальность подписки
        is_subscribed = payment_service.check_user_subscription(current_user)
    except Exception as e:
        current_app.logger.error(f"Error checking subscription in profile: {e}")
        is_subscribed = False
        flash("Ошибка проверки подписки.", "error")

    return render_template(
        "profile.html", user=current_user, is_subscribed=is_subscribed
    )


@bp.route("/subject/<int:subject_id>", methods=["GET", "POST"])
def subject_detail(subject_id):
    try:
        subject = Subject.query.get_or_404(subject_id)
    except Exception as e:
        current_app.logger.error(f"Error loading subject {subject_id}: {e}")
        flash("Ошибка загрузки предмета.", "error")
        return redirect(url_for("main.index"))

    # Проверяем подписку для аутентифицированных пользователей
    if current_user.is_authenticated:
        try:
            # Создаем сервис платежей
            payment_service = YooKassaService()
            # Проверяем подписку пользователя
            if not payment_service.check_user_subscription(current_user):
                flash("Для доступа к предметам необходима активная подписка.", "warning")
                return redirect(url_for("main.subscription"))
            
            # Проверяем доступ к предмету по группе (если пользователь не админ)
            if not current_user.is_admin:
                # Проверяем, есть ли у пользователя группа
                if current_user.group:
                    # Проверяем, доступен ли предмет для группы пользователя
                    subject_group = SubjectGroup.query.filter_by(
                        subject_id=subject.id, 
                        group_id=current_user.group.id
                    ).first()
                    if not subject_group:
                        flash("У вас нет доступа к этому предмету.", "error")
                        return redirect(url_for("main.index"))
                else:
                    flash("У вас не назначена группа. Обратитесь к администратору.", "error")
                    return redirect(url_for("main.index"))
        except Exception as e:
            current_app.logger.error(f"Error checking subscription in subject_detail: {e}")
            flash("Ошибка проверки подписки.", "error")
            return redirect(url_for("main.index"))

    try:
        lectures = Material.query.filter_by(subject_id=subject.id, type="lecture").all()
        assignments = (
            Material.query.options(joinedload(Material.submissions))
            .filter_by(subject_id=subject.id, type="assignment")
            .all()
        )
    except Exception as e:
        current_app.logger.error(f"Error loading materials for subject {subject.id}: {e}")
        lectures = []
        assignments = []
        flash("Ошибка загрузки материалов.", "error")
    form = None
    user_submissions = {}
    if current_user.is_authenticated:
        try:
            for material in assignments:
                for sub in material.submissions:
                    if str(sub.user_id) == str(current_user.id) and sub.file:
                        user_submissions[material.id] = sub
                        break
        except Exception as e:
            current_app.logger.error(f"Error loading user submissions: {e}")
            user_submissions = {}
    if current_user.is_authenticated and current_user.is_admin:
        form = MaterialForm()
        form.subject_id.choices = [(subject.id, subject.title)]
        form.subject_id.data = subject.id
        if form.validate_on_submit():
            filename = None
            solution_filename = None

            # Импортируем менеджер файлов
            from .utils.file_storage import FileStorageManager

            # Получаем информацию о предмете
            subject = Subject.query.get_or_404(subject_id)

            if form.file.data:
                file = form.file.data
                original_filename = secure_filename(file.filename)

                # Создаем путь для файла материала
                full_path, relative_path = FileStorageManager.get_material_upload_path(
                    subject.id, original_filename
                )

                # Сохраняем файл
                if FileStorageManager.save_file(file, full_path):
                    filename = relative_path

            if form.type.data == "assignment" and form.solution_file.data:
                solution_file = form.solution_file.data
                original_solution_filename = secure_filename(solution_file.filename)

                # Создаем путь для файла решения
                full_solution_path, relative_solution_path = (
                    FileStorageManager.get_material_upload_path(
                        subject.id,
                        f"solution_{original_solution_filename}",
                    )
                )

                # Сохраняем файл решения
                if FileStorageManager.save_file(solution_file, full_solution_path):
                    solution_filename = relative_solution_path
            material = Material(
                title=form.title.data,
                description=form.description.data,
                file=filename,
                type=form.type.data,
                solution_file=solution_filename,
                created_by=current_user.id,
                subject_id=subject.id,
            )
            db.session.add(material)
            db.session.commit()
            flash("Материал добавлен")
            return redirect(url_for("main.subject_detail", subject_id=subject.id))
    return render_template(
        "subjects/subject_detail.html",
        subject=subject,
        lectures=lectures,
        assignments=assignments,
        form=form,
        user_submissions=user_submissions,
    )


@bp.route("/subject/<int:subject_id>/delete", methods=["POST"])
@login_required
def delete_subject(subject_id):
    if not current_user.is_admin:
        flash("Доступ запрещён")
        return redirect(url_for("main.index"))
    subject = Subject.query.get_or_404(subject_id)
    # Удаляем все материалы этого предмета
    for material in subject.materials:
        db.session.delete(material)
    db.session.delete(subject)
    db.session.commit()
    flash("Предмет удалён")
    return redirect(url_for("main.index"))


# Удаляю личный кабинет
# @bp.route('/account')
# @login_required
# def account():
#    submissions = Submission.query.filter_by(user_id=current_user.id).all()
#    return render_template('account.html', submissions=submissions)


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            return redirect(url_for("main.index"))
        flash("Неверное имя пользователя или пароль")
    return render_template("auth/login.html", form=form)


@bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    form = RegistrationForm()

    current_app.logger.info(f"Регистрация - метод: {request.method}")

    if form.validate_on_submit():
        current_app.logger.info(
            f"Форма валидна, проверяем данные: {form.username.data}, {form.email.data}"
        )
        try:
            # Проверяем, что пользователь с таким username или email не существует
            existing_user = User.query.filter(
                (User.username == form.username.data) | (User.email == form.email.data)
            ).first()

            if existing_user:
                if existing_user.username == form.username.data:
                    flash(
                        f'Пользователь с именем "{form.username.data}" уже существует',
                        "error",
                    )
                else:
                    flash(
                        f'Пользователь с email "{form.email.data}" уже существует',
                        "error",
                    )
                return render_template("auth/register.html", form=form)

            # Сохраняем данные регистрации в сессии
            session["pending_registration"] = {
                "username": form.username.data,
                "email": form.email.data,
                "password": form.password.data,
                "group_id": form.group_id.data,
            }

            # Создаем временный код подтверждения
            verification = EmailVerification.create_verification(email=form.email.data)
            db.session.add(verification)
            db.session.commit()

            current_app.logger.info(
                f"Verification code created for pending registration ({form.email.data}): {' '.join(verification.code)} (type: {type(verification.code)}, length: {len(verification.code)})"
            )

            # Отправляем email с кодом
            if EmailService.send_verification_email(form.email.data, verification.code):
                flash("Проверьте вашу почту для подтверждения email.")
                session["pending_verification_id"] = verification.id
                return redirect(url_for("main.email_verification"))
            else:
                flash("Ошибка отправки email. Попробуйте еще раз.")
                db.session.delete(verification)
                db.session.commit()

        except Exception as e:
            current_app.logger.error(f"Ошибка при обработке регистрации: {str(e)}")
            db.session.rollback()
            flash("Ошибка при обработке регистрации. Попробуйте еще раз.")
    else:
        current_app.logger.warning(f"Форма не валидна: {form.errors}")
        for field, errors in form.errors.items():
            for error in errors:
                current_app.logger.warning(f"Ошибка в поле {field}: {error}")

    return render_template("auth/register.html", form=form)


@bp.route("/email/verification", methods=["GET", "POST"])
def email_verification():
    """Страница подтверждения email"""
    verification_id = session.get("pending_verification_id")
    pending_registration = session.get("pending_registration")

    if not verification_id or not pending_registration:
        flash("Сначала зарегистрируйтесь.")
        return redirect(url_for("main.register"))

    form = EmailVerificationForm()

    if form.validate_on_submit():
        # Проверяем код подтверждения
        verification = EmailVerification.query.filter_by(
            id=verification_id, code=form.code.data, is_used=False
        ).first()

        if verification and verification.expires_at > datetime.utcnow():
            # Код верный и не истек - создаем пользователя
            try:
                hashed_password = generate_password_hash(
                    pending_registration["password"]
                )
                user = User(
                    username=pending_registration["username"],
                    email=pending_registration["email"],
                    password=hashed_password,
                    is_verified=True,  # Пользователь подтвержден
                    group_id=pending_registration.get("group_id") if pending_registration.get("group_id") else None,
                )
                db.session.add(user)
                db.session.commit()

                # Обновляем verification с правильным user_id и очищаем email
                verification.user_id = user.id
                verification.email = None
                verification.is_used = True
                db.session.commit()

                current_app.logger.info(
                    f"User created and email verified: {user.username} ({user.email}) with code: {' '.join(form.code.data)}"
                )

                # Очищаем сессию
                session.pop("pending_verification_id", None)
                session.pop("pending_registration", None)

                flash(
                    "Регистрация успешно завершена! Теперь вы можете войти в систему."
                )
                return redirect(url_for("main.login"))

            except Exception as e:
                current_app.logger.error(
                    f"Ошибка при создании пользователя после подтверждения: {str(e)}"
                )
                db.session.rollback()
                flash("Ошибка при завершении регистрации. Попробуйте еще раз.")
                return redirect(url_for("main.register"))
        else:
            flash("Неверный код или код истек. Попробуйте еще раз.")

    return render_template(
        "auth/email_verification.html",
        form=form,
        user_email=pending_registration["email"],
    )


@bp.route("/email/resend", methods=["GET", "POST"])
def resend_verification():
    """Повторная отправка кода подтверждения"""
    verification_id = session.get("pending_verification_id")
    pending_registration = session.get("pending_registration")

    if not verification_id or not pending_registration:
        flash("Сначала зарегистрируйтесь.")
        return redirect(url_for("main.register"))

    try:
        # Удаляем старый код подтверждения
        EmailVerification.query.filter_by(id=verification_id, is_used=False).delete()

        # Создаем новый код подтверждения
        verification = EmailVerification.create_verification(
            email=pending_registration["email"]
        )
        db.session.add(verification)
        db.session.commit()

        current_app.logger.info(
            f"New verification code created for pending registration ({pending_registration['email']}): {' '.join(verification.code)}"
        )

        # Обновляем ID в сессии
        session["pending_verification_id"] = verification.id

        # Отправляем email с новым кодом
        if EmailService.send_resend_verification_email(
            pending_registration["email"], verification.code
        ):
            flash("Новый код подтверждения отправлен на ваш email.")
        else:
            flash("Ошибка отправки email. Попробуйте еще раз.")

    except Exception as e:
        current_app.logger.error(f"Ошибка при повторной отправке кода: {str(e)}")
        db.session.rollback()
        flash("Ошибка при отправке кода. Попробуйте еще раз.")

    return redirect(url_for("main.email_verification"))


@bp.route("/password/reset", methods=["GET", "POST"])
def password_reset_request():
    """Страница запроса восстановления пароля"""
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    form = PasswordResetRequestForm()
    if form.validate_on_submit():
        email = form.email.data
        user = User.query.filter_by(email=email).first()

        if user:
            # Удаляем старые коды восстановления для этого email
            PasswordReset.query.filter_by(email=email, is_used=False).delete()

            # Создаем новый код восстановления
            reset = PasswordReset.create_reset(email)
            db.session.add(reset)
            db.session.commit()

            current_app.logger.info(
                f"Password reset code created for {email}: {' '.join(reset.code)}"
            )

            # Отправляем email с кодом
            if EmailService.send_password_reset_email(email, reset.code):
                flash(
                    "Код восстановления отправлен на вашу почту. Проверьте email и введите код.",
                    "info",
                )
                return redirect(url_for("main.password_reset_confirm"))
            else:
                flash("Ошибка отправки email. Попробуйте позже.", "error")
        else:
            # Для безопасности не показываем, что email не найден
            flash(
                "Если указанный email зарегистрирован, код восстановления будет отправлен.",
                "info",
            )
            return redirect(url_for("main.password_reset_confirm"))

    return render_template("auth/password_reset_request.html", form=form)


@bp.route("/password/reset/confirm", methods=["GET", "POST"])
def password_reset_confirm():
    """Страница подтверждения кода и смены пароля"""
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    form = PasswordResetForm()
    if form.validate_on_submit():
        code = form.code.data
        new_password = form.new_password.data

        # Ищем активный код восстановления
        reset = (
            PasswordReset.query.filter_by(code=code, is_used=False)
            .filter(PasswordReset.expires_at > datetime.utcnow())
            .first()
        )

        if reset:
            # Находим пользователя по email
            user = User.query.filter_by(email=reset.email).first()
            if user:
                # Обновляем пароль
                user.password = generate_password_hash(new_password)
                reset.is_used = True
                db.session.commit()

                current_app.logger.info(
                    f"Password reset successful for user {user.username} ({user.email})"
                )
                flash(
                    "Пароль успешно изменен! Теперь вы можете войти с новым паролем.",
                    "success",
                )
                return redirect(url_for("main.login"))
            else:
                flash("Ошибка: пользователь не найден.", "error")
        else:
            flash("Неверный код или код истек. Попробуйте еще раз.", "error")

    return render_template("auth/password_reset_confirm.html", form=form)


@bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("main.index"))


@bp.route("/privacy")
def privacy():
    """Страница политики конфиденциальности"""
    return render_template("static/privacy.html")


@bp.route("/terms")
def terms():
    """Страница условий предоставления услуг"""
    return render_template("static/terms.html")


@bp.route("/s", methods=["GET", "POST"])
@login_required
def shorten_page():
    """Скрытая страница сокращения ссылок. Доступ только по прямой ссылке."""
    form = ShortenForm()
    short_url = None
    if form.validate_on_submit():
        link = create_short_link(
            original_url=form.url.data,
            ttl=form.ttl.data,
            max_clicks=form.max_clicks.data,
        )
        short_url = url_for('main.resolve_shortlink', code=link.code, _external=True)
        flash("Ссылка сокращена", "success")
    return render_template("static/shorten.html", form=form, short_url=short_url)


@bp.route("/l/<string:code>")
def resolve_shortlink(code: str):
    """Редирект по короткому коду"""
    current_app.logger.info(f"shortlink: resolve attempt code={code}")
    link = ShortLink.query.filter_by(code=code).first()
    if not link:
        current_app.logger.info(f"shortlink: not found code={code}")
        return redirect(url_for('main.not_found'))
    # Проверяем правила
    allowed, reason = check_access(link)
    if not allowed:
        current_app.logger.info(f"shortlink: blocked reason={reason}")
        return redirect(url_for('main.shortlink_expired'))
    register_click(link)
    current_app.logger.info(f"shortlink: redirecting to original clicks_now={link.clicks}")
    return redirect(link.original_url)


@bp.route("/l/expired")
def shortlink_expired():
    return render_template("static/shortlink_expired.html")


@bp.route("/404")
def not_found():
    return render_template("static/404.html"), 404


@bp.app_errorhandler(404)
def handle_404(error):
    return redirect(url_for('main.not_found'))


@bp.route("/material/<int:material_id>")
@login_required
def material_detail(material_id):
    material = Material.query.get_or_404(material_id)

    # Создаем сервис платежей
    payment_service = YooKassaService()
    # Проверяем подписку пользователя
    if not payment_service.check_user_subscription(current_user):
        flash("Для доступа к материалам необходима активная подписка.", "warning")
        return redirect(url_for("main.subscription"))

    return render_template("subjects/material_detail.html", material=material)


@bp.route("/material/<int:material_id>/add_solution", methods=["POST"])
@login_required
def add_solution_file(material_id):
    if not current_user.is_admin:
        flash("Доступ запрещён")
        return redirect(url_for("main.index"))
    material = Material.query.get_or_404(material_id)
    file = request.files.get("solution_file")
    if file:
        # Импортируем менеджер файлов
        from .utils.file_storage import FileStorageManager

        # Получаем информацию о предмете
        subject = material.subject
        original_filename = secure_filename(file.filename)

        # Создаем путь для файла решения
        full_path, relative_path = FileStorageManager.get_material_upload_path(
            subject.id, f"admin_solution_{original_filename}"
        )

        # Сохраняем файл
        if FileStorageManager.save_file(file, full_path):
            material.solution_file = relative_path
            db.session.commit()
            flash("Готовая практика добавлена")
    return redirect(url_for("main.subject_detail", subject_id=material.subject_id))


@bp.route("/material/<int:material_id>/submit_solution", methods=["POST"])
@login_required
def submit_solution(material_id):
    material = Material.query.get_or_404(material_id)

    # Создаем сервис платежей и проверяем подписку
    payment_service = YooKassaService()
    if not payment_service.check_user_subscription(current_user):
        flash("Для загрузки решений необходима активная подписка.", "warning")
        return redirect(url_for("main.subscription"))

    if material.type != "assignment":
        flash("Можно загружать решение только для практик")
        return redirect(url_for("main.subject_detail", subject_id=material.subject_id))
    file = request.files.get("solution_file")
    if file:
        # Импортируем менеджер файлов
        from .utils.file_storage import FileStorageManager

        # Получаем информацию о предмете
        subject = material.subject
        original_filename = secure_filename(file.filename)

        # Создаем путь для файла решения пользователя
        full_path, relative_path = FileStorageManager.get_subject_upload_path(
            subject.id, current_user.id, f"user_solution_{original_filename}"
        )

        # Сохраняем файл
        if FileStorageManager.save_file(file, full_path):
            # Обновить или создать Submission
            from .models import Submission

            submission = Submission.query.filter_by(
                user_id=current_user.id, material_id=material.id
            ).first()
            if not submission:
                submission = Submission(
                    user_id=current_user.id, material_id=material.id
                )
                db.session.add(submission)
            submission.file = relative_path
            db.session.commit()
            flash("Решение загружено")
    return redirect(url_for("main.subject_detail", subject_id=material.subject_id))


@bp.route("/material/<int:material_id>/delete", methods=["POST"])
@login_required
def delete_material(material_id):
    if not current_user.is_admin:
        flash("Доступ запрещён")
        return redirect(url_for("main.index"))
    material = Material.query.get_or_404(material_id)
    subject_id = material.subject_id
    db.session.delete(material)
    db.session.commit()
    flash("Материал удалён")
    return redirect(url_for("main.subject_detail", subject_id=subject_id))


# Удаляем дублирующуюся функцию admin_subjects

# Удаляю admin_materials
# @bp.route('/admin/materials', methods=['GET', 'POST'])
# @login_required
# def admin_materials():
#    if not current_user.is_admin:
#        flash('Доступ запрещён')
#        return redirect(url_for('main.index'))
#    form = MaterialForm()
#    form.subject_id.choices = [(s.id, s.title) for s in Subject.query.all()]
#    if form.validate_on_submit():
#        filename = None
#        solution_filename = None
#        if form.file.data:
#            filename = form.file.data.filename
#            upload_folder = current_app.config['UPLOAD_FOLDER']
#            os.makedirs(upload_folder, exist_ok=True)
#            form.file.data.save(os.path.join(upload_folder, filename))
#        if form.type.data == 'assignment' and form.solution_file.data:
#            solution_filename = form.solution_file.data.filename
#            upload_folder = current_app.config['UPLOAD_FOLDER']
#            os.makedirs(upload_folder, exist_ok=True)
#            form.solution_file.data.save(os.path.join(upload_folder, solution_filename))
#        material = Material(
#            title=form.title.data,
#            description=form.description.data,
#            file=filename,
#            type=form.type.data,
#            solution_file=solution_filename,
#            created_by=current_user.id,
#            subject_id=form.subject_id.data
#        )
#        db.session.add(material)
#        db.session.commit()
#        flash('Материал добавлен')
#        return redirect(url_for('main.admin_materials'))
#    materials = Material.query.all()
#    return render_template('admin/materials.html', materials=materials, form=form)


@bp.route("/admin/users", methods=["GET", "POST"])
@login_required
def admin_users():
    """Админка для управления пользователями"""
    if not current_user.is_admin:
        flash("Доступ запрещён")
        return redirect(url_for("main.index"))

    form = AdminUserForm()
    password_map = {}
    message = ""

    # Диагностика формы
    current_app.logger.info(f"Форма создана: {form}")
    current_app.logger.info(
        f"CSRF токен: {form.csrf_token.current_token if form.csrf_token else 'Нет токена'}"
    )

    # Создание нового пользователя
    current_app.logger.info(f"Метод запроса: {request.method}")
    current_app.logger.info(f"Данные формы: {request.form}")
    current_app.logger.info(f"Значение submit: {request.form.get('submit')}")

    # Проверяем все возможные условия
    if request.method == "POST":
        current_app.logger.info("POST запрос получен")
        if request.form.get("submit") == "Зарегистрироваться":
            current_app.logger.info("Найдена кнопка 'Зарегистрироваться'")
        else:
            current_app.logger.info(
                f"Кнопка не найдена. Доступные поля: {list(request.form.keys())}"
            )

    if request.method == "POST" and request.form.get("submit") == "Зарегистрироваться":
        current_app.logger.info("Обрабатываем форму создания пользователя")
        current_app.logger.info("Проверяем валидацию формы")
        current_app.logger.info(f"Ошибки формы: {form.errors}")

        if form.validate_on_submit():
            current_app.logger.info(
                f"Админка - создание пользователя: {form.username.data}, {form.email.data}"
            )
            try:
                # Проверяем, что пользователь с таким username или email не существует
                existing_user = User.query.filter(
                    (User.username == form.username.data)
                    | (User.email == form.email.data)
                ).first()

                if existing_user:
                    if existing_user.username == form.username.data:
                        current_app.logger.warning(
                            f"Пользователь с именем {form.username.data} уже существует"
                        )
                        flash(
                            f'Пользователь с именем "{form.username.data}" уже существует',
                            "error",
                        )
                    else:
                        current_app.logger.warning(
                            f"Пользователь с email {form.email.data} уже существует"
                        )
                        flash(
                            f'Пользователь с email "{form.email.data}" уже существует',
                            "error",
                        )
                else:
                    current_app.logger.info(
                        f"Создаем нового пользователя: {form.username.data}"
                    )
                    user = User(
                        username=form.username.data,
                        email=form.email.data,
                        password=generate_password_hash(form.password.data),
                        is_admin=False,
                        is_subscribed=False,
                        group_id=form.group_id.data if form.group_id.data else None,
                    )
                    db.session.add(user)
                    db.session.commit()
                    current_app.logger.info(
                        f"Пользователь успешно создан с ID: {user.id}"
                    )
                    password_map[user.id] = form.password.data
                    flash(f"Пользователь {user.username} успешно создан")

            except Exception as e:
                current_app.logger.error(f"Ошибка создания пользователя: {str(e)}")
                import traceback

                current_app.logger.error(f"Traceback: {traceback.format_exc()}")
                db.session.rollback()
                flash("Ошибка при создании пользователя", "error")
        else:
            current_app.logger.warning(f"Форма админки не валидна: {form.errors}")
            for field, errors in form.errors.items():
                for error in errors:
                    current_app.logger.warning(f"Ошибка в поле {field}: {error}")

    # Сброс пароля пользователя
    if request.method == "POST" and request.form.get("reset_user_id"):
        try:
            user_id = int(request.form.get("reset_user_id"))
            user = User.query.get(user_id)
            if user:
                new_password = "".join(
                    random.choices(
                        string.ascii_letters + string.digits + "!@#$%^&*", k=10
                    )
                )
                user.password = generate_password_hash(new_password)
                db.session.commit()
                password_map[user.id] = new_password
                flash(f"Пароль для пользователя {user.username} сброшен")
            else:
                flash("Пользователь не найден", "error")
        except Exception as e:
            current_app.logger.error(f"Ошибка сброса пароля: {str(e)}")
            db.session.rollback()  # Откатываем транзакцию при ошибке
            flash("Ошибка при сбросе пароля", "error")

    # Удаление пользователя
    if request.method == "POST" and request.form.get("delete_user_id"):
        try:
            user_id = int(request.form.get("delete_user_id"))
            current_app.logger.info(f"Попытка удаления пользователя с ID: {user_id}")
            user = User.query.get(user_id)
            if user:
                current_app.logger.info(
                    f"Найден пользователь для удаления: {user.username} (ID: {user.id})"
                )
                if user.id == current_user.id:
                    flash("Нельзя удалить самого себя", "error")
                elif user.is_admin:
                    flash("Нельзя удалить администратора", "error")
                else:
                    username = user.username
                    current_app.logger.info(
                        f"Начинаем удаление пользователя {username} (ID: {user.id})"
                    )

                    # Удаляем все связанные данные пользователя
                    try:
                        # Удаляем уведомления
                        notifications_count = Notification.query.filter_by(
                            user_id=user.id
                        ).count()
                        Notification.query.filter_by(user_id=user.id).delete()
                        current_app.logger.info(
                            f"Удалено уведомлений: {notifications_count}"
                        )

                        # Удаляем сообщения тикетов
                        ticket_messages_count = TicketMessage.query.filter_by(
                            user_id=user.id
                        ).count()
                        TicketMessage.query.filter_by(user_id=user.id).delete()
                        current_app.logger.info(
                            f"Удалено сообщений тикетов: {ticket_messages_count}"
                        )

                        # Удаляем тикеты пользователя
                        tickets_count = Ticket.query.filter_by(user_id=user.id).count()
                        Ticket.query.filter_by(user_id=user.id).delete()
                        current_app.logger.info(f"Удалено тикетов: {tickets_count}")

                        # Удаляем коды подтверждения email
                        email_verifications_count = EmailVerification.query.filter_by(
                            user_id=user.id
                        ).count()
                        EmailVerification.query.filter_by(user_id=user.id).delete()
                        current_app.logger.info(
                            f"Удалено кодов подтверждения email: {email_verifications_count}"
                        )

                        # Удаляем платежи
                        payments_count = Payment.query.filter_by(
                            user_id=user.id
                        ).count()
                        Payment.query.filter_by(user_id=user.id).delete()
                        current_app.logger.info(f"Удалено платежей: {payments_count}")

                        # Удаляем решения
                        submissions_count = Submission.query.filter_by(
                            user_id=user.id
                        ).count()
                        Submission.query.filter_by(user_id=user.id).delete()
                        current_app.logger.info(f"Удалено решений: {submissions_count}")

                        # Удаляем сообщения чата
                        chat_messages_count = ChatMessage.query.filter_by(
                            user_id=user.id
                        ).count()
                        ChatMessage.query.filter_by(user_id=user.id).delete()
                        current_app.logger.info(
                            f"Удалено сообщений чата: {chat_messages_count}"
                        )

                        # Удаляем файлы пользователя с использованием FileStorageManager
                        from .utils.file_storage import FileStorageManager

                        if FileStorageManager.delete_user_files(user.id):
                            current_app.logger.info(
                                f"Файлы пользователя {user.id} успешно удалены"
                            )
                        else:
                            current_app.logger.warning(
                                f"Ошибка при удалении файлов пользователя {user.id}"
                            )

                        # Удаляем файлы тикетов
                        for ticket in Ticket.query.filter_by(user_id=user.id).all():
                            if FileStorageManager.delete_ticket_files(ticket.id):
                                current_app.logger.info(
                                    f"Файлы тикета {ticket.id} успешно удалены"
                                )
                            else:
                                current_app.logger.warning(
                                    f"Ошибка при удалении файлов тикета {ticket.id}"
                                )

                        # Удаляем самого пользователя
                        db.session.delete(user)
                        db.session.commit()
                        current_app.logger.info(
                            f"Пользователь {username} успешно удален"
                        )
                        flash(f"Пользователь {username} удалён")

                    except Exception as e:
                        current_app.logger.error(
                            f"Ошибка при удалении связанных данных пользователя {username}: {str(e)}"
                        )
                        import traceback

                        current_app.logger.error(f"Traceback: {traceback.format_exc()}")
                        db.session.rollback()
                        flash(f"Ошибка при удалении пользователя {username}", "error")
                        return redirect(url_for("main.admin_users"))
            else:
                flash("Пользователь не найден", "error")
        except Exception as e:
            current_app.logger.error(f"Ошибка удаления пользователя: {str(e)}")
            db.session.rollback()  # Откатываем транзакцию при ошибке
            flash("Ошибка при удалении пользователя", "error")

    # Изменение статуса администратора
    if request.method == "POST" and request.form.get("toggle_admin_id"):
        try:
            user_id = int(request.form.get("toggle_admin_id"))
            user = User.query.get(user_id)
            if user:
                if user.id == current_user.id:
                    flash(
                        "Нельзя изменить статус администратора для самого себя", "error"
                    )
                else:
                    user.is_admin = not user.is_admin
                    status = (
                        "назначен администратором"
                        if user.is_admin
                        else "снят с администратора"
                    )
                    db.session.commit()
                    flash(f"Пользователь {user.username} {status}")
            else:
                flash("Пользователь не найден", "error")
        except Exception as e:
            current_app.logger.error(
                f"Ошибка изменения статуса администратора: {str(e)}"
            )
            db.session.rollback()  # Откатываем транзакцию при ошибке
            flash("Ошибка при изменении статуса администратора", "error")

    # Изменение группы пользователя
    if request.method == "POST" and request.form.get("change_group_user_id"):
        try:
            user_id = int(request.form.get("change_group_user_id"))
            new_group_id = request.form.get("new_group_id")
            user = User.query.get(user_id)
            
            if user:
                if new_group_id:
                    group = Group.query.get(int(new_group_id))
                    if group:
                        user.group_id = group.id
                        flash(f"Пользователь {user.username} перемещен в группу '{group.name}'")
                    else:
                        flash("Группа не найдена", "error")
                        return redirect(url_for("main.admin_users"))
                else:
                    user.group_id = None
                    flash(f"Пользователь {user.username} убран из группы")
                
                db.session.commit()
            else:
                flash("Пользователь не найден", "error")
        except Exception as e:
            current_app.logger.error(f"Ошибка изменения группы пользователя: {str(e)}")
            db.session.rollback()
            flash("Ошибка при изменении группы пользователя", "error")

    # Выдача/отзыв подписки
    if request.method == "POST" and request.form.get("toggle_subscription_id"):
        try:
            user_id = int(request.form.get("toggle_subscription_id"))
            current_app.logger.info(
                f"Обрабатываем изменение подписки для пользователя ID: {user_id}"
            )
            user = User.query.get(user_id)
            if user:
                current_app.logger.info(
                    f"Пользователь найден: {user.username}, текущий статус подписки: {user.is_subscribed}"
                )
                if user.is_subscribed:
                    # Отзываем подписку
                    current_app.logger.info(
                        f"Отзываем подписку у пользователя {user.username}"
                    )
                    user.is_subscribed = False
                    user.subscription_expires = None
                    user.is_manual_subscription = (
                        False  # Сбрасываем флаг ручной подписки
                    )
                    status = "отозвана"
                else:
                    # Выдаем подписку на 30 дней
                    current_app.logger.info(
                        f"Выдаем подписку пользователю {user.username} на 30 дней"
                    )
                    user.is_subscribed = True
                    user.subscription_expires = datetime.utcnow() + timedelta(days=30)
                    user.is_manual_subscription = (
                        True  # Устанавливаем флаг ручной подписки
                    )
                    status = "выдана на 30 дней"

                db.session.commit()
                current_app.logger.info(
                    f"Подписка успешно изменена: {user.username} - {status}"
                )
                flash(f"Подписка для пользователя {user.username} {status}")
            else:
                current_app.logger.error(f"Пользователь с ID {user_id} не найден")
                flash("Пользователь не найден", "error")
        except Exception as e:
            current_app.logger.error(f"Ошибка изменения подписки: {str(e)}")
            import traceback

            current_app.logger.error(f"Traceback: {traceback.format_exc()}")
            db.session.rollback()  # Откатываем транзакцию при ошибке
            flash("Ошибка при изменении подписки", "error")

    # Управление короткими ссылками (создание)
    if request.method == "POST" and request.form.get("create_shortlink_url"):
        try:
            original_url = request.form.get("create_shortlink_url", "")
            ttl = request.form.get("create_shortlink_ttl", "") or ""
            max_clicks_val = request.form.get("create_shortlink_max_clicks", "") or ""

            link = create_short_link(original_url, ttl, max_clicks_val)
            flash("Короткая ссылка создана", "success")
        except Exception as e:
            current_app.logger.error(f"Ошибка создания короткой ссылки: {str(e)}")
            db.session.rollback()
            flash("Ошибка создания короткой ссылки", "error")

    # Управление короткими ссылками (сброс кликов)
    if request.method == "POST" and request.form.get("reset_clicks_shortlink_id"):
        try:
            sid = int(request.form.get("reset_clicks_shortlink_id"))
            link = ShortLink.query.get(sid)
            if link:
                reset_clicks(link)
                flash("Счётчик переходов сброшен", "success")
            else:
                flash("Ссылка не найдена", "error")
        except Exception as e:
            current_app.logger.error(f"Ошибка сброса кликов: {str(e)}")
            db.session.rollback()
            flash("Ошибка сброса кликов", "error")

    # Управление короткими ссылками (удаление)
    if request.method == "POST" and request.form.get("delete_shortlink_id"):
        try:
            sid = int(request.form.get("delete_shortlink_id"))
            link = ShortLink.query.get(sid)
            if link:
                delete_short_link(link)
                flash("Ссылка удалена", "success")
            else:
                flash("Ссылка не найдена", "error")
        except Exception as e:
            current_app.logger.error(f"Ошибка удаления короткой ссылки: {str(e)}")
            db.session.rollback()
            flash("Ошибка удаления короткой ссылки", "error")

    # Управление короткими ссылками (обновление правил)
    if request.method == "POST" and request.form.get("update_shortlink_id"):
        try:
            sid = int(request.form.get("update_shortlink_id"))
            ttl = (request.form.get("update_shortlink_ttl", "") or "").strip()
            max_clicks_val = (request.form.get("update_shortlink_max_clicks", "") or "").strip()
            link = ShortLink.query.get(sid)
            if not link:
                flash("Ссылка не найдена", "error")
            else:
                update_rule(link, ttl=ttl, max_clicks=max_clicks_val)
                flash("Правила ссылки обновлены", "success")
        except Exception as e:
            current_app.logger.error(f"Ошибка обновления правил короткой ссылки: {str(e)}")
            db.session.rollback()
            flash("Ошибка обновления правил короткой ссылки", "error")

    # Получаем все короткие ссылки
    try:
        short_links = ShortLink.query.order_by(ShortLink.created_at.desc()).all()
    except Exception as e:
        current_app.logger.error(f"Error loading short links: {e}")
        short_links = []
        flash("Ошибка загрузки коротких ссылок.", "error")

    # Получаем всех пользователей с информацией о подписке
    try:
        users = User.query.all()
    except Exception as e:
        current_app.logger.error(f"Error loading users: {e}")
        users = []
        flash("Ошибка загрузки пользователей.", "error")

    return render_template(
        "admin/users.html",
        users=users,
        form=form,
        password_map=password_map,
        message=message,
        short_links=short_links,
        groups=Group.query.all(),  # Добавляем группы для модальных окон
    )


@bp.route("/admin/groups", methods=["GET", "POST"])
@login_required
def admin_groups():
    """Админка для управления группами"""
    if not current_user.is_admin:
        flash("Доступ запрещён")
        return redirect(url_for("main.index"))

    # Проверяем CSRF токен для POST запросов
    if request.method == "POST":
        current_app.logger.info(f"POST запрос в admin_groups: {request.form}")
        current_app.logger.info(f"CSRF токен в запросе: {request.form.get('csrf_token', 'НЕ НАЙДЕН')}")
        
        # Проверяем, что CSRF токен присутствует
        if not request.form.get('csrf_token'):
            current_app.logger.error("CSRF токен отсутствует в запросе")
            flash("Ошибка безопасности: отсутствует CSRF токен", "error")
            return redirect(url_for("main.admin_groups"))

    form = GroupForm()
    message = ""

    if request.method == "POST":
        # Создание новой группы
        if request.form.get("submit") == "Сохранить":
            if form.validate_on_submit():
                try:
                    # Проверяем уникальность названия группы
                    existing_group = Group.query.filter_by(name=form.name.data).first()
                    if existing_group:
                        flash(f'Группа с названием "{form.name.data}" уже существует', "error")
                    else:
                        group = Group(
                            name=form.name.data,
                            description=form.description.data,
                            is_active=form.is_active.data
                        )
                        db.session.add(group)
                        db.session.commit()
                        flash(f"Группа '{group.name}' успешно создана")
                        # Очищаем форму
                        form.name.data = ""
                        form.description.data = ""
                        form.is_active.data = True
                except Exception as e:
                    current_app.logger.error(f"Ошибка создания группы: {str(e)}")
                    db.session.rollback()
                    flash("Ошибка при создании группы", "error")

        # Редактирование группы (inline)
        elif request.form.get("action") == "edit":
            try:
                current_app.logger.info(f"Редактирование группы: {request.form}")
                group_id = int(request.form.get("group_id"))
                group = Group.query.get(group_id)
                if group:
                    current_app.logger.info(f"Обновляем группу: {group.name} (ID: {group_id})")
                    current_app.logger.info(f"Новые данные: name='{request.form.get('name')}', description='{request.form.get('description')}', is_active='{request.form.get('is_active')}'")
                    
                    group.name = request.form.get("name")
                    group.description = request.form.get("description")
                    
                    # Обновляем статус активности группы
                    is_active_value = request.form.get("is_active")
                    if is_active_value is not None:
                        group.is_active = bool(int(is_active_value))
                        current_app.logger.info(f"Статус активности обновлен: {group.is_active}")
                    
                    db.session.commit()
                    
                    # Возвращаем JSON ответ для AJAX
                    if request.headers.get('Accept') == 'application/json':
                        return jsonify({
                            'success': True,
                            'message': f"Группа '{group.name}' успешно обновлена"
                        })
                    else:
                        flash(f"Группа '{group.name}' успешно обновлена")
                else:
                    if request.headers.get('Accept') == 'application/json':
                        return jsonify({
                            'success': False,
                            'error': 'Группа не найдена'
                        }), 404
                    else:
                        flash("Группа не найдена", "error")
            except Exception as e:
                current_app.logger.error(f"Ошибка редактирования группы: {str(e)}")
                db.session.rollback()
                if request.headers.get('Accept') == 'application/json':
                    return jsonify({
                        'success': False,
                        'error': f'Ошибка при редактировании группы: {str(e)}'
                    }), 500
                else:
                    flash("Ошибка при редактировании группы", "error")

        # Удаление группы (inline)
        elif request.form.get("action") == "delete":
            current_app.logger.info(f"Получен запрос на удаление группы: {request.form}")
            try:
                group_id = int(request.form.get("group_id"))
                current_app.logger.info(f"Попытка удаления группы с ID: {group_id}")
                
                group = Group.query.get(group_id)
                if group:
                    current_app.logger.info(f"Группа найдена: {group.name}")
                    if group.users:
                        current_app.logger.warning(f"Попытка удаления группы '{group.name}' с пользователями: {len(group.users)}")
                        if request.headers.get('Accept') == 'application/json':
                            return jsonify({
                                'success': False,
                                'error': f"Нельзя удалить группу '{group.name}' - в ней есть пользователи"
                            }), 400
                        else:
                            flash(f"Нельзя удалить группу '{group.name}' - в ней есть пользователи", "error")
                    else:
                        current_app.logger.info(f"Удаляем группу '{group.name}' (ID: {group_id})")
                        db.session.delete(group)
                        db.session.commit()
                        current_app.logger.info(f"Группа '{group.name}' успешно удалена")
                        if request.headers.get('Accept') == 'application/json':
                            return jsonify({
                                'success': True,
                                'message': f"Группа '{group.name}' успешно удалена"
                            })
                        else:
                            flash(f"Группа '{group.name}' успешно удалена")
                else:
                    current_app.logger.error(f"Группа с ID {group_id} не найдена")
                    if request.headers.get('Accept') == 'application/json':
                        return jsonify({
                            'success': False,
                            'error': 'Группа не найдена'
                        }), 404
                    else:
                        flash("Группа не найдена", "error")
            except Exception as e:
                current_app.logger.error(f"Ошибка удаления группы: {str(e)}")
                current_app.logger.error(f"Traceback: {e.__traceback__}")
                db.session.rollback()
                if request.headers.get('Accept') == 'application/json':
                    return jsonify({
                        'success': False,
                        'error': f'Ошибка при удалении группы: {str(e)}'
                    }), 500
                else:
                    flash("Ошибка при удалении группы", "error")

    # Получаем все группы
    try:
        groups = Group.query.order_by(Group.name).all()
    except Exception as e:
        current_app.logger.error(f"Error loading groups: {e}")
        groups = []
        flash("Ошибка загрузки групп.", "error")

    return render_template(
        "admin/groups.html",
        groups=groups,
        form=form,
        message=message,
    )


@bp.route("/admin/subject-groups", methods=["GET", "POST"])
@login_required
def admin_subject_groups():
    """Админка для управления предметами по группам"""
    if not current_user.is_admin:
        flash("Доступ запрещён")
        return redirect(url_for("main.index"))

    # Получаем все предметы с их группами
    try:
        subjects = Subject.query.options(joinedload(Subject.groups)).order_by(Subject.title).all()
        groups = Group.query.filter_by(is_active=True).order_by(Group.name).all()
    except Exception as e:
        current_app.logger.error(f"Error loading subjects or groups: {e}")
        subjects = []
        groups = []
        flash("Ошибка загрузки предметов или групп.", "error")

    # Создаем форму после получения данных
    form = SubjectGroupForm()
    # Заполняем форму актуальными данными
    form.populate_choices(subjects, groups)
    message = ""

    if request.method == "POST":
        # Назначение предмета группам
        if request.form.get("submit") == "Сохранить":
            if form.validate_on_submit():
                try:
                    subject_id = form.subject_id.data
                    group_ids = form.group_ids.data
                    
                    # Удаляем существующие связи для этого предмета
                    SubjectGroup.query.filter_by(subject_id=subject_id).delete()
                    
                    # Создаем новые связи
                    for group_id in group_ids:
                        subject_group = SubjectGroup(
                            subject_id=subject_id,
                            group_id=group_id
                        )
                        db.session.add(subject_group)
                    
                    db.session.commit()
                    flash(f"Предмет успешно назначен группам")
                    
                    # Очищаем форму
                    form.subject_id.data = 0
                    form.group_ids.data = []
                except Exception as e:
                    current_app.logger.error(f"Ошибка назначения предмета группам: {str(e)}")
                    db.session.rollback()
                    flash("Ошибка при назначении предмета группам", "error")

        # Редактирование групп предмета
        elif request.form.get("edit_subject_id"):
            try:
                subject_id = int(request.form.get("edit_subject_id"))
                group_ids = request.form.getlist("edit_group_ids")
                
                # Удаляем существующие связи для этого предмета
                SubjectGroup.query.filter_by(subject_id=subject_id).delete()
                
                # Создаем новые связи
                for group_id in group_ids:
                    if group_id:  # Проверяем, что group_id не пустой
                        subject_group = SubjectGroup(
                            subject_id=subject_id,
                            group_id=int(group_id)
                        )
                        db.session.add(subject_group)
                
                db.session.commit()
                flash(f"Группы предмета успешно обновлены")
            except Exception as e:
                current_app.logger.error(f"Ошибка обновления групп предмета: {str(e)}")
                db.session.rollback()
                flash("Ошибка при обновлении групп предмета", "error")

        # Удаление всех связей предмета с группами
        elif request.form.get("remove_all_groups"):
            try:
                subject_id = int(request.form.get("remove_all_groups"))
                subject = Subject.query.get(subject_id)
                if subject:
                    SubjectGroup.query.filter_by(subject_id=subject_id).delete()
                    db.session.commit()
                    flash(f"Предмет '{subject.title}' убран из всех групп")
                else:
                    flash("Предмет не найден", "error")
            except Exception as e:
                current_app.logger.error(f"Ошибка удаления связей предмета с группами: {str(e)}")
                db.session.rollback()
                flash("Ошибка при удалении связей предмета с группами", "error")

    return render_template(
        "admin/subject_groups.html",
        subjects=subjects,
        groups=groups,
        form=form,
        message=message,
    )


# Добавляю context_processor для передачи users и формы на все страницы
@bp.app_context_processor
def inject_admin_users():
    """
    Context processor для передачи списка пользователей в шаблоны.

    Возвращает:
        dict: Словарь с ключом 'users' для использования в шаблонах
    """
    try:
        users = (
            User.query.all()
            if current_user.is_authenticated and current_user.is_admin
            else []
        )
    except Exception as e:
        current_app.logger.error(f"Error in inject_admin_users: {e}")
        users = []
    return dict(users=users)


@bp.app_context_processor
def inject_subscription_status():
    """
    Context processor для передачи актуального статуса подписки в шаблоны.

    Возвращает:
        dict: Словарь с ключом 'is_subscribed' для использования в шаблонах
    """
    is_subscribed = False
    if current_user.is_authenticated:
        try:
            payment_service = YooKassaService()
            is_subscribed = payment_service.check_user_subscription(current_user)
        except Exception as e:
            current_app.logger.error(f"Error in inject_subscription_status: {e}")
            is_subscribed = False
    return dict(is_subscribed=is_subscribed)


@bp.route("/wiki")
def wiki():
    """
    Wiki-страница с документацией и руководствами.
    """
    return render_template("static/wiki.html")

# Чат-система
@bp.route("/chat/messages")
@login_required
def get_chat_messages():
    """Получение последних 150 сообщений чата"""
    try:
        messages = (
            ChatMessage.query.order_by(ChatMessage.created_at.desc()).limit(150).all()
        )
        messages.reverse()  # Возвращаем в хронологическом порядке

        messages_data = []
        for msg in messages:
            messages_data.append(
                {
                    "id": msg.id,
                    "user_id": msg.user_id,
                    "username": msg.user.username,
                    "message": msg.message,
                    "file_path": msg.file_path,
                    "file_name": msg.file_name,
                    "file_type": msg.file_type,
                    "created_at": msg.created_at.strftime("%H:%M"),
                    "is_own": msg.user_id == current_user.id,
                }
            )

        return jsonify({"success": True, "messages": messages_data})
    except Exception as e:
        current_app.logger.error(f"Ошибка получения сообщений чата: {str(e)}")
        return jsonify({"success": False, "error": "Ошибка получения сообщений"})


@bp.route("/chat/send", methods=["POST"])
@login_required
def send_chat_message():
    """Отправка сообщения в чат"""
    current_app.logger.info("=== НАЧАЛО ОТПРАВКИ СООБЩЕНИЯ ===")
    current_app.logger.info(
        f"Попытка отправки сообщения от пользователя: {current_user.username}"
    )
    current_app.logger.info(f"Данные формы: {request.form}")
    current_app.logger.info(f"Файлы: {request.files}")
    current_app.logger.info(f"Метод запроса: {request.method}")
    current_app.logger.info(f"URL: {request.url}")

    try:
        message = request.form.get("message", "").strip()
        file = request.files.get("file")

        current_app.logger.info(
            f"Сообщение: '{message}', Файл: {file.filename if file else 'Нет'}"
        )

        if not message and not file:
            current_app.logger.warning("Пустое сообщение и нет файла")
            return jsonify(
                {"success": False, "error": "Сообщение или файл обязательны"}
            )

        chat_message = ChatMessage(user_id=current_user.id, message=message)

        # Обработка загруженного файла
        if file and file.filename:
            # Проверяем тип файла
            allowed_extensions = {
                "png",
                "jpg",
                "jpeg",
                "gif",
                "pdf",
                "doc",
                "docx",
                "txt",
                "zip",
                "rar",
            }
            file_extension = (
                file.filename.rsplit(".", 1)[1].lower() if "." in file.filename else ""
            )

            if file_extension not in allowed_extensions:
                return jsonify(
                    {"success": False, "error": "Неподдерживаемый тип файла"}
                )

            # Проверяем размер файла (максимум 10MB)
            if len(file.read()) > 10 * 1024 * 1024:
                return jsonify(
                    {"success": False, "error": "Файл слишком большой (максимум 10MB)"}
                )

            file.seek(0)  # Возвращаем указатель в начало

            # Сохраняем файл
            from werkzeug.utils import secure_filename

            filename = secure_filename(file.filename)
            # Импортируем менеджер файлов
            from .utils.file_storage import FileStorageManager

            # Создаем путь для файла чата
            full_path, relative_path = FileStorageManager.get_chat_file_path(
                current_user.id, filename
            )

            # Сохраняем файл
            if FileStorageManager.save_file(file, full_path):
                # Определяем тип файла
                file_type = FileStorageManager.get_file_type(filename)

                chat_message.file_path = relative_path
                chat_message.file_name = filename
                chat_message.file_type = file_type

        db.session.add(chat_message)
        db.session.commit()

        # Возвращаем данные нового сообщения
        current_app.logger.info(f"Сообщение успешно сохранено с ID: {chat_message.id}")

        response_data = {
            "success": True,
            "message": {
                "id": chat_message.id,
                "user_id": chat_message.user_id,
                "username": current_user.username,
                "message": chat_message.message,
                "file_path": chat_message.file_path,
                "file_name": chat_message.file_name,
                "file_type": chat_message.file_type,
                "created_at": chat_message.created_at.strftime("%H:%M"),
                "is_own": True,
            },
        }

        current_app.logger.info("=== УСПЕШНОЕ ЗАВЕРШЕНИЕ ОТПРАВКИ ===")
        return jsonify(response_data)

    except Exception as e:
        current_app.logger.error("=== ОШИБКА ОТПРАВКИ СООБЩЕНИЯ ===")
        current_app.logger.error(f"Ошибка отправки сообщения в чат: {str(e)}")
        import traceback

        current_app.logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({"success": False, "error": "Ошибка отправки сообщения"})


# ==================== СИСТЕМА ТИКЕТОВ ====================


@bp.route("/tickets", methods=["GET", "POST"])
@login_required
def tickets():
    """Страница списка тикетов для администраторов"""
    if not current_user.is_admin:
        flash("Доступ запрещен", "error")
        return redirect(url_for("main.index"))

    # Получаем все тикеты с информацией о пользователях
    tickets_list = (
        Ticket.query.join(User, Ticket.user_id == User.id)
        .order_by(Ticket.created_at.desc())
        .all()
    )

    return render_template("tickets/tickets.html", tickets=tickets_list)


@bp.route("/tickets/<int:ticket_id>")
@login_required
def ticket_detail(ticket_id: int):
    """Детальная страница тикета для администраторов"""
    if not current_user.is_admin:
        flash("Доступ запрещен", "error")
        return redirect(url_for("main.index"))

    ticket = Ticket.query.get_or_404(ticket_id)
    return render_template("tickets/ticket_detail.html", ticket=ticket)


@bp.route("/my-tickets/<int:ticket_id>")
@login_required
def user_ticket_detail(ticket_id: int):
    """Детальная страница тикета для пользователей"""
    ticket = Ticket.query.get_or_404(ticket_id)

    # Проверяем, что тикет принадлежит текущему пользователю
    if ticket.user_id != current_user.id:
        flash("Доступ запрещен", "error")
        return redirect(url_for("main.index"))

    return render_template("tickets/user_ticket_detail.html", ticket=ticket)


@bp.route("/tickets/<int:ticket_id>/accept", methods=["POST"])
@login_required
def accept_ticket(ticket_id: int):
    """Принятие тикета администратором"""
    if not current_user.is_admin:
        return jsonify({"success": False, "error": "Доступ запрещен"})

    ticket = Ticket.query.get_or_404(ticket_id)
    ticket.status = "accepted"
    ticket.admin_id = current_user.id
    ticket.updated_at = datetime.utcnow()

    db.session.commit()

    flash("Тикет принят", "success")
    return redirect(url_for("main.ticket_detail", ticket_id=ticket_id))


@bp.route("/tickets/<int:ticket_id>/reject", methods=["POST"])
@login_required
def reject_ticket(ticket_id: int):
    """Отклонение тикета администратором"""
    if not current_user.is_admin:
        return jsonify({"success": False, "error": "Доступ запрещен"})

    ticket = Ticket.query.get_or_404(ticket_id)
    ticket.status = "rejected"
    ticket.admin_id = current_user.id
    ticket.updated_at = datetime.utcnow()

    db.session.commit()

    flash("Тикет отклонен", "success")
    return redirect(url_for("main.tickets"))


@bp.route("/tickets/<int:ticket_id>/close", methods=["POST"])
@login_required
def close_ticket(ticket_id: int):
    """Закрытие тикета администратором"""
    if not current_user.is_admin:
        return jsonify({"success": False, "error": "Доступ запрещен"})

    ticket = Ticket.query.get_or_404(ticket_id)
    ticket.status = "closed"
    ticket.admin_id = current_user.id
    ticket.updated_at = datetime.utcnow()

    db.session.commit()

    flash("Тикет закрыт", "success")
    return redirect(url_for("main.tickets"))


@bp.route("/tickets/<int:ticket_id>/respond", methods=["POST"])
@login_required
def respond_to_ticket(ticket_id: int):
    """Ответ администратора на тикет"""
    if not current_user.is_admin:
        return jsonify({"success": False, "error": "Доступ запрещен"})

    ticket = Ticket.query.get_or_404(ticket_id)
    response_text = request.form.get("response", "").strip()

    if not response_text:
        flash("Введите текст ответа", "error")
        return redirect(url_for("main.ticket_detail", ticket_id=ticket_id))

    # Создаем новое сообщение администратора
    admin_message = TicketMessage(
        ticket_id=ticket.id,
        user_id=current_user.id,
        message=response_text,
        is_admin=True,
    )

    db.session.add(admin_message)

    # Обновляем время последнего ответа администратора
    ticket.admin_response_at = datetime.utcnow()
    ticket.admin_id = current_user.id
    ticket.updated_at = datetime.utcnow()

    # Создаем уведомление для пользователя только если тикет не закрыт
    if ticket.status != "closed":
        notification = Notification(
            user_id=ticket.user_id,
            title="Ответ на тикет",
            message=f'Администратор ответил на ваш тикет "{ticket.subject}"',
            type="info",
            link=url_for("main.user_ticket_detail", ticket_id=ticket.id),
        )

        db.session.add(notification)
        db.session.commit()

    flash("Ответ отправлен", "success")
    return redirect(url_for("main.ticket_detail", ticket_id=ticket_id))


@bp.route("/tickets/<int:ticket_id>/upload_file", methods=["POST"])
@login_required
def upload_ticket_file(ticket_id: int):
    """Загрузка файла к тикету"""
    try:
        ticket = Ticket.query.get_or_404(ticket_id)

        # Проверяем права доступа
        if not current_user.is_admin and ticket.user_id != current_user.id:
            return jsonify({"success": False, "error": "Доступ запрещен"})

        # Проверяем статус тикета
        if ticket.status == "closed":
            return jsonify(
                {"success": False, "error": "Нельзя загружать файлы в закрытый тикет"}
            )

        file = request.files.get("file")
        if not file or not file.filename:
            return jsonify({"success": False, "error": "Файл не выбран"})

        from .utils.file_storage import FileStorageManager

        # Проверяем размер файла
        if not FileStorageManager.validate_file_size(file):
            return jsonify(
                {"success": False, "error": "Файл слишком большой (максимум 10MB)"}
            )

        # Проверяем тип файла
        if not FileStorageManager.is_allowed_file(file.filename):
            return jsonify({"success": False, "error": "Неподдерживаемый тип файла"})

        # Получаем пути для сохранения
        full_path, relative_path = FileStorageManager.get_ticket_file_path(
            ticket_id, file.filename
        )

        # Сохраняем файл
        if FileStorageManager.save_file(file, full_path):
            # Создаем запись о файле
            ticket_file = TicketFile(
                ticket_id=ticket.id,
                file_path=relative_path,
                file_name=file.filename,
                file_size=FileStorageManager.get_file_size(file),
                file_type=FileStorageManager.get_file_type(file.filename),
            )

            db.session.add(ticket_file)
            db.session.commit()

            return jsonify(
                {
                    "success": True,
                    "message": "Файл успешно загружен",
                    "file": {
                        "id": ticket_file.id,
                        "name": ticket_file.file_name,
                        "size": FileStorageManager.format_file_size(
                            ticket_file.file_size
                        ),
                        "type": ticket_file.file_type,
                    },
                }
            )
        else:
            return jsonify({"success": False, "error": "Ошибка сохранения файла"})

    except Exception as e:
        current_app.logger.error(f"Ошибка загрузки файла тикета: {str(e)}")
        return jsonify({"success": False, "error": "Ошибка загрузки файла"})


@bp.route("/tickets/<int:ticket_id>/delete_file/<int:file_id>", methods=["POST"])
@login_required
def delete_ticket_file(ticket_id: int, file_id: int):
    """Удаление файла тикета"""
    try:
        ticket = Ticket.query.get_or_404(ticket_id)
        ticket_file = TicketFile.query.get_or_404(file_id)

        # Проверяем права доступа
        if not current_user.is_admin and ticket.user_id != current_user.id:
            return jsonify({"success": False, "error": "Доступ запрещен"})

        # Проверяем, что файл принадлежит тикету
        if ticket_file.ticket_id != ticket_id:
            return jsonify({"success": False, "error": "Файл не найден"})

        # Проверяем статус тикета
        if ticket.status == "closed":
            return jsonify(
                {"success": False, "error": "Нельзя удалять файлы из закрытого тикета"}
            )

        from .utils.file_storage import FileStorageManager

        # Удаляем файл с диска
        if FileStorageManager.delete_file(ticket_file.file_path):
            # Удаляем запись из БД
            db.session.delete(ticket_file)
            db.session.commit()

            return jsonify({"success": True, "message": "Файл успешно удален"})
        else:
            return jsonify({"success": False, "error": "Ошибка удаления файла"})

    except Exception as e:
        current_app.logger.error(f"Ошибка удаления файла тикета: {str(e)}")
        return jsonify({"success": False, "error": "Ошибка удаления файла"})


@bp.route("/api/tickets/<int:ticket_id>/files")
@login_required
def get_ticket_files(ticket_id: int):
    """Получение списка файлов тикета"""
    try:
        ticket = Ticket.query.get_or_404(ticket_id)

        # Проверяем права доступа
        if not current_user.is_admin and ticket.user_id != current_user.id:
            return jsonify({"success": False, "error": "Доступ запрещен"})

        from .utils.file_storage import FileStorageManager

        files_info = []
        for ticket_file in ticket.files:
            files_info.append(
                {
                    "id": ticket_file.id,
                    "name": ticket_file.file_name,
                    "size": FileStorageManager.format_file_size(ticket_file.file_size),
                    "type": ticket_file.file_type,
                    "uploaded_at": ticket_file.uploaded_at.strftime("%d.%m.%Y %H:%M"),
                    "path": ticket_file.file_path,
                }
            )

        return jsonify({"success": True, "files": files_info})

    except Exception as e:
        current_app.logger.error(f"Ошибка получения файлов тикета: {str(e)}")
        return jsonify({"success": False, "error": "Ошибка получения файлов"})


@bp.route("/api/create_ticket", methods=["POST"])
@login_required
def create_ticket():
    """API для создания тикета через модальное окно"""
    try:
        subject = request.form.get("subject", "").strip()
        message = request.form.get("message", "").strip()
        files = request.files.getlist("files")

        # Валидация
        if not subject or len(subject) < 5:
            return jsonify(
                {"success": False, "error": "Тема должна содержать минимум 5 символов"}
            )

        if not message or len(message) < 10:
            return jsonify(
                {
                    "success": False,
                    "error": "Сообщение должно содержать минимум 10 символов",
                }
            )

        # Создаем тикет
        ticket = Ticket(user_id=current_user.id, subject=subject, message=message)

        db.session.add(ticket)
        db.session.flush()  # Получаем ID тикета

        # Обрабатываем файлы с использованием FileStorageManager
        if files:
            from .utils.file_storage import FileStorageManager

            # Обрабатываем файлы тикета
            saved_files = FileStorageManager.process_ticket_files(files, ticket.id)

            # Создаем записи о файлах в БД
            for file_info in saved_files:
                ticket_file = TicketFile(
                    ticket_id=ticket.id,
                    file_path=file_info["file_path"],
                    file_name=file_info["file_name"],
                    file_size=file_info["file_size"],
                    file_type=file_info["file_type"],
                )
                db.session.add(ticket_file)

        db.session.commit()

        return jsonify(
            {"success": True, "message": "Тикет успешно создан", "ticket_id": ticket.id}
        )

    except Exception as e:
        current_app.logger.error(f"Ошибка создания тикета: {str(e)}")
        db.session.rollback()
        return jsonify({"success": False, "error": "Ошибка создания тикета"})


@bp.route("/api/notifications")
@login_required
def get_notifications():
    """API для получения уведомлений пользователя"""
    # Получаем уведомления, исключая те, что связаны с закрытыми тикетами
    notifications = (
        Notification.query.filter_by(user_id=current_user.id, is_read=False)
        .order_by(Notification.created_at.desc())
        .all()
    )

    # Фильтруем уведомления от закрытых тикетов
    filtered_notifications = []
    for notification in notifications:
        # Если это уведомление о тикете, проверяем его статус
        if notification.link and "/my-tickets/" in notification.link:
            try:
                ticket_id = int(notification.link.split("/")[-1])
                ticket = Ticket.query.get(ticket_id)
                if ticket and ticket.status != "closed":
                    filtered_notifications.append(notification)
            except (ValueError, IndexError):
                # Если не удалось извлечь ID тикета, включаем уведомление
                filtered_notifications.append(notification)
        else:
            # Если это не уведомление о тикете, включаем его
            filtered_notifications.append(notification)

    return jsonify(
        {
            "success": True,
            "notifications": [
                {
                    "id": n.id,
                    "title": n.title,
                    "message": n.message,
                    "type": n.type,
                    "link": n.link,
                    "created_at": n.created_at.strftime("%d.%m.%Y в %H:%M"),
                }
                for n in filtered_notifications
            ],
        }
    )


@bp.route("/api/notifications/<int:notification_id>/read", methods=["POST"])
@login_required
def mark_notification_read(notification_id: int):
    """API для отметки уведомления как прочитанного"""
    notification = Notification.query.get_or_404(notification_id)

    # Проверяем, что уведомление принадлежит текущему пользователю
    if notification.user_id != current_user.id:
        return jsonify({"success": False, "error": "Доступ запрещен"})

    notification.is_read = True
    db.session.commit()

    return jsonify({"success": True})


@bp.route("/api/ticket/user_response", methods=["POST"])
@login_required
def user_response_to_ticket():
    """API для ответа пользователя на тикет"""
    try:
        # Получаем данные из формы
        ticket_id = request.form.get("ticket_id")
        message = request.form.get("message", "").strip()
        files = request.files.getlist("files")

        # Валидация
        if not message or len(message) < 5:
            return jsonify(
                {
                    "success": False,
                    "error": "Сообщение должно содержать минимум 5 символов",
                }
            )

        # Находим тикет
        ticket = Ticket.query.get_or_404(ticket_id)

        # Проверяем, что тикет принадлежит текущему пользователю
        if ticket.user_id != current_user.id:
            return jsonify({"success": False, "error": "Доступ запрещен"})

        # Проверяем, что тикет не закрыт
        if ticket.status == "closed":
            return jsonify({"success": False, "error": "Тикет закрыт"})

        # Проверяем, что есть ответ администратора
        admin_messages = TicketMessage.query.filter_by(
            ticket_id=ticket.id, is_admin=True
        ).first()
        if not admin_messages:
            return jsonify(
                {"success": False, "error": "Нет ответа администратора для ответа"}
            )

        # Создаем новое сообщение пользователя
        user_message = TicketMessage(
            ticket_id=ticket.id,
            user_id=current_user.id,
            message=message,
            is_admin=False,
        )

        db.session.add(user_message)

        # Обновляем время последнего ответа пользователя
        ticket.user_response = message
        ticket.user_response_at = datetime.utcnow()
        ticket.updated_at = datetime.utcnow()

        # Обрабатываем файлы
        if files:
            import os
            from werkzeug.utils import secure_filename

            upload_dir = os.path.join(current_app.static_folder, "ticket_files")
            if not os.path.exists(upload_dir):
                os.makedirs(upload_dir)

            for file in files:
                if file and file.filename and file.filename.strip():
                    # Проверяем размер файла (максимум 10MB)
                    file.seek(0, 2)
                    file_size = file.tell()
                    file.seek(0)

                    if file_size > 10 * 1024 * 1024:  # 10MB
                        continue

                    # Проверяем расширение файла
                    allowed_extensions = {
                        "png",
                        "jpg",
                        "jpeg",
                        "gif",
                        "pdf",
                        "doc",
                        "docx",
                        "txt",
                        "zip",
                        "rar",
                    }
                    file_extension = (
                        file.filename.rsplit(".", 1)[1].lower()
                        if "." in file.filename
                        else ""
                    )

                    if file_extension not in allowed_extensions:
                        continue

                    # Сохраняем файл
                    filename = secure_filename(file.filename)
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    unique_filename = (
                        f"{ticket.id}_user_response_{timestamp}_{filename}"
                    )

                    file_path = os.path.join(upload_dir, unique_filename)
                    file.save(file_path)

                    # Определяем тип файла
                    if file_extension in {"png", "jpg", "jpeg", "gif"}:
                        file_type = "image"
                    elif file_extension in {"pdf", "doc", "docx", "txt"}:
                        file_type = "document"
                    else:
                        file_type = "archive"

                    # Создаем запись о файле
                    ticket_file = TicketFile(
                        ticket_id=ticket.id,
                        file_path=f"ticket_files/{unique_filename}",
                        file_name=filename,
                        file_size=file_size,
                        file_type=file_type,
                    )

                    db.session.add(ticket_file)

        db.session.commit()

        return jsonify({"success": True, "message": "Ответ отправлен"})

    except Exception as e:
        current_app.logger.error(f"Ошибка отправки ответа пользователя: {str(e)}")
        return jsonify({"success": False, "error": "Ошибка отправки ответа"})


@bp.errorhandler(400)
def bad_request(error):
    """Обработчик ошибки 400 Bad Request"""
    current_app.logger.error("=== ОШИБКА 400 BAD REQUEST ===")
    current_app.logger.error(f"Ошибка: {error}")
    current_app.logger.error(f"Запрос: {request}")
    current_app.logger.error(f"Данные формы: {request.form}")
    current_app.logger.error(f"Файлы: {request.files}")
    current_app.logger.error(f"Заголовки: {dict(request.headers)}")
    return jsonify({"success": False, "error": "Некорректный запрос"}), 400

@bp.route("/macro/time")
def macro_time():
    """Страница конвертера времени"""
    return render_template("for_my_love/time.html")
    
@bp.route("/macro")
def macro():
    """Страница макросов"""
    return render_template("for_my_love/macro.html")