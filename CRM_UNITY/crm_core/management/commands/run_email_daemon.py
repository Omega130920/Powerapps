# management/commands/run_email_daemon.py
import time
from django.core.management.base import BaseCommand
from django.core.management import call_command

class Command(BaseCommand):
    help = "Continuous loop daemon for Outlook email sync"

    def handle(self, *args, **options):
        self.stdout.write("Starting email ingestion daemon...")
        while True:
            try:
                call_command('sync_outlook_emails')
            except Exception as e:
                self.stderr.write(f"Daemon sync error: {e}")
            time.sleep(60)  # Wait 60 seconds between runs