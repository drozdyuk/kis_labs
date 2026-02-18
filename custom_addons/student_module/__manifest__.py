{
    'name': 'Student Module',
    'version': '19.0.1.0.0',
    'category': 'Education',
    'summary': 'Manage student records',
    'description': 'A module to manage student information for educational purposes.',
    'author': 'Student',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'security/student_rules.xml',
        'views/student_views.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
