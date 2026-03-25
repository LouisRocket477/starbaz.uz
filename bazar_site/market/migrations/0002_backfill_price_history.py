# Generated manually for backfilling ListingPriceHistory

from django.db import migrations


def backfill_price_history(apps, schema_editor):
    Listing = apps.get_model("market", "Listing")
    ListingPriceHistory = apps.get_model("market", "ListingPriceHistory")

    for listing in Listing.objects.all():
        if not ListingPriceHistory.objects.filter(listing=listing).exists():
            price = listing.original_price or listing.price
            if price is not None:
                ListingPriceHistory.objects.create(
                    listing=listing,
                    price=price,
                )


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("market", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(backfill_price_history, noop),
    ]
