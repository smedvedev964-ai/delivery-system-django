from django.db import migrations, models
import django.db.models.deletion


def keep_one_address_per_user(apps, schema_editor):
    Address = apps.get_model("accounts", "Address")
    Order = apps.get_model("orders", "Order")
    database = schema_editor.connection.alias

    user_ids = Address.objects.using(database).values_list("user_id", flat=True).distinct()
    for user_id in user_ids.iterator():
        addresses = list(
            Address.objects.using(database)
            .filter(user_id=user_id)
            .order_by("-id")
        )
        if len(addresses) < 2:
            continue
        keeper = addresses[0]
        keeper.is_default = True
        keeper.save(update_fields=["is_default"])
        duplicate_ids = [address.pk for address in addresses[1:]]
        Order.objects.using(database).filter(address_id__in=duplicate_ids).update(
            address_id=keeper.pk
        )
        Address.objects.using(database).filter(pk__in=duplicate_ids).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0001_initial"),
        ("orders", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(keep_one_address_per_user, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="address",
            name="user",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="address",
                to="accounts.user",
            ),
        ),
        migrations.AlterModelOptions(
            name="address",
            options={"ordering": ["city", "street"]},
        ),
    ]
