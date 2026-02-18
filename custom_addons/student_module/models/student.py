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
