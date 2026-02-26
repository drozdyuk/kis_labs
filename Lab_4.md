# ЛАБОРАТОРНА РОБОТА №4

## ЗВІТНІСТЬ, АНАЛІТИКА ТА БІЗНЕС-ЛОГІКА В ERP

### Передумови

Для виконання лабораторної роботи необхідне працююче середовище Odoo 19 у Docker з лабораторної роботи №2. Переконайтеся, що контейнери `odoo19-app` та `odoo19-db` запущені, модуль `student_module` встановлено, а в моделі `edu.student` є щонайменше 10 записів з різними групами, балами та статусами (зокрема записи, імпортовані через ETL у ЛР3).

```bash
# Перевірка: контейнери працюють
docker ps

# Перевірка: Odoo відповідає
curl -s -o /dev/null -w "%{http_code}" http://localhost:8069/web/login
# Очікуваний результат: 200
```

---

## 1. Мета роботи

Метою лабораторної роботи є:

- створення PDF-звіту (QWeb) для моделі Odoo з використанням шаблонізатора та агрегованих даних;
- реалізація wizard (TransientModel) для масових операцій із демонстрацією транзакційної атомарності;
- практичне дослідження конкурентного доступу та механізму оптимістичного блокування в ORM Odoo;
- розуміння зв'язку між транзакційними гарантіями ACID та поведінкою ERP-системи при одночасній роботі кількох користувачів.

Робота складається з трьох частин: QWeb-звіт (Частина I), wizard для масових операцій (Частина II), дослідження конкурентного доступу (Частина III).

> **Контекст.** У лекції 3 ми розглядали транзакції, ACID, рівні ізоляції та механізми конкурентного доступу. Ця лабораторна дає практичний досвід: ви побачите, як Odoo реалізує атомарність через rollback при помилці у wizard, і спостерігатимете за оптимістичним блокуванням при одночасному редагуванні запису двома користувачами.

---

## 2. Теоретичні відомості

### 2.1. Звітність у ERP-системах

Звітність — один із головних результатів роботи ERP. Дані, накопичені в системі (продажі, закупівлі, виробництво, кадри), мають цінність лише тоді, коли з них можна отримати структуровану інформацію для прийняття рішень.

В Odoo звіти генеруються за допомогою шаблонізатора QWeb — XML-based движка, що рендерить HTML, який потім конвертується у PDF через wkhtmltopdf. QWeb-шаблон має доступ до даних моделі та може виконувати ітерації, умовне відображення, обчислення агрегатів.

Типові звіти в ERP: рахунок-фактура (invoice), комерційна пропозиція (quotation), складська накладна (delivery slip), звіт про залишки, відомість оцінок.

### 2.2. QWeb: основи синтаксису

QWeb-шаблони використовують спеціальні XML-атрибути для управління рендерингом:

| Директива | Призначення | Приклад |
|-----------|-------------|---------|
| `t-foreach` / `t-as` | Цикл по колекції | `<t t-foreach="students" t-as="s">` |
| `t-esc` | Вивід значення (з екрануванням) | `<span t-esc="s.name"/>` |
| `t-if` | Умовне відображення | `<span t-if="s.is_honors">★</span>` |
| `t-set` | Визначення змінної | `<t t-set="total" t-value="0"/>` |
| `t-att-*` | Динамічний HTML-атрибут | `<td t-att-class="'bold' if s.is_honors else ''"` |
| `t-call` | Виклик іншого шаблону | `t-call="web.external_layout"` |

Шаблон `web.external_layout` — стандартна обгортка Odoo, що додає верхній та нижній колонтитули компанії (логотип, адреса, реквізити). Використовуйте його для всіх друкованих звітів.

### 2.3. Wizard (TransientModel)

Wizard в Odoo — це модель типу `TransientModel`, призначена для інтерактивних операцій, які потребують вводу від користувача перед виконанням. На відміну від звичайних моделей (`Model`), записи `TransientModel` зберігаються тимчасово і автоматично очищуються системою (за замовчуванням через 1 годину).

