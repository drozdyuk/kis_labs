# ЛАБОРАТОРНА РОБОТА N1

## РОЗГОРТАННЯ ERP-СИСТЕМИ ODOO 19, МОДУЛЬНА АРХІТЕКТУРА ТА КРИПТОГРАФІЧНИЙ ЗАХИСТ ДОКУМЕНТІВ

### Передумови

Для виконання лабораторної роботи необхідно мати комп'ютер із не менше ніж 8 ГБ оперативної пам'яті (оптимально 16 ГБ), 4 ядрами CPU та щонайменше 10 ГБ вільного місця на диску. Операційна система — Ubuntu 22.04/24.04, Windows 10/11 або macOS.

---

## 1. Мета роботи

Метою лабораторної роботи є:

- формування практичних навичок розгортання ERP-системи Odoo 19 у контейнеризованому середовищі Docker;
- засвоєння базових принципів модульної архітектури Odoo: модулі, моделі, поля, методи, інтерфейси та права доступу;
- ознайомлення з криптографічними механізмами захисту даних у корпоративних інформаційних системах;
- реалізація кастомного модуля цифрового підпису документів та практична демонстрація забезпечення цілісності даних у ERP-системі.

Робота складається з трьох логічних етапів: розгортання середовища (Частина I), створення навчального модуля з контролем доступу (Частина II), реалізація криптографічного захисту документів (Частина III).

---

## 2. Теоретичні відомості

### 2.1. Архітектура Odoo як ERP-платформи

Odoo є багаторівневою корпоративною інформаційною системою, що реалізує клієнт-серверну архітектуру. Користувач працює через веб-інтерфейс у браузері. Сервер застосунку (Python) обробляє запити, виконує перевірки та реалізує бізнес-логіку. Дані зберігаються у реляційній базі даних PostgreSQL.

Взаємодія між об'єктами предметної області та базою даних здійснюється через ORM (Object-Relational Mapping). ORM дозволяє описувати структуру даних у вигляді Python-класів (моделей) і працювати з записами через методи API, забезпечуючи узгодженість даних та підтримку транзакційної логіки.

### 2.2. Модульна архітектура Odoo

Функціональність Odoo організована у вигляді модулів. Модуль — це ізольований функціональний компонент, який може: (1) створювати нові моделі та поля, (2) розширювати існуючі моделі через механізм наслідування (`_inherit`), (3) додавати інтерфейси користувача, (4) визначати правила доступу, (5) реалізовувати бізнес-логіку. Модульна архітектура дозволяє керувати залежностями між компонентами, спрощує супровід і дає змогу розвивати систему без модифікації ядра.

### 2.3. Контроль доступу: права на модель та обмеження записів

Контроль доступу в Odoo складається з двох базових рівнів. Перший рівень — права доступу до моделі (читання/створення/редагування/видалення), які визначаються у файлі `ir.model.access.csv`. Другий рівень — обмеження доступу до конкретних записів (record rules), які задають доменні умови (domain) і застосовуються залежно від груп користувачів. Такий підхід дозволяє реалізувати як загальні рольові обмеження, так і сегментацію даних (наприклад, доступ лише до «своїх» записів).

### 2.4. Криптографічні методи захисту інформації

Криптографічні методи поділяються на симетричні та асиметричні. Симетричні алгоритми (AES, DES) використовують один і той самий ключ для шифрування і дешифрування. Їх перевага — висока швидкодія, недолік — необхідність безпечної передачі секретного ключа обом сторонам.

Асиметричні алгоритми передбачають використання пари ключів: відкритого (public key) та закритого (private key). Відкритий ключ може бути загальнодоступним, закритий — відомий лише його власнику.

### 2.5. Алгоритм RSA

RSA (Rivest–Shamir–Adleman) є асиметричним алгоритмом, що базується на складності факторизації добутку двох великих простих чисел.

Генерація ключів:

1. Вибираються два великих простих числа *p* та *q*.
2. Обчислюється *n = p × q* (модуль).
3. Обчислюється функція Ейлера: *φ(n) = (p − 1)(q − 1)*.
4. Вибирається відкрита експонента *e*, взаємно проста з *φ(n)* (зазвичай *e = 65537*).
5. Обчислюється закрита експонента *d* як мультиплікативна обернена: *d ≡ e⁻¹ (mod φ(n))*.

Відкритий ключ: *(e, n)*. Закритий ключ: *(d, n)*.

Шифрування: *C = Mᵉ mod n*. Дешифрування: *M = Cᵈ mod n*.

### 2.6. Цифровий підпис та хешування

Цифровий підпис забезпечує три ключові властивості: автентичність (підтвердження авторства), цілісність (виявлення змін у документі) та неспростовність (автор не може заперечити факт підпису).

