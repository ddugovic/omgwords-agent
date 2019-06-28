# Generated by Django 2.2.2 on 2019-06-28 05:21

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('preferred_name', models.CharField(max_length=64, null=True)),
                ('ntsc_pb', models.IntegerField(null=True)),
                ('pal_pb', models.IntegerField(null=True)),
            ],
        ),
    ]
