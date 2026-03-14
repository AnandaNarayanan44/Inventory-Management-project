"""
Django management command to train all ML models.
Run this command to train/retrain all machine learning models.

Usage:
    python manage.py train_ml_models
"""
from django.core.management.base import BaseCommand
import os
import sys

class Command(BaseCommand):
    help = 'Train all machine learning models (expiry, sales, demand)'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting ML model training...\n'))
        
        # Train expiry model
        self.stdout.write('Training expiry risk prediction model...')
        try:
            # Change to ml directory
            ml_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '..', 'ml')
            ml_dir = os.path.abspath(ml_dir)
            
            # Import and run expiry model training
            sys.path.insert(0, ml_dir)
            from expiry_model_train import *
            
            self.stdout.write(self.style.SUCCESS('OK: Expiry model trained successfully!\n'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'ERROR: Error training expiry model: {e}\n'))
        
        # Note about sales and demand models
        self.stdout.write(self.style.WARNING(
            'Note: Sales and demand prediction models are trained automatically\n'
            'when you visit the ML page (/ml/) with sufficient data.\n'
            'They require at least 3 sales records to train properly.\n'
        ))
        
        self.stdout.write(self.style.SUCCESS('\nML model training completed!'))
        self.stdout.write(
            '\nTo use the models:\n'
            '1. Visit /ml/ for sales and demand predictions\n'
            '2. Visit /predict-expiry/ for expiry risk predictions\n'
        ))