Типовий цикл роботи wizard: (1) користувач натискає кнопку → відкривається форма wizard; (2) користувач вводить параметри (наприклад, новий статус, дату, причину); (3) натискає «Підтвердити» → wizard виконує масову операцію; (4) тимчасовий запис wizard видаляється автоматично.

Wizards є особливо цінними для операцій, що мають бути атомарними: або всі зміни застосовуються, або жодна. Оскільки метод wizard виконується в одній транзакції, помилка на будь-якому записі призводить до повного rollback — жоден запис не буде змінено.

### 2.4. Конкурентний доступ та оптимістичне блокування

У багатокористувацькій ERP-системі кілька людей можуть одночасно редагувати один і той самий запис. Це створює класичну проблему «втраченого оновлення» (lost update): користувач A і B відкривають запис, A зберігає зміни, B зберігає свої — і перезаписує зміни A.

Odoo вирішує це через оптимістичне блокування на основі поля `write_date`. Механізм працює так:

1. Коли користувач відкриває форму, клієнт запам'ятовує `write_date` запису.
2. Коли користувач зберігає зміни, ORM порівнює запам'ятований `write_date` з поточним значенням у БД.
3. Якщо значення збігаються — ніхто інший не змінював запис, зміни зберігаються.
4. Якщо значення відрізняються — хтось уже змінив запис, ORM сигналізує про конфлікт.

Це називається «оптимістичним», тому що система не блокує запис при відкритті (на відміну від «песимістичного» блокування), а перевіряє конфлікт лише в момент збереження. Такий підхід ефективніший для веб-додатків, де більшість сесій завершуються без конфлікту.

---

# ЧАСТИНА I. QWEB-ЗВІТ

## 3. Розширення модуля student_module

Для додавання звіту потрібно розширити існуючий модуль `student_module` новими файлами. Робота ведеться в каталозі `custom_addons/student_module/`.

### 3.1. Оновлена структура модуля

Після завершення цієї частини структура модуля виглядатиме так:

```
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
  report/                    ← НОВИЙ каталог
    student_report.xml       ← шаблон звіту
  wizard/                    ← НОВИЙ каталог
    __init__.py
    mass_status_wizard.py
    mass_status_wizard_view.xml
```

### 3.2. Оновлення маніфесту

Додайте нові файли до `data` у `__manifest__.py`:

```python
{
    "name": "Student Module",
    "version": "19.0.2.0.0",
    "category": "Education",
    "summary": "Навчальний модуль: моделі, звітність, wizards.",
    "depends": ["base"],
    "data": [
        "security/ir.model.access.csv",
        "security/student_rules.xml",
        "views/student_views.xml",
        "views/menus.xml",
        "report/student_report.xml",
        "wizard/mass_status_wizard_view.xml",
    ],
    "installable": True,
    "application": True,
}
```

### 3.3. Оновлення ініціалізації

Додайте імпорт пакету `wizard` у `student_module/__init__.py`:

```python
from . import models
from . import wizard
```

## 4. Допоміжний метод для звіту

Щоб звіт містив агреговані дані (середній бал, кількість відмінників), додамо допоміжний метод до моделі `edu.student`. Він обчислюватиме статистику по групах, яку QWeb-шаблон використає при рендерингу.

Додайте наступний метод у файл `models/student.py` (всередині класу `StudentProfile`):

```python
def get_report_data(self):
    """
    Формує структуру даних для звіту: студенти згруповані за group_code,
    з агрегатами по кожній групі.
    """
    groups = {}
    for rec in self:
        code = rec.group_code or "Без групи"
        if code not in groups:
            groups[code] = {
                "code": code,
                "students": [],
                "total": 0,
                "honors_count": 0,
                "grade_sum": 0.0,
            }
        g = groups[code]
        g["students"].append(rec)
        g["total"] += 1
        g["grade_sum"] += rec.avg_grade or 0.0
        if rec.is_honors:
            g["honors_count"] += 1

    # Обчислюємо середній бал по групі
    for g in groups.values():
        g["avg"] = round(g["grade_sum"] / g["total"], 2) if g["total"] else 0

    # Сортуємо за кодом групи
    return dict(sorted(groups.items()))
```