Процес підпису: (1) обчислюється криптографічний хеш документа (наприклад, SHA-256); (2) хеш шифрується закритим ключем підписанта — отримується підпис.

Процес перевірки: (1) обчислюється хеш отриманого документа; (2) підпис розшифровується відкритим ключем — відновлюється оригінальний хеш; (3) порівнюються два хеші: якщо збігаються — документ не змінювався.

**Чому підписується хеш, а не весь документ?** RSA-шифрування повільне для великих обсягів даних. Хеш-функція перетворює дані довільного розміру у рядок фіксованої довжини (256 біт для SHA-256). Підпис хешу є математично еквівалентним підпису всього документа з точки зору безпеки.

### 2.7. Криптографія у контексті ERP-систем

У корпоративних інформаційних системах криптографічні механізми використовуються для захисту фінансових транзакцій, електронного документообігу, забезпечення аудиторського сліду та відповідності нормативним вимогам (eIDAS у ЄС, Закон України «Про електронний цифровий підпис»). Цифровий підпис дозволяє зафіксувати стан документа (наприклад, замовлення на продаж) у конкретний момент часу та виявити будь-які подальші модифікації.

---

# ЧАСТИНА I. РОЗГОРТАННЯ ODOO 19 У DOCKER

## 3. Загальні положення

Docker використовується для стандартизації середовища виконання: усі студенти отримують однакову версію Odoo, PostgreSQL та узгоджені параметри конфігурації незалежно від операційної системи. У межах лабораторної роботи використовується мінімальна конфігурація з двох контейнерів: (1) PostgreSQL як СУБД, (2) Odoo 19 як сервер застосунку.

> **Примітка.** Використовується офіційний Docker-образ `odoo:19.0` з Docker Hub. Якщо під час виконання образ `odoo:19.0` недоступний, допускається використання `odoo:18.0` із відповідними позначками у звіті.

## 4. Розгортання на Ubuntu 22.04/24.04

### 4.1. Оновлення системи та встановлення Docker

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y docker.io docker-compose-plugin
```

Перевірка встановлення:

```bash
docker --version
docker compose version
```

### 4.2. Налаштування запуску Docker без sudo

```bash
sudo usermod -aG docker $USER
```

Після виконання команди необхідно перезапустити сесію користувача (вийти/зайти) або перезавантажити систему.

```bash
docker run --rm hello-world
```

### 4.3. Створення структури проєкту

```bash
mkdir -p ~/odoo19-lab/{custom_addons,config}
cd ~/odoo19-lab
```

Каталог `custom_addons` призначений для навчальних модулів. Каталог `config` містить конфігураційні файли Odoo.

### 4.4. Створення конфігурації Odoo (`config/odoo.conf`)

```ini
[options]
admin_passwd = admin
db_host = db
db_port = 5432
db_user = odoo
db_password = odoo
addons_path = /usr/lib/python3/dist-packages/odoo/addons,/mnt/extra-addons
log_level = info
```

Параметр `admin_passwd` є майстер-паролем для керування базами. `addons_path` визначає, де Odoo шукає модулі: стандартні модулі в контейнері та навчальні модулі, змонтовані у `/mnt/extra-addons`.

### 4.5. Створення `docker-compose.yml`

```yaml
services:
  db:
    image: postgres:15
    container_name: odoo19-db
    restart: unless-stopped
    environment:
      POSTGRES_DB: postgres
      POSTGRES_USER: odoo
      POSTGRES_PASSWORD: odoo
    volumes:
      - odoo19_db_data:/var/lib/postgresql/data

  odoo:
    image: odoo:19.0
    container_name: odoo19-app
    restart: unless-stopped
    depends_on:
      - db
    ports:
      - "8069:8069"
    volumes:
      - odoo19_web_data:/var/lib/odoo
      - ./custom_addons:/mnt/extra-addons
      - ./config/odoo.conf:/etc/odoo/odoo.conf
    command: ["odoo", "--dev=xml"]

volumes:
  odoo19_db_data:
  odoo19_web_data:
```

Пояснення ключових параметрів:

- `restart: unless-stopped` — контейнери автоматично перезапускаються після перезавантаження системи.
- `command: ["odoo", "--dev=xml"]` — режим розробника на рівні сервера; зміни у XML-файлах views застосовуються без повного перезапуску контейнера. *Для продуктивного середовища цей параметр слід видалити.*
- Том `odoo19_db_data` забезпечує збереження даних PostgreSQL між перезапусками.

### 4.6. Запуск контейнерів та перевірка

```bash
docker compose up -d
docker ps
```

Очікуваний результат: два контейнери зі статусом Up — `odoo19-db` та `odoo19-app`.

Перегляд логів Odoo (для діагностики):

```bash
docker logs -f odoo19-app
```

### 4.7. Створення бази даних у веб-інтерфейсі

Відкрити у браузері адресу http://localhost:8069. При першому запуску Odoo запропонує створити базу даних:

- **Master Password** — значення `admin_passwd` з `odoo.conf` (за замовчуванням: `admin`).
- **Database Name** — наприклад, `erplab`.
- **Email / Password** — облікові дані адміністратора (наприклад, `admin` / `admin`).
- **Language** — Ukrainian або English.
- **Country** — Ukraine.
- **Demo Data** — рекомендується увімкнути для навчальних цілей.

Після створення бази встановити модуль **Sales** (знадобиться у Частині III) та створити кілька тестових записів для підтвердження працездатності системи.

### 4.8. Активація режиму розробника (Developer Mode)

Режим розробника є обов'язковим для роботи з кастомними модулями. Без нього пункт «Update Apps List» недоступний, і нові модулі не з'являться у списку додатків.

Для активації: перейти у меню **Settings** → у нижній частині сторінки натиснути посилання **Activate the developer mode**.

Альтернативний спосіб: додати `?debug=1` до URL-адреси, наприклад: `http://localhost:8069/odoo?debug=1`.

### 4.9. Зупинка та очищення середовища

Зупинка без видалення даних:

```bash
docker compose down
```

Повне очищення разом з даними (застосовувати обережно):

```bash
docker compose down -v
```

## 5. Розгортання на Windows 10/11

### 5.1. Підготовка середовища: WSL2 та Docker Desktop

```bash
wsl --install
```

Після встановлення WSL2 необхідно перезавантажити систему та інсталювати Docker Desktop. У налаштуваннях Docker Desktop слід увімкнути **Use the WSL 2 based engine** та інтеграцію з обраним WSL-дистрибутивом.

```bash
docker --version
docker compose version
```

### 5.2. Створення проєкту та запуск

Створити каталог проєкту, наприклад `C:\Users\<User>\odoo19-lab`, і в ньому каталоги `custom_addons` та `config`. Далі створити файли `docker-compose.yml` та `config\odoo.conf` за аналогією з Ubuntu-версією (зміст ідентичний).

```bash
cd C:\Users\<User>\odoo19-lab
docker compose up -d
```

Доступ до системи: http://localhost:8069. У разі конфлікту порту 8069 дозволяється змінити порт публікації на 8070: `"8070:8069"` у `docker-compose.yml`.

## 6. Розгортання на macOS

### 6.1. Встановлення Docker Desktop та створення проєкту

```bash
docker --version
docker compose version
mkdir -p ~/odoo19-lab/{custom_addons,config}
cd ~/odoo19-lab
```

### 6.2. Додавання конфігураційних файлів та запуск

Створити `config/odoo.conf` і `docker-compose.yml` за аналогією з Ubuntu-версією. Запуск:

```bash
docker compose up -d
```

Доступ до системи: http://localhost:8069.

---

# ЧАСТИНА II. МОДУЛЬНА АРХІТЕКТУРА: СТВОРЕННЯ НАВЧАЛЬНОГО МОДУЛЯ

## 7. Структура навчального модуля

У каталозі `custom_addons` необхідно створити модуль `student_module` з такою структурою:

```
custom_addons/
  student_module/
    __init__.py
    __manifest__.py
    models/
      __init__.py
      student.py
      res_users.py
    views/
      student_views.xml
      menus.xml
    security/
      ir.model.access.csv
      student_rules.xml
```

Файл `res_users.py` додано для розширення моделі `res.users` кастомним полем, яке використовуватиметься у record rule (див. розділ 10.2).

## 8. Код модуля

### 8.1. Маніфест модуля (`__manifest__.py`)

Маніфест визначає метадані модуля, його залежності та перелік файлів даних.

```python
{
    "name": "Student Module",
    "version": "19.0.1.0.0",
    "category": "Education",
    "summary": "Навчальний модуль для демонстрації моделей, полів, методів і прав доступу.",
    "depends": ["base"],
    "data": [
        "security/ir.model.access.csv",
        "security/student_rules.xml",
        "views/student_views.xml",
        "views/menus.xml",
    ],
    "installable": True,
    "application": True,
}
```

Параметр `"application": True` забезпечує відображення модуля на головному екрані Apps без необхідності знімати фільтр.

### 8.2. Ініціалізація Python-пакетів

**Файл `student_module/__init__.py`:**

```python
from . import models
```

**Файл `student_module/models/__init__.py`:**

```python
from . import student
from . import res_users
```

