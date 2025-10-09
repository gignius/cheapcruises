import asyncio
from database_async import AsyncSessionLocal, CruiseDealRepository
import time

async def check_progress():
    while True:
        async with AsyncSessionLocal() as session:
            repo = CruiseDealRepository(session)
            deals = await repo.get_all()
            
            by_line = {}
            for d in deals:
                by_line[d.cruise_line] = by_line.get(d.cruise_line, 0) + 1
            
            print(f"\n[{time.strftime('%H:%M:%S')}] Progress Update:")
            print(f"  Total deals: {len(deals)}")
            print(f"  Cruise lines: {len(by_line)}")
            
            if len(deals) > 0:
                print(f"\n  Top 5 cruise lines:")
                for line, count in sorted(by_line.items(), key=lambda x: -x[1])[:5]:
                    print(f"    {line}: {count}")
            
            # Check if scraper is still running
            import subprocess
            result = subprocess.run(['powershell', 'Get-Process python -ErrorAction SilentlyContinue | Where-Object {$_.Path -like "*Cheapcruises*"}'], 
                                  capture_output=True, text=True)
            
            if not result.stdout.strip():
                print("\n  Scraper appears to have finished!")
                break
            
            print("\n  Waiting 30 seconds...")
            await asyncio.sleep(30)

asyncio.run(check_progress())