Після збереження файлу перезапустіть контейнер:

```bash
docker restart odoo19-app
```

## 5. QWeb-шаблон звіту

### 5.1. Реєстрація звіту та шаблон

Створіть файл `report/student_report.xml`:

```xml
<odoo>

    <!-- ===================================================
         1. Реєстрація дії звіту (кнопка Print у списку/формі)
         =================================================== -->
    <record id="action_report_student_list" model="ir.actions.report">
        <field name="name">Відомість студентів</field>
        <field name="model">edu.student</field>
        <field name="report_type">qweb-pdf</field>
        <field name="report_name">student_module.report_student_list</field>
        <field name="report_file">student_module.report_student_list</field>
        <field name="binding_model_id" ref="model_edu_student"/>
        <field name="binding_type">report</field>
    </record>

    <!-- ===================================================
         2. QWeb-шаблон звіту
         =================================================== -->
    <template id="report_student_list">
        <t t-call="web.html_container">
            <t t-foreach="docs" t-as="doc_batch">

                <!-- Ми отримуємо recordset, викликаємо наш метод -->
                <t t-set="report_data" t-value="docs.get_report_data()"/>

                <t t-call="web.external_layout">
                    <div class="page">

                        <!-- Заголовок -->
                        <h2 style="text-align: center; margin-bottom: 20px;">
                            Відомість студентів
                        </h2>

                        <!-- Дата формування -->
                        <p style="text-align: right; font-size: 12px; color: #666;">
                            Дата формування:
                            <span t-esc="context_timestamp(datetime.datetime.now()).strftime('%d.%m.%Y %H:%M')"/>
                        </p>

                        <!-- Цикл по групах -->
                        <t t-foreach="report_data.items()" t-as="group_item">
                            <t t-set="group_code" t-value="group_item[0]"/>
                            <t t-set="group" t-value="group_item[1]"/>

                            <h3 style="margin-top: 25px; border-bottom: 2px solid #333; padding-bottom: 5px;">
                                Група: <span t-esc="group_code"/>
                            </h3>

                            <!-- Таблиця студентів групи -->
                            <table class="table table-sm table-bordered"
                                   style="font-size: 13px;">
                                <thead>
                                    <tr style="background-color: #f0f0f0;">
                                        <th style="width: 5%;">№</th>
                                        <th style="width: 40%;">ПІБ</th>
                                        <th style="width: 15%; text-align: center;">Середній бал</th>
                                        <th style="width: 20%; text-align: center;">Статус</th>
                                        <th style="width: 10%; text-align: center;">Відзнака</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <t t-foreach="group['students']" t-as="student">
                                        <tr t-att-style="'font-weight: bold;' if student.is_honors else ''">
                                            <td><span t-esc="student_index + 1"/></td>
                                            <td><span t-esc="student.name"/></td>
                                            <td style="text-align: center;">
                                                <span t-esc="'%.2f' % student.avg_grade"/>
                                            </td>
                                            <td style="text-align: center;">
                                                <t t-if="student.status == 'studying'">Навчається</t>
                                                <t t-if="student.status == 'completed'">Завершив(ла)</t>
                                                <t t-if="student.status == 'academic_leave'">Акад. відпустка</t>
                                            </td>
                                            <td style="text-align: center;">
                                                <t t-if="student.is_honors">★</t>
                                            </td>
                                        </tr>
                                    </t>
                                </tbody>
                            </table>

                            <!-- Підсумок по групі -->
                            <div style="margin-top: 5px; margin-bottom: 15px;
                                        font-size: 12px; color: #444;">
                                Всього: <strong t-esc="group['total']"/> студентів |
                                Середній бал: <strong t-esc="group['avg']"/> |
                                Відмінників: <strong t-esc="group['honors_count']"/>
                            </div>

                        </t>

                        <!-- Загальний підсумок -->
                        <div style="margin-top: 30px; padding: 10px;
                                    border-top: 2px solid #333; font-size: 13px;">
                            <strong>Загалом у відомості:</strong>
                            <span t-esc="len(docs)"/> студентів
                        </div>

                    </div>
                </t>

            </t>
        </t>
    </template>

</odoo>
```

