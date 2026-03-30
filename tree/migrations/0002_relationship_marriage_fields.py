from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tree', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='relationship',
            name='marriage_date',
            field=models.DateField(blank=True, null=True, verbose_name='Heiratsdatum'),
        ),
        migrations.AddField(
            model_name='relationship',
            name='marriage_place',
            field=models.CharField(blank=True, max_length=200, verbose_name='Heiratsort'),
        ),
        migrations.AddField(
            model_name='relationship',
            name='divorce_date',
            field=models.DateField(blank=True, null=True, verbose_name='Scheidungsdatum'),
        ),
    ]
