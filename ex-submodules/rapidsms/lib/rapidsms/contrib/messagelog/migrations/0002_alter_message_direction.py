# Generated by Django 3.2.12 on 2022-05-05 15:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('messagelog', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='message',
            name='direction',
            field=models.CharField(choices=[('I', 'Incoming'), ('O', 'Outgoing')], max_length=1),
        ),
    ]