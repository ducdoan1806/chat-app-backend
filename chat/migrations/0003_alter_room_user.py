# Generated by Django 5.0.6 on 2024-06-26 04:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0002_room_user'),
    ]

    operations = [
        migrations.AlterField(
            model_name='room',
            name='user',
            field=models.ManyToManyField(blank=True, to='chat.userprofile'),
        ),
    ]
