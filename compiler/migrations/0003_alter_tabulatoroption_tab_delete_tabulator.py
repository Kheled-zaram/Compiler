# Generated by Django 4.2 on 2023-05-09 13:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('compiler', '0002_tabulator_tabulatoroption_dependanttabulatoroption'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tabulatoroption',
            name='tab',
            field=models.CharField(choices=[('STANDARD', 'STANDARD'), ('OPTIMIZATIONS', 'OPTIMIZATIONS'), ('PROCESSOR', 'PROCESSOR'), ('DEPENDANT', 'DEPENDANT'), ((('STANDARD', False), ('OPTIMIZATIONS', True), ('PROCESSOR', False), ('DEPENDANT', False)), (('STANDARD', False), ('OPTIMIZATIONS', True), ('PROCESSOR', False), ('DEPENDANT', False)))], max_length=20),
        ),
        migrations.DeleteModel(
            name='Tabulator',
        ),
    ]
