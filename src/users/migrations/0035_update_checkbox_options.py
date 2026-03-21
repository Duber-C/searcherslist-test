from django.db import migrations


def add_generic_subtitles(apps, schema_editor):
    Question = apps.get_model('users', 'Question')
    CHECK_TYPES = ['checkbox', 'multiselect', 'checkbox_group']
    for q in Question.objects.filter(question_type__in=CHECK_TYPES):
        try:
            opts = q.options or []
            changed = False
            new_opts = []
            for o in opts:
                # Only operate on simple string options
                if isinstance(o, str):
                    parts = [p.strip() for p in o.split(',')]
                    if len(parts) == 1:
                        # append a generic subtitle
                        new_opts.append(f"{parts[0]}, generic subtitle")
                        changed = True
                    else:
                        new_opts.append(o)
                else:
                    new_opts.append(o)

            if changed:
                q.options = new_opts
                q.save(update_fields=['options'])
        except Exception:
            # don't fail the whole migration for a single bad row
            continue


def remove_generic_subtitles(apps, schema_editor):
    Question = apps.get_model('users', 'Question')
    CHECK_TYPES = ['checkbox', 'multiselect', 'checkbox_group']
    for q in Question.objects.filter(question_type__in=CHECK_TYPES):
        try:
            opts = q.options or []
            new_opts = []
            changed = False
            for o in opts:
                if isinstance(o, str):
                    parts = [p.strip() for p in o.split(',')]
                    # strip trailing generic subtitle if present
                    if len(parts) > 1 and parts[-1].lower() == 'generic subtitle':
                        new_opts.append(', '.join(parts[:-1]))
                        changed = True
                    else:
                        new_opts.append(o)
                else:
                    new_opts.append(o)
            if changed:
                q.options = new_opts
                q.save(update_fields=['options'])
        except Exception:
            continue


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0034_add_questionnaire_answers'),
    ]

    operations = [
        migrations.RunPython(add_generic_subtitles, remove_generic_subtitles),
    ]
