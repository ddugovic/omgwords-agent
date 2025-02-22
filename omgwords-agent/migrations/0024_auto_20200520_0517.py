# Generated by Django 2.2.10 on 2020-05-20 05:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('omgwords-agent', '0023_user_remove_pb_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='discorduser',
            name='discriminator',
            field=models.CharField(max_length=4, null=True),
        ),
        migrations.AddConstraint(
            model_name='discorduser',
            constraint=models.UniqueConstraint(fields=('username', 'discriminator'), name='unique_username_discriminator'),
        ),
    ]
