# accounts/migrations/0002_change_profile_picture.py
from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='userprofile',
            name='profile_picture',
        ),
        migrations.AddField(
            model_name='userprofile',
            name='profile_picture',
            field=models.TextField(blank=True, help_text='Base64 encoded profile picture', null=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='profile_picture_content_type',
            field=models.CharField(blank=True, help_text='MIME type of the profile picture', max_length=50, null=True),
        ),
    ]