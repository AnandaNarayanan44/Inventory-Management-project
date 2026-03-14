"""
Seed realistic-ish sales data so ML training has enough rows to work.

This project trains the sales prediction model when you visit /ml/ and there are
at least 3 distinct sale dates. On fresh DBs, that often isn't true, which makes
the ML page show "Not enough sales data..." and predictions appear "broken".

Usage:
  python manage.py seed_ml_sales
  python manage.py seed_ml_sales --days 21 --products 5 --force

Safe-by-default:
  - If you already have >= 3 distinct sale dates, this command does nothing
    unless you pass --force.
"""

from __future__ import annotations

import random
from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from InventoryApp.models import Product, Sale, SaleItem, Warehouse


def _d2(x: Decimal | int | float | str) -> Decimal:
    return Decimal(str(x)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


class Command(BaseCommand):
    help = "Seed Sale/SaleItem rows for ML training (sales + demand predictions)."

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=14, help="How many past days to seed (default: 14)")
        parser.add_argument("--products", type=int, default=3, help="How many demo products to ensure exist (default: 3)")
        parser.add_argument("--min-sale-dates", type=int, default=3, help="Minimum distinct sale dates required (default: 3)")
        parser.add_argument("--force", action="store_true", help="Seed even if DB already has enough sale dates")
        parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility (default: 42)")

    @transaction.atomic
    def handle(self, *args, **options):
        days: int = options["days"]
        products_n: int = options["products"]
        min_sale_dates: int = options["min_sale_dates"]
        force: bool = options["force"]
        seed: int = options["seed"]

        random.seed(seed)

        existing_sale_dates = Sale.objects.values_list("sale_date", flat=True).distinct().count()
        if existing_sale_dates >= min_sale_dates and not force:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Already have {existing_sale_dates} distinct sale dates (>= {min_sale_dates}). "
                    "Skipping seeding. Use --force to seed anyway."
                )
            )
            return

        wh, _ = Warehouse.objects.get_or_create(
            name="Main Warehouse",
            defaults={"location": "Demo Location"},
        )

        # Ensure some products exist (only create if there aren't enough).
        existing_products = list(Product.objects.all().order_by("id")[:products_n])
        to_create = max(0, products_n - len(existing_products))
        created = []
        for i in range(to_create):
            idx = len(existing_products) + i + 1
            created.append(
                Product(
                    name=f"Demo Product {idx}",
                    category="Demo",
                    price=_d2(50 + idx * 10),
                    gst=_d2(18),
                    active=True,
                )
            )
        if created:
            Product.objects.bulk_create(created)
        products = list(Product.objects.all().order_by("id")[:products_n])

        today = timezone.now().date()
        start = today - timedelta(days=max(days, 3))

        # Create 1 sale per day with 1-3 items. Keep totals positive and somewhat trending.
        created_sales = 0
        created_items = 0

        for d in range((today - start).days + 1):
            sale_date = start + timedelta(days=d)

            # Avoid colliding invoice_number with existing data.
            invoice_number = f"ML-DEMO-{sale_date:%Y%m%d}-{random.randint(100, 999)}"
            if Sale.objects.filter(invoice_number=invoice_number).exists():
                # Extremely unlikely, but keep going.
                continue

            items_count = random.randint(1, min(3, len(products)))
            chosen = random.sample(products, k=items_count)

            subtotal = Decimal("0.00")
            tax = Decimal("0.00")

            sale = Sale.objects.create(
                invoice_number=invoice_number,
                customer_name="Demo Customer",
                staff_name="Demo Staff",
                sale_date=sale_date,
                notes="Seeded demo sale for ML training",
                subtotal=_d2(0),
                tax_amount=_d2(0),
                total_amount=_d2(0),
            )

            # Mild upward trend + weekly seasonality.
            trend_multiplier = Decimal("1.00") + (Decimal(d) / Decimal(max(1, days))) * Decimal("0.25")
            weekday_multiplier = Decimal("1.10") if sale_date.weekday() in (4, 5) else Decimal("1.00")  # Fri/Sat
            base_qty = int((trend_multiplier * weekday_multiplier * Decimal("2.5")).to_integral_value())

            for p in chosen:
                qty = max(1, base_qty + random.randint(-1, 3))
                unit_price = _d2(p.price)
                gst_percent = _d2(getattr(p, "gst", 0) or 0)

                line_subtotal = _d2(Decimal(qty) * unit_price)
                line_tax = _d2(line_subtotal * (gst_percent / Decimal("100")))
                line_total = _d2(line_subtotal + line_tax)

                SaleItem.objects.create(
                    sale=sale,
                    product=p,
                    warehouse=wh,
                    quantity=qty,
                    unit_price=unit_price,
                    gst_percent=gst_percent,
                    line_total=line_total,
                )
                created_items += 1
                subtotal += line_subtotal
                tax += line_tax

            sale.subtotal = _d2(subtotal)
            sale.tax_amount = _d2(tax)
            sale.total_amount = _d2(subtotal + tax)
            sale.save(update_fields=["subtotal", "tax_amount", "total_amount"])
            created_sales += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {created_sales} sales and {created_items} sale items "
                f"from {start} to {today} (Warehouse={wh.name})."
            )
        )


