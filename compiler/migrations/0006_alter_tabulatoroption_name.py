# Generated by Django 4.2 on 2023-05-10 15:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('compiler', '0005_alter_tabulatoroption_name_alter_tabulatoroption_tab'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tabulatoroption',
            name='name',
            field=models.CharField(max_length=40),
        ),
    ]
