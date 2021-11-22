# Generated by Django 2.2.24 on 2021-07-13 07:48

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import model_utils.fields
import opaque_keys.edx.django.models
import simple_history.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='CourseAppStatus',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('app_id', models.CharField(db_index=True, max_length=32)),
                ('enabled', models.BooleanField(default=False)),
                ('course_key', opaque_keys.edx.django.models.CourseKeyField(db_index=True, max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='HistoricalCourseAppStatus',
            fields=[
                ('id', models.IntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('app_id', models.CharField(db_index=True, max_length=32)),
                ('enabled', models.BooleanField(default=False)),
                ('course_key', opaque_keys.edx.django.models.CourseKeyField(db_index=True, max_length=255)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField()),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'historical course app status',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': 'history_date',
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.AddIndex(
            model_name='courseappstatus',
            index=models.Index(fields=['app_id', 'course_key'], name='course_apps_app_id_b3df8c_idx'),
        ),
        migrations.AddConstraint(
            model_name='courseappstatus',
            constraint=models.UniqueConstraint(fields=('app_id', 'course_key'), name='unique_app_config_for_course'),
        ),
    ]