### 5.2. Пояснення архітектури звіту

Звіт складається з двох частин у XML-файлі:

**`ir.actions.report`** — реєструє звіт у системі. Поле `binding_model_id` прив'язує його до моделі `edu.student`, тому кнопка «Print» з'явиться у списку та формі студентів. Поле `report_name` вказує на технічний ID QWeb-шаблону.

**`template`** — QWeb-шаблон рендерингу. Змінна `docs` містить recordset обраних студентів. Ми викликаємо `docs.get_report_data()`, щоб отримати згруповані дані з агрегатами. Обгортка `web.external_layout` додає колонтитули компанії.

> **Зверніть увагу:** у шаблоні немає SQL-запитів чи прямого доступу до бази. Усі дані отримуються через ORM (recordset `docs` та метод моделі). Це забезпечує дотримання прав доступу: звіт покаже тільки ті записи, до яких користувач має доступ згідно з ACL та record rules.

## 6. Встановлення та тестування звіту

### 6.1. Оновлення модуля

```bash
docker restart odoo19-app
```

В Odoo: **Apps → Student Module → ⋮ (меню) → Upgrade**.

Якщо виникає помилка — перегляньте логи:

```bash
docker logs --tail 50 odoo19-app
```

### 6.2. Генерація звіту

1. Перейдіть до **Education → Студенти**.
2. Виберіть кілька записів (чекбокси у списку) або відкрийте один запис.
3. Натисніть **Print → Відомість студентів**.
4. Завантажиться PDF-файл з відомістю, згрупованою за групами, з підсумками.

### 6.3. Що перевірити

- Студенти згруповані за `group_code`.
- Середній бал кожної групи обчислений коректно.
- Відмінники (бал ≥ 90) виділені жирним шрифтом та позначкою ★.
- Колонтитули компанії присутні (логотип, адреса).
- Дата формування відповідає поточному моменту.

---

# ЧАСТИНА II. WIZARD ДЛЯ МАСОВИХ ОПЕРАЦІЙ

## 7. Концепція wizard

У ЛР2 ви працювали з прямим редагуванням записів: відкрив форму — змінив поле — зберіг. Але що, якщо потрібно змінити статус одразу 50 студентам? Відкривати кожну форму окремо — неприйнятно. Для цього існують wizards.

Наш wizard дозволить: (1) вибрати новий статус, (2) опціонально вказати причину, (3) застосувати зміну до всіх обраних студентів в одній транзакції. Якщо хоча б один запис не пройде валідацію — жоден не буде змінений.

## 8. Реалізація wizard

### 8.1. Модель wizard (`wizard/mass_status_wizard.py`)

Створіть файл `wizard/__init__.py`:

```python
from . import mass_status_wizard
```

Створіть файл `wizard/mass_status_wizard.py`:

```python
from odoo import models, fields, api
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)


class MassStatusWizard(models.TransientModel):
    """
    Wizard для масової зміни статусу студентів.
    TransientModel — записи тимчасові, автоматично очищуються.
    """
    _name = "edu.mass.status.wizard"
    _description = "Масова зміна статусу студентів"

    new_status = fields.Selection(
        selection=[
            ("studying", "Навчається"),
            ("completed", "Завершив(ла)"),
            ("academic_leave", "Академічна відпустка"),
        ],
        string="Новий статус",
        required=True,
    )

    reason = fields.Char(
        string="Причина зміни",
        help="Необов'язкове поле. Буде записано в лог.",
    )

    min_grade = fields.Float(
        string="Мінімальний бал",
        help="Якщо вказано — статус зміниться тільки у студентів "
             "з балом не нижче цього значення.",
    )

    student_count = fields.Integer(
        string="Кількість обраних",
        compute="_compute_student_count",
    )

    @api.depends()
    def _compute_student_count(self):
        """Показує, скільки студентів буде оброблено."""
        active_ids = self.env.context.get("active_ids", [])
        for rec in self:
            rec.student_count = len(active_ids)

    def action_apply(self):
        """
        Застосовує зміну статусу. Виконується в одній транзакції:
        якщо будь-який запис спричинить помилку — жоден не буде змінено.
        """
        self.ensure_one()

        active_ids = self.env.context.get("active_ids", [])
        if not active_ids:
            raise UserError("Не обрано жодного студента.")

        students = self.env["edu.student"].browse(active_ids)

        # Фільтрація за мінімальним балом (якщо вказано)
        if self.min_grade:
            filtered = students.filtered(
                lambda s: s.avg_grade and s.avg_grade >= self.min_grade
            )
            skipped = len(students) - len(filtered)
            if skipped:
                _logger.info(
                    "Wizard: пропущено %d студентів з балом нижче %.1f",
                    skipped, self.min_grade,
                )
            students = filtered

        if not students:
            raise UserError(
                f"Жоден студент не відповідає критерію "
                f"(мінімальний бал: {self.min_grade})."
            )

        # Масове оновлення — одна транзакція
        students.write({"status": self.new_status})

        reason_msg = f" Причина: {self.reason}" if self.reason else ""
        _logger.info(
            "Wizard: статус %d студентів змінено на '%s'.%s",
            len(students), self.new_status, reason_msg,
        )

        # Повідомлення користувачу
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Статус оновлено",
                "message": (
                    f"Змінено статус {len(students)} студентів "
                    f"на «{dict(self._fields['new_status'].selection).get(self.new_status)}»."
                ),
                "type": "success",
                "sticky": False,
                "next": {"type": "ir.actions.act_window_close"},
            },
        }
```

### 8.2. Інтерфейс wizard (`wizard/mass_status_wizard_view.xml`)

```xml
<odoo>

    <!-- Форма wizard -->
    <record id="view_mass_status_wizard_form" model="ir.ui.view">
        <field name="name">edu.mass.status.wizard.form</field>
        <field name="model">edu.mass.status.wizard</field>
        <field name="arch" type="xml">
            <form string="Масова зміна статусу">
                <group>
                    <field name="student_count" readonly="1"
                           widget="statinfo" string="Обрано студентів"/>
                </group>
                <group>
                    <field name="new_status"/>
                    <field name="min_grade"/>
                    <field name="reason" placeholder="Наприклад: завершення семестру"/>
                </group>
                <footer>
                    <button name="action_apply" string="Застосувати"
                            type="object" class="btn-primary"/>
                    <button string="Скасувати" class="btn-secondary"
                            special="cancel"/>
                </footer>
            </form>
        </field>
    </record>

    <!-- Action для виклику wizard зі списку студентів -->
    <record id="action_mass_status_wizard" model="ir.actions.act_window">
        <field name="name">Змінити статус</field>
        <field name="res_model">edu.mass.status.wizard</field>
        <field name="view_mode">form</field>
        <field name="target">new</field>
        <field name="binding_model_id" ref="model_edu_student"/>
        <field name="binding_view_types">list</field>
    </record>

</odoo>
```

### 8.3. Оновлення прав доступу

Додайте рядок для wizard у файл `security/ir.model.access.csv`:

```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_edu_student_user,edu.student user,model_edu_student,base.group_user,1,1,1,0
access_edu_mass_status_wizard,edu.mass.status.wizard user,model_edu_mass_status_wizard,base.group_user,1,1,1,1
```

## 9. Тестування wizard

### 9.1. Встановлення

```bash
docker restart odoo19-app
```

В Odoo: **Apps → Student Module → ⋮ → Upgrade**.

### 9.2. Сценарій 1: Масова зміна статусу

1. Перейдіть до **Education → Студенти**.
2. Виберіть 5–7 студентів за допомогою чекбоксів.
3. Натисніть **Action (⚙) → Змінити статус**.
4. У вікні wizard:
   - **Новий статус:** Завершив(ла)
   - **Причина:** Завершення навчального року
   - **Мінімальний бал:** залиште порожнім
5. Натисніть **Застосувати**.
6. Перевірте: статус усіх обраних студентів змінився на «Завершив(ла)».

### 9.3. Сценарій 2: Фільтрація за балом

1. Виберіть 5–7 студентів з різними балами.
2. **Action → Змінити статус**.
3. **Новий статус:** Навчається, **Мінімальний бал:** 85.
4. **Застосувати**.
5. Перевірте: статус змінився тільки у студентів з балом ≥ 85. Інші залишилися без змін.

### 9.4. Сценарій 3: Демонстрація атомарності

Цей сценарій демонструє транзакційний rollback. Для його виконання тимчасово додамо перевірку, що імітує помилку на конкретному записі.

Додайте в метод `action_apply` наступний блок **перед** рядком `students.write(...)`:

```python
        # ТИМЧАСОВО: імітація помилки для демонстрації rollback
        for s in students:
            if s.avg_grade and s.avg_grade < 50:
                raise UserError(
                    f"Помилка: студент {s.name} має бал {s.avg_grade}, "
                    f"що нижче допустимого для зміни статусу. "
                    f"Жоден запис не було змінено (rollback)."
                )
```

Тепер:
1. Переконайтеся, що серед студентів є хоча б один із балом < 50. Якщо немає — створіть або оновіть запис через веб-інтерфейс.
2. Виберіть кількох студентів, серед яких є студент із балом < 50.
3. **Action → Змінити статус → Завершив(ла) → Застосувати**.
4. Результат: **помилка**. Повідомлення про студента з низьким балом.
5. Перевірте: **жоден** студент зі списку не змінив статус — ні ті, що з балом < 50, ні ті, що з балом > 50. Це і є атомарність: транзакція або виконується повністю, або не виконується зовсім.

> Після демонстрації **видаліть** тимчасовий блок коду та перезапустіть контейнер.

---

# ЧАСТИНА III. КОНКУРЕНТНИЙ ДОСТУП

## 10. Підготовка до експерименту

Для дослідження конкурентного доступу потрібні два окремі сеанси користувачів. Ви можете використати:
- два різні браузери (наприклад, Chrome та Firefox);
- один браузер у звичайному режимі та другий у режимі інкогніто;
- два профілі одного браузера.

### 10.1. Створення другого користувача

Якщо другий тестовий користувач ще не створений (з ЛР2):

1. Увійдіть як admin.
2. **Settings → Users & Companies → Users → New**.
3. Заповніть:
   - **Name:** Тестовий Викладач
   - **Email / Login:** `teacher@test.com`
   - **Password:** `teacher`
   - **Навчальна група (x_group_code):** залиште порожнім (або вкажіть групу, записи якої він має бачити)
4. Збережіть. Переконайтеся, що у користувача є група «Internal User».

> **Про record rules.** Пам'ятайте, що record rule з ЛР2 обмежує видимість записів за `group_code`. Для цього експерименту обом користувачам потрібен доступ до одного й того ж запису. Якщо record rule заважає — тимчасово деактивуйте його в **Settings → Technical → Record Rules** або працюйте під admin у обох сеансах (admin ігнорує record rules).

## 11. Експеримент: одночасне редагування

### 11.1. Хід експерименту

Виконуйте дії в точній послідовності, фіксуючи кожен крок скріншотом.

**Крок 1.** У браузері A увійдіть як admin. Відкрийте запис студента (наприклад, ID=1). Запишіть поточне значення `avg_grade` (наприклад, 85.0).

**Крок 2.** У браузері B увійдіть як `teacher@test.com` (або як admin в інкогніто). Відкрийте **той самий** запис студента.

**Крок 3.** У браузері A змініть `avg_grade` на 90.0. **Збережіть** (кнопка 💾 або Ctrl+S).

**Крок 4.** У браузері B (де все ще відкрита стара версія запису з балом 85.0) змініть `avg_grade` на 75.0. **Спробуйте зберегти.**

### 11.2. Очікуваний результат

Odoo виявить конфлікт: запис було змінено між моментом відкриття форми та моментом збереження. Система покаже попередження про те, що дані були змінені іншим користувачем, і запропонує перезавантажити запис.

Це і є оптимістичне блокування в дії: Odoo не блокує запис при відкритті, але виявляє конфлікт при спробі зберегти застарілі дані.

### 11.3. Альтернативний сценарій: послідовне редагування

Повторіть експеримент, але цього разу:

**Крок 3.** У браузері A змініть бал та збережіть.

**Крок 4.** У браузері B **перезавантажте сторінку** (F5) перед редагуванням.

**Крок 5.** У браузері B змініть бал та збережіть.

Результат: обидва збереження пройдуть без конфлікту, тому що браузер B отримав актуальну версію запису (з оновленим `write_date`) перед редагуванням.

### 11.4. Спостереження за write_date

Щоб побачити механізм зсередини, увімкніть режим розробника та відкрийте вкладку технічних полів запису:

1. Відкрийте запис студента.
2. У режимі розробника: **Debug menu (🐛) → View Metadata**.
3. Зверніть увагу на поля `write_date` та `write_uid` — вони показують, коли і ким запис було змінено востаннє.

Кожне успішне збереження оновлює `write_date`. Саме це значення порівнюється при наступному збереженні для виявлення конфлікту.

## 12. Додатковий експеримент: конкурентний доступ через API

Конфлікт можна відтворити і через XML-RPC. Створіть файл `concurrency_test.py`:

```python
"""
Демонстрація конкурентного доступу через XML-RPC.
Два "клієнти" читають один запис, потім обидва намагаються записати.
"""

from connection import connect

models, db, uid, password = connect()

MODEL = "edu.student"

# Знайдемо перший запис
ids = models.execute_kw(db, uid, password, MODEL, "search", [[]], {"limit": 1})
if not ids:
    print("Немає записів для тесту.")
    exit(1)

record_id = ids[0]

# "Клієнт A" читає запис
data_a = models.execute_kw(
    db, uid, password, MODEL, "read",
    [[record_id]], {"fields": ["name", "avg_grade"]}
)[0]
print(f"Клієнт A прочитав: {data_a['name']}, бал = {data_a['avg_grade']}")

# "Клієнт B" читає той самий запис
data_b = models.execute_kw(
    db, uid, password, MODEL, "read",
    [[record_id]], {"fields": ["name", "avg_grade"]}
)[0]
print(f"Клієнт B прочитав: {data_b['name']}, бал = {data_b['avg_grade']}")

# Клієнт A записує
models.execute_kw(
    db, uid, password, MODEL, "write",
    [[record_id], {"avg_grade": 91.0}]
)
print("Клієнт A записав бал = 91.0 ✓")

# Клієнт B записує (через XML-RPC — без перевірки write_date!)
models.execute_kw(
    db, uid, password, MODEL, "write",
    [[record_id], {"avg_grade": 72.0}]
)
print("Клієнт B записав бал = 72.0 ✓")

# Фінальний стан
final = models.execute_kw(
    db, uid, password, MODEL, "read",
    [[record_id]], {"fields": ["avg_grade"]}
)[0]
print(f"\nФінальний бал: {final['avg_grade']}")
print("⚠ Зміна клієнта A втрачена (lost update)!")
```

### 12.1. Аналіз результату

Запустіть скрипт:

```bash
python3 concurrency_test.py
```

Результат: обидва запити `write` виконаються успішно, фінальний бал = 72.0. Зміна клієнта A (91.0) перезаписана клієнтом B — це класична проблема «втраченого оновлення» (lost update).

**Чому це відбувається?** Оптимістичне блокування в Odoo реалізовано на рівні **веб-клієнта**, а не на рівні ORM. Веб-клієнт зберігає `write_date` при відкритті форми та перевіряє його при збереженні. XML-RPC API цієї перевірки не виконує — кожен `write` застосовується безумовно.

