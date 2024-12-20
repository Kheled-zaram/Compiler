# Generated by Django 4.2 on 2023-05-10 07:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('compiler', '0004_alter_tabulatoroption_tab'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tabulatoroption',
            name='name',
            field=models.CharField(max_length=40, unique=True),
        ),
        migrations.AlterField(
            model_name='tabulatoroption',
            name='tab',
            field=models.CharField(choices=[('STANDARD', 'STANDARD'), ('OPTIMIZATIONS', 'OPTIMIZATIONS'), ('PROCESSOR', 'PROCESSOR'), ('DEPENDANT', 'DEPENDANT'), ('is_multiple_choice', 'is_multiple_choice')], max_length=20),
        ),
    ]