### 8.3. Розширення моделі користувача (`models/res_users.py`)

Для демонстрації record rule необхідно, щоб кожен користувач мав атрибут навчальної групи. Цей атрибут додається через механізм наслідування (`_inherit`) моделі `res.users` — один із фундаментальних патернів Odoo: замість модифікації ядра ми розширюємо існуючу модель новим полем.

```python
from odoo import models, fields

class ResUsers(models.Model):
    _inherit = "res.users"

    x_group_code = fields.Char(
        string="Навчальна група",
        help="Код навчальної групи користувача (наприклад, КН-51м)",
    )
```

Після встановлення модуля у формі кожного користувача (Settings → Users & Companies → Users) з'явиться нове поле «Навчальна група».

### 8.4. Модель студента (`models/student.py`)

Модель `edu.student` описує навчальний профіль студента з обчислюваним полем (compute) і перевіркою обмежень (constraint).

```python
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class StudentProfile(models.Model):
    _name = "edu.student"
    _description = "Профіль студента (навчальна модель)"

    name = fields.Char(string="ПІБ", required=True)
    group_code = fields.Char(string="Група", required=True)
    avg_grade = fields.Float(string="Середній бал", digits=(3, 2))
    status = fields.Selection(
        selection=[
            ("studying", "Навчається"),
            ("completed", "Завершив(ла)"),
            ("academic_leave", "Академічна відпустка"),
        ],
        string="Статус",
        default="studying",
        required=True,
    )
    is_honors = fields.Boolean(
        string="Відзнака",
        compute="_compute_is_honors",
        store=True,
    )

    @api.depends("avg_grade")
    def _compute_is_honors(self):
        for rec in self:
            rec.is_honors = bool(rec.avg_grade and rec.avg_grade >= 90.0)

    @api.constrains("avg_grade")
    def _check_avg_grade_range(self):
        for rec in self:
            if rec.avg_grade and (rec.avg_grade < 0 or rec.avg_grade > 100):
                raise ValidationError(
                    "Середній бал має бути в діапазоні від 0 до 100."
                )
```

Поле `is_honors` є похідним і зберігається у БД (`store=True`), що дозволяє використовувати його у фільтрах та звітах. Constraint гарантує коректність введених значень.

### 8.5. Інтерфейс користувача (`views/student_views.xml`)

Інтерфейси в Odoo описуються декларативно в XML. Tree view — для списку записів, Form view — для перегляду та редагування.

```xml
<odoo>
    <record id="view_student_tree" model="ir.ui.view">
        <field name="name">edu.student.tree</field>
        <field name="model">edu.student</field>
        <field name="arch" type="xml">
            <tree>
                <field name="name"/>
                <field name="group_code"/>
                <field name="avg_grade"/>
                <field name="status"/>
                <field name="is_honors"/>
            </tree>
        </field>
    </record>

    <record id="view_student_form" model="ir.ui.view">
        <field name="name">edu.student.form</field>
        <field name="model">edu.student</field>
        <field name="arch" type="xml">
            <form>
                <sheet>
                    <group>
                        <group string="Основна інформація">
                            <field name="name"/>
                            <field name="group_code"/>
                        </group>
                        <group string="Навчання">
                            <field name="avg_grade"/>
                            <field name="status"/>
                            <field name="is_honors" readonly="1"/>
                        </group>
                    </group>
                </sheet>
            </form>
        </field>
    </record>

    <record id="action_student" model="ir.actions.act_window">
        <field name="name">Студенти</field>
        <field name="res_model">edu.student</field>
        <field name="view_mode">tree,form</field>
    </record>
</odoo>
```

### 8.6. Меню (`views/menus.xml`)

```xml
<odoo>
    <menuitem id="menu_edu_root"
              name="Education"
              sequence="10"/>

    <menuitem id="menu_students"
              name="Студенти"
              parent="menu_edu_root"
              action="action_student"
              sequence="10"/>
</odoo>
```

## 9. Налаштування доступу

### 9.1. Права доступу до моделі (`security/ir.model.access.csv`)

```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_edu_student_user,edu.student user,model_edu_student,base.group_user,1,1,1,0
```

`perm_unlink=0` забороняє видалення звичайним користувачам. Адміністратор (суперкористувач) завжди має повний доступ.

### 9.2. Record rule: доступ лише до «своєї» групи (`security/student_rules.xml`)

```xml
<odoo>
    <record id="student_group_rule" model="ir.rule">
        <field name="name">Students: access only own group</field>
        <field name="model_id" ref="model_edu_student"/>
        <field name="domain_force">
            [('group_code', '=', user.x_group_code)]
        </field>
        <field name="groups" eval="[(4, ref('base.group_user'))]"/>
    </record>
</odoo>
```