Це важливий архітектурний момент: зовнішні інтеграції (API, ETL-скрипти) повинні самостійно реалізовувати контроль конкурентності, якщо це необхідно. Наприклад, через перевірку `write_date` перед записом або через використання блокувань на рівні PostgreSQL.

---

# ПОРЯДОК ВИКОНАННЯ, ЗВІТ, КОНТРОЛЬНІ ЗАПИТАННЯ

## 13. Порядок виконання роботи

**Частина I. QWeb-звіт:**

13.1. Додати метод `get_report_data()` у модель `edu.student`.

13.2. Створити QWeb-шаблон звіту `report/student_report.xml`.

13.3. Оновити маніфест, оновити модуль.

13.4. Згенерувати PDF-звіт, перевірити коректність груп, агрегатів, форматування.

**Частина II. Wizard:**

13.5. Створити модель wizard `edu.mass.status.wizard` (TransientModel).

13.6. Створити форму wizard та зареєструвати action.

13.7. Оновити ACL (`ir.model.access.csv`), оновити модуль.

13.8. Протестувати сценарії 1–3 (масова зміна, фільтрація за балом, демонстрація rollback).

**Частина III. Конкурентний доступ:**

13.9. Створити другого тестового користувача (якщо ще не створений).

13.10. Провести експеримент з одночасним редагуванням у двох браузерах (11.1–11.2).

13.11. Провести альтернативний сценарій з перезавантаженням форми (11.3).

13.12. Провести API-експеримент з lost update (розділ 12).

## 14. Вимоги до звіту

Звіт подається у друкованому або електронному вигляді та повинен містити:

14.1. Згенерований PDF-звіт (вкладений або скріншот). Пояснення структури QWeb-шаблону: як працюють `t-foreach`, `t-if`, `t-esc`, як обчислюються агрегати.

14.2. Повний код wizard (`mass_status_wizard.py`) із поясненням: чому обрано `TransientModel`, як працює `context.get("active_ids")`, навіщо потрібен `ensure_one()`.

14.3. Скріншоти wizard: форма з заповненими полями, результат виконання, повідомлення про успіх.

14.4. Демонстрація атомарності: скріншоти до та після спроби виконання wizard з помилкою. Пояснення: чому жоден запис не змінився.

14.5. Протокол експерименту з конкурентним доступом: покрокові скріншоти обох браузерів, опис попередження про конфлікт.

14.6. Лог виконання `concurrency_test.py` із поясненням: чому lost update відбувається через API, але не через веб-інтерфейс. Яка архітектурна відмінність?

14.7. Висновки: роль QWeb-звітів у ERP; транзакційна атомарність як гарантія цілісності даних; оптимістичне vs песимістичне блокування — переваги та обмеження кожного підходу.

## 15. Контрольні запитання

1. Чим QWeb-шаблон відрізняється від звичайного HTML? Які директиви QWeb ви використали у звіті?
2. Чому звіт викликає метод моделі (`get_report_data`) замість прямого SQL-запиту? Які переваги має ORM-підхід у контексті прав доступу?
3. Поясніть різницю між `Model` та `TransientModel`. Чому wizard реалізовано як `TransientModel`, а не як звичайну модель?
4. Що означає атомарність транзакції? Як ви продемонстрували rollback у wizard?
5. У чому різниця між оптимістичним та песимістичним блокуванням? Який підхід використовує Odoo і чому?
6. Чому оптимістичне блокування Odoo працює у веб-інтерфейсі, але не працює через XML-RPC API? Як би ви реалізували захист від lost update в ETL-скрипті з ЛР3?
7. Що відбудеться, якщо запланована дія (cron) і користувач одночасно змінюють один і той самий запис? Хто «переможе»?
8. Чому метод `write` у wizard виконується одним викликом для всього recordset, а не в циклі по кожному запису окремо? Яка різниця з точки зору продуктивності та транзакційності?
9. Наведіть 3 приклади бізнес-операцій в ERP, для яких wizard є природнішим інтерфейсом, ніж пряме редагування записів.
10. Як Odoo визначає, що запис було змінено іншим користувачем? Яке поле використовується та де зберігається попереднє значення?
