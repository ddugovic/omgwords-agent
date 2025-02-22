# Generated by Django 2.2.4 on 2020-02-11 06:27

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('omgwords-agent', '0011_user_same_piece_sets'),
    ]

    operations = [
        migrations.CreateModel(
            name='Coin',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('heads', models.IntegerField(default=0)),
                ('tails', models.IntegerField(default=0)),
                ('sides', models.IntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='Side',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField()),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='+', to='omgwords-agent.User')),
            ],
        ),
    ]