`domain_force` задає фільтр, який автоматично застосовується до пошуку та відображення записів: користувач бачить лише записи, де `group_code` відповідає його `x_group_code`.

> **Важливо.** Щоб record rule працював, після встановлення модуля необхідно: (1) перейти до Settings → Users & Companies → Users; (2) відкрити профіль тестового користувача; (3) заповнити поле «Навчальна група» (наприклад, КН-51м); (4) створити записи студентів із відповідними значеннями `group_code`. Суперкористувач (admin) ігнорує record rules — для тестування потрібно створити окремого користувача з правами Internal User.

## 10. Встановлення модуля student_module

1. Переконатися, що режим розробника активовано (п. 4.8).
2. Перейти до **Apps → Update Apps List** → підтвердити оновлення.
3. Знайти «Student Module» та натиснути **Install**.
4. У разі помилки — переглянути логи:

```bash
docker logs --tail 100 odoo19-app
```

Типові причини помилок: синтаксична помилка в Python-коді, невірний шлях у маніфесті, пропущений імпорт у `__init__.py`.

### 10.1. Тестування модуля

- Створити 3–5 записів студентів із різними групами та балами.
- Перевірити, що поле `is_honors` автоматично обчислюється (бал ≥ 90 → True).
- Перевірити спрацювання constraint: ввести бал більше 100 — система повинна відхилити запис.
- Перевірити заборону видалення: під звичайним користувачем спробувати видалити запис.
- Перевірити дію record rule: створити двох користувачів із різними `x_group_code`, увійти під кожним і переконатися, що кожен бачить лише «свої» записи.

---

# ЧАСТИНА III. КРИПТОГРАФІЧНИЙ ЗАХИСТ ДОКУМЕНТІВ

## 11. Підготовка середовища

### 11.1. Перевірка наявності бібліотеки cryptography

Бібліотека `cryptography` входить до стандартних залежностей Odoo (файл `requirements.txt`). У Docker-образі `odoo:19.0` вона встановлена за замовчуванням:

```bash
docker exec odoo19-app python3 -c "import cryptography; print(cryptography.__version__)"
```

Очікуваний результат — версія бібліотеки (наприклад, `42.0.8`).

Якщо бібліотека відсутня (що малоймовірно для офіційного образу):

```bash
docker exec -u root odoo19-app pip3 install cryptography --break-system-packages
docker restart odoo19-app
```

### 11.2. Модуль Sales

Для демонстрації підпису у контексті реального бізнес-документа використовуватиметься модель `sale.order`. Якщо модуль Sales ще не встановлено — встановити його через Apps (мав бути встановлений у п. 4.7).

## 12. Створення модуля document_sign

### 12.1. Структура модуля

У каталозі `custom_addons` (поруч із `student_module`) створити модуль `document_sign`:

```
custom_addons/
  document_sign/
    __init__.py
    __manifest__.py
    models/
      __init__.py
      sale_order_sign.py
    views/
      sale_order_sign_views.xml
```

### 12.2. Маніфест (`__manifest__.py`)

```python
{
    "name": "Document Digital Signature",
    "version": "19.0.1.0.0",
    "category": "Sales",
    "summary": "Цифровий підпис та перевірка цілісності замовлень на продаж.",
    "depends": ["sale_management"],
    "data": [
        "views/sale_order_sign_views.xml",
    ],
    "installable": True,
    "application": False,
    "license": "LGPL-3",
}
```

Модуль залежить від `sale`, оскільки розширює модель `sale.order`. `"application": False` вказує, що це розширення існуючого модуля.

### 12.3. Ініціалізація пакетів

**Файл `document_sign/__init__.py`:**

```python
from . import models
```

**Файл `document_sign/models/__init__.py`:**

```python
from . import sale_order_sign
```

### 12.4. Модель: розширення sale.order (`models/sale_order_sign.py`)

Повний код моделі з детальними коментарями. Модуль додає до замовлення на продаж три поля (підпис, статус верифікації, дату підпису) та методи підпису, перевірки та скидання.

