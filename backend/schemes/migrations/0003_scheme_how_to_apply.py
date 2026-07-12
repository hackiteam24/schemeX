from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('schemes', '0002_scheme_bpl_required_scheme_caste_categories_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='scheme',
            name='how_to_apply',
            field=models.TextField(blank=True, help_text='Steps / process to apply for this scheme.'),
        ),
    ]