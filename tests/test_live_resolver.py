from backend.app.discovery.url_resolver import resolve_ats_urls

urls = {
    "Remotive": "https://remotive.com/remote-jobs/data/senior-data-scientist-2091129",
    "Arbeitnow": "https://www.arbeitnow.com/jobs/companies/almedia/junior-software-engineer-data-berlin-75989",
}

for source, url in urls.items():
    print(f"\n--- {source} ---")
    ats_urls = resolve_ats_urls(url)
    print("ATS URLs found:", ats_urls)