```python
import base64
import logging

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding

from odoo import models, fields, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class SaleOrderSign(models.Model):
    _inherit = "sale.order"

    # ---- Нові поля ----
    digital_signature = fields.Binary(
        string="Цифровий підпис",
        readonly=True,
        copy=False,
        help="RSA-підпис хешу ключових полів документа.",
    )
    signature_date = fields.Datetime(
        string="Дата підпису",
        readonly=True,
        copy=False,
    )
    is_verified = fields.Boolean(
        string="Підпис перевірено",
        default=False,
        readonly=True,
        copy=False,
    )
    
    # ======================================================
    # Нотифікації через bus.bus (форма оновлюється коректно)
    # ======================================================

    def _notify(self, title, message, notification_type="success", sticky=False):
        """Send a notification via bus so the form still reloads."""
        self.env["bus.bus"]._sendone(
            self.env.user.partner_id,
            "simple_notification",
            {
                "title": title,
                "message": message,
                "type": notification_type,
                "sticky": sticky,
            },
        )

    # ======================================================
    # Допоміжні методи: робота з ключами
    # ======================================================

    def _get_or_create_keys(self):
        """
        Отримує або генерує пару RSA-ключів.
        Ключі зберігаються у системних параметрах Odoo
        (ir.config_parameter), що забезпечує їх персистентність
        між перезапусками сервера. У промислових системах ключі
        зберігаються на рівні користувача або у зовнішньому HSM,
        а не як глобальний параметр системи.
        """
        ICP = self.env["ir.config_parameter"].sudo()

        private_pem = ICP.get_param("document_sign.private_key")
        public_pem = ICP.get_param("document_sign.public_key")

        if not private_pem or not public_pem:
            # Генерація нової пари ключів (2048 біт)
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
            )

            # Серіалізація у формат PEM
            private_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption(),
            ).decode("utf-8")

            public_pem = private_key.public_key().public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            ).decode("utf-8")

            # Збереження у системних параметрах
            ICP.set_param("document_sign.private_key", private_pem)
            ICP.set_param("document_sign.public_key", public_pem)

            _logger.info("Document Sign: RSA key pair generated and stored.")

        return private_pem, public_pem

    def _load_private_key(self, pem_data):
        """Завантажує закритий ключ із PEM-рядка."""
        return serialization.load_pem_private_key(
            pem_data.encode("utf-8"),
            password=None,
        )

    def _load_public_key(self, pem_data):
        """Завантажує відкритий ключ із PEM-рядка."""
        return serialization.load_pem_public_key(
            pem_data.encode("utf-8"),
        )

    # ======================================================
    # Формування payload — дані, що підписуються
    # ======================================================

    def _get_sign_payload(self):
        """
        Формує рядок із ключових полів документа.
        Саме цей рядок буде хешований і підписаний.
        Якщо будь-яке з цих полів змінити після підпису,
        верифікація виявить розбіжність.
        """
        self.ensure_one()
        payload = (
            f"{self.name or ''}"
            f"|{self.date_order or ''}"
            f"|{self.amount_total or 0.0}"
            f"|{self.partner_id.id or 0}"
        )
        return payload.encode("utf-8")

    # ======================================================
    # Дії (actions): підпис і перевірка
    # ======================================================

    def action_sign_document(self):
        """
        Підписує документ:
        1. Формує payload із ключових полів.
        2. Підписує payload закритим ключем (RSA + SHA-256).
           Бібліотека cryptography сама обчислює хеш під час
           виклику sign() — додаткове хешування не потрібне.
        3. Зберігає підпис у полі digital_signature.
        """
        self.ensure_one()

        if self.digital_signature:
            raise UserError(
                "Документ вже підписано. Для повторного підпису "
                "спочатку скиньте поточний підпис."
            )

        private_pem, _public_pem = self._get_or_create_keys()
        private_key = self._load_private_key(private_pem)

        payload = self._get_sign_payload()

        # Підпис: бібліотека cryptography виконує SHA-256
        # хешування автоматично у межах виклику sign()
        signature = private_key.sign(
            payload,
            padding.PKCS1v15(),
            hashes.SHA256(),
        )

        self.write({
            "digital_signature": base64.b64encode(signature),
            "signature_date": fields.Datetime.now(),
            "is_verified": True,
        })

        self._notify(
            "Підпис створено",
            f"Документ {self.name} успішно підписано.",
        )

    def action_verify_signature(self):
        """
        Перевіряє цифровий підпис:
        1. Формує payload із поточних значень полів.
        2. Розшифровує підпис відкритим ключем.
        3. Порівнює хеші: якщо дані змінилися — верифікація
           провалюється (InvalidSignature).
        """
        self.ensure_one()

        if not self.digital_signature:
            raise UserError("Документ не підписано.")

        _private_pem, public_pem = self._get_or_create_keys()
        public_key = self._load_public_key(public_pem)

        payload = self._get_sign_payload()
        signature = base64.b64decode(self.digital_signature)

        try:
            public_key.verify(
                signature,
                payload,
                padding.PKCS1v15(),
                hashes.SHA256(),
            )
            self.is_verified = True
            self._notify(
                "Результат перевірки",
                f"Підпис документа {self.name} валідний. "
                "Цілісність даних підтверджено.",
                "success",
                sticky=True,
            )
        except Exception:
            self.is_verified = False
            self._notify(
                "Результат перевірки",
                f"УВАГА! Підпис документа {self.name} НЕВАЛІДНИЙ. "
                "Дані були змінені після підпису!",
                "danger",
                sticky=True,
            )

    def action_reset_signature(self):
        """Скидає підпис для повторного підписання."""
        self.ensure_one()
        self.write({
            "digital_signature": False,
            "signature_date": False,
            "is_verified": False,
        })
```

