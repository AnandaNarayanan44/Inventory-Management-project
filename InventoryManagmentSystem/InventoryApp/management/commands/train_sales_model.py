"""
Train and persist the sales prediction model (same logic used on /ml/ page),
without needing to visit the page.

Usage:
  python manage.py train_sales_model
"""

from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db.models import Sum
from django.conf import settings


class Command(BaseCommand):
    help = "Train the sales linear regression model and save it to media/ml_models/."

    def add_arguments(self, parser):
        parser.add_argument("--min-sale-dates", type=int, default=3, help="Minimum distinct sale dates required (default: 3)")

    def handle(self, *args, **options):
        # Local imports so Django is fully ready.
        import numpy as np
        from sklearn.linear_model import LinearRegression
        import joblib

        from InventoryApp.models import Sale, MLModelArtifact

        min_sale_dates: int = options["min_sale_dates"]
        model_name = "sales_linear_regression"

        sales = (
            Sale.objects.values("sale_date")
            .annotate(total=Sum("total_amount"))
            .order_by("sale_date")
        )
        sales_list = list(sales)

        if len(sales_list) < min_sale_dates:
            self.stdout.write(
                self.style.ERROR(
                    f"Not enough sales data to train. Need at least {min_sale_dates} distinct sale dates, "
                    f"found {len(sales_list)}. Run: python manage.py seed_ml_sales"
                )
            )
            return

        # Prepare data
        days = np.array([(row["sale_date"] - sales_list[0]["sale_date"]).days for row in sales_list]).reshape(-1, 1)
        totals = np.array([float(row["total"]) for row in sales_list])

        # Remove outliers (values more than 3 standard deviations from mean)
        mean_total = np.mean(totals)
        std_total = np.std(totals)
        if std_total > 0:
            mask = np.abs(totals - mean_total) <= 3 * std_total
            days = days[mask.flatten()]
            totals = totals[mask]

        if len(totals) < min_sale_dates:
            self.stdout.write(
                self.style.ERROR(
                    f"Not enough valid sales data after filtering. Need at least {min_sale_dates} sale dates."
                )
            )
            return

        reg = LinearRegression()
        reg.fit(days, totals)
        r2_score = reg.score(days, totals)

        model_dir = settings.MEDIA_ROOT / "ml_models"
        model_dir.mkdir(parents=True, exist_ok=True)
        model_path = model_dir / f"{model_name}.pkl"
        joblib.dump(reg, model_path)

        MLModelArtifact.objects.update_or_create(
            name=model_name,
            defaults={
                "model_file": f"ml_models/{model_name}.pkl",
                "trained_on_rows": len(totals),
                "notes": f"Linear regression on daily totals. R2={r2_score:.3f}",
            },
        )

        self.stdout.write(self.style.SUCCESS(f"OK: Trained and saved {model_name} to {model_path}"))
        self.stdout.write(self.style.SUCCESS(f"  Rows used: {len(totals)} | R2: {r2_score:.3f}"))


