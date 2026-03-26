from django.db import migrations


def set_q3_metadata(apps, schema_editor):
    Question = apps.get_model('users', 'Question')
    try:
        q = Question.objects.filter(id='q3').first()
        if not q:
            return
        # Only update when fields are empty to avoid overwriting custom edits
        changed = False
        if not q.options:
            q.options = [
                "SDE (Seller's Discretionary Earnings)",
                "EBITDA"
            ]
            changed = True
        if not q.examples:
            q.examples = [
                "$250K - $500K",
                "$500K - $1M",
                "$1M - $2M",
                "$2M - $5M",
                "$5M+"
            ]
            changed = True
        extra = q.extra or {}
        if not extra.get('radioTitle'):
            extra['radioTitle'] = 'Select financial metric:'
            changed = True
        if not extra.get('textTitle1'):
            extra['textTitle1'] = 'Minimum Earnings'
            changed = True
        if not extra.get('textTitle2'):
            extra['textTitle2'] = 'Maximum Earnings'
            changed = True
        if changed:
            q.extra = extra
            q.save()
    except Exception:
        # best-effort; don't block migrations on data issues
        pass


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0032_add_question_subtitle'),
    ]

    operations = [
        migrations.RunPython(set_q3_metadata, reverse_code=migrations.RunPython.noop),
    ]