**Ключові архітектурні рішення:**

- **Збереження ключів у `ir.config_parameter`.** Системні параметри Odoo зберігаються в БД PostgreSQL і є персистентними між перезапусками контейнера. Це стандартний підхід Odoo для зберігання конфігурацій.
- **Відсутність подвійного хешування.** Метод `private_key.sign(payload, padding, hashes.SHA256())` самостійно обчислює SHA-256 хеш від payload. Окреме попереднє хешування через `hashlib` було б помилкою (підписувався б хеш від хешу).
- **Payload із роздільниками.** Символ `|` між полями запобігає колізіям (наприклад, `"AB|C" ≠ "A|BC"`).
- **Нотифікації.** Повернення `ir.actions.client` з `display_notification` — стандартний механізм Odoo для повідомлення користувача.

### 12.5. Інтерфейс (`views/sale_order_sign_views.xml`)

XML розширює стандартну форму замовлення на продаж, додаючи кнопки підпису/перевірки та блок інформації про підпис.

```xml
<odoo>

    <record id="view_order_form_sign" model="ir.ui.view">
        <field name="name">sale.order.form.sign</field>
        <field name="model">sale.order</field>
        <field name="inherit_id" ref="sale.view_order_form"/>
        <field name="arch" type="xml">

            <!-- Кнопки у верхній панелі форми -->
            <xpath expr="//form/header" position="inside">
                <button name="action_sign_document"
                        string="Підписати документ"
                        type="object"
                        class="btn-primary"
                        invisible="digital_signature"/>
                <button name="action_verify_signature"
                        string="Перевірити підпис"
                        type="object"
                        class="btn-warning"
                        invisible="not digital_signature"/>
                <button name="action_reset_signature"
                        string="Скинути підпис"
                        type="object"
                        class="btn-secondary"
                        invisible="not digital_signature"
                        confirm="Ви впевнені, що хочете скинути підпис?"/>
            </xpath>

            <!-- Блок інформації про підпис -->
            <xpath expr="//page[1]" position="before">
                <group string="Цифровий підпис" invisible="not digital_signature">
                    <group>
                        <field name="signature_date"/>
                        <field name="is_verified"
                               widget="boolean_toggle"
                               readonly="1"/>
                    </group>
                    <group>
                        <field name="digital_signature" readonly="1"
                               widget="char" string="Підпис (Base64)"/>
                    </group>
                </group>
            </xpath>

        </field>
    </record>

</odoo>
```

Пояснення: кнопка «Підписати документ» відображається лише якщо документ ще не підписано (атрибут `invisible`). Кнопки «Перевірити підпис» та «Скинути підпис» — лише якщо підпис присутній.

### 12.6. Встановлення модуля

1. Переконатися, що файли збережені в `custom_addons/document_sign/`.
2. Перейти до **Apps → Update Apps List**.
3. Знайти «Document Digital Signature» та натиснути **Install**.

## 13. Тестування криптографічного захисту

### 13.1. Сценарій 1: Підпис документа

1. Перейти до **Sales → Orders**.
2. Створити нове замовлення на продаж: вказати клієнта, додати продукт.
3. Натиснути **Підписати документ**.
4. Переконатися: з'явилося повідомлення про успішний підпис, відображається дата підпису та статус `is_verified = True`.

### 13.2. Сценарій 2: Перевірка цілісності (без змін)

1. На підписаному замовленні натиснути **Перевірити підпис**.
2. Результат: «Підпис валідний. Цілісність даних підтверджено.»

### 13.3. Сценарій 3: Виявлення модифікації (tamper detection)

Це ключовий сценарій, який демонструє практичну цінність цифрового підпису.

1. На підписаному замовленні запам'ятати суму (`amount_total`).

2. Змінити дані документа, що входять до payload. Для цього відредагувати рядки замовлення (додати продукт або змінити кількість), щоб змінилася загальна сума.

   Альтернативний спосіб (через SQL, для наочності):

   ```bash
   docker exec -it odoo19-db psql -U odoo -d erplab -c \
       "UPDATE sale_order SET amount_total = 99999.99 WHERE id = <ID>;"
   ```

   Замініть `<ID>` на фактичний ID запису, а `erplab` — на назву вашої бази.

3. Натиснути **Перевірити підпис**.

4. Результат: **«УВАГА! Підпис НЕВАЛІДНИЙ. Дані були змінені після підпису!»**, статус `is_verified` → False.

Цей сценарій ілюструє, як цифровий підпис захищає від несанкціонованих або випадкових змін у фінансових документах ERP-системи.

### 13.4. Сценарій 4: Повторний підпис

1. Натиснути **Скинути підпис** → підтвердити.
2. Підписати документ повторно.
3. Перевірити підпис — результат має бути позитивним.

---

# ПОРЯДОК ВИКОНАННЯ, ЗВІТ, КОНТРОЛЬНІ ЗАПИТАННЯ

## 14. Порядок виконання роботи

**Частина I. Розгортання:**

14.1. Встановити Docker та Docker Compose для своєї ОС.

14.2. Створити структуру проєкту, конфігурацію `odoo.conf` та `docker-compose.yml`.

14.3. Запустити контейнери, створити базу даних, активувати режим розробника.

14.4. Встановити модуль Sales та створити тестові записи.

**Частина II. Модульна архітектура:**

14.5. Створити структуру модуля `student_module`.

14.6. Реалізувати модель `edu.student` з computed field та constraint.

14.7. Реалізувати розширення `res.users` полем `x_group_code`.

14.8. Створити views (tree, form), action та меню.

14.9. Налаштувати `ir.model.access.csv` та record rule.

14.10. Встановити модуль та провести тестування (п. 10.1).

**Частина III. Криптографічний захист:**

14.11. Перевірити наявність бібліотеки `cryptography` у контейнері.

14.12. Створити модуль `document_sign` з повною структурою.

14.13. Реалізувати модель та XML-інтерфейс.

14.14. Встановити модуль та провести тестування за сценаріями 1–4 (розділ 13).

## 15. Вимоги до звіту

Звіт подається у друкованому або електронному вигляді та повинен містити:

15.1. Опис розгортання середовища (для своєї ОС) із ключовими командами та скріншотами: `docker ps`, веб-інтерфейс Odoo.

15.2. Опис структури модуля `student_module` із поясненням призначення каталогів і файлів.

15.3. Фрагменти коду моделей (включно з `res_users.py`) та пояснення полів, computed-логіки, constraint.

15.4. Скріншоти інтерфейсу `student_module`: tree view, form view, меню.

15.5. Налаштування доступів: вміст `ir.model.access.csv`, опис та демонстрація record rule зі скріншотами під різними користувачами.

15.6. Математичне обґрунтування алгоритму RSA: генерація ключів на числовому прикладі (наприклад, p=7, q=17), обчислення відкритого та закритого ключів, демонстрація шифрування та дешифрування одного символу.

15.7. Повний код модуля `document_sign` із поясненням архітектурних рішень: збереження ключів у `ir.config_parameter`, відсутність подвійного хешування, формування payload, механізм xpath для розширення views.

15.8. Скріншоти результатів тестування за всіма чотирма сценаріями (розділ 13).

15.9. Висновки: роль модульної архітектури у керованості ERP; значення контролю доступу та криптографічного захисту для корпоративних даних; порівняння різних механізмів захисту (ACL, record rules, цифровий підпис, аудиторський слід).

## 16. Контрольні запитання

1. Які компоненти формують мінімальну архітектуру Odoo та як вони взаємодіють між собою?
2. Що таке модуль Odoo та які типові артефакти він містить (навести приклади)?
3. Як ORM пов'язує модель Python із таблицею PostgreSQL? Які переваги дає такий підхід?
4. У чому різниця між computed field та звичайним полем? Які наслідки має `store=True`?
5. Поясніть механізм наслідування (`_inherit`) в Odoo. Чому розширення `res.users` та `sale.order` не потребує модифікації вихідного коду ядра?
6. У чому полягає різниця між правами доступу до моделі (`ir.model.access.csv`) та record rule?
7. Які ризики для підприємства можуть виникати за відсутності контролю доступу в ERP-системі?
8. У чому відмінність між симетричним та асиметричним шифруванням? Наведіть приклади алгоритмів кожного типу.
9. Чому для цифрового підпису використовується хеш документа, а не весь документ?
10. Яким чином RSA забезпечує неможливість підробки підпису? Яка математична задача лежить в основі стійкості RSA?
11. Чому ключі зберігаються в `ir.config_parameter`, а не у файлах на диску? Які переваги та недоліки такого підходу?
12. Яку роль відіграє цифровий підпис у забезпеченні цілісності транзакцій в ERP? Наведіть приклади бізнес-сценаріїв, де підпис є критичним.
