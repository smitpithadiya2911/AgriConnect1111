from django.apps import apps

for app_name in ['accounts', 'marketplace']:
    app = apps.get_app_config(app_name)
    for model in app.get_models():
        print(f"=== Model: {model.__name__} (table: {model._meta.db_table}) ===")
        for field in model._meta.fields:
            print(f"  {field.name} | {field.get_internal_type()} | null={field.null} | pk={field.primary_key}")
