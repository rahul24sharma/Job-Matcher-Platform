# test_job_scraping.py

from app.db.session import SessionLocal
from app.services.job_scraper import JobScraperService

# Test direct scraping
db = SessionLocal()
scraper = JobScraperService(db)

print("Testing Remotive API...")
try:
    count = scraper.scrape_remotive_jobs(limit=5)  # Just 5 jobs for testing
    print(f"✅ Successfully scraped {count} jobs from Remotive!")
except Exception as e:
    print(f"❌ Error: {e}")

db.close()