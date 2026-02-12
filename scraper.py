import asyncio
import os
import pandas as pd
from datetime import datetime
from playwright.async_api import async_playwright

# --- CONFIGURATION ---
URL = "https://www.kenousa.com/games/GVR/Green/draws.php"
CSV_FILE = "results.csv"

async def run():
    async with async_playwright() as p:
        # Launch browser (headless=True means it runs without a visible window, efficient for servers)
        browser = await p.chromium.launch(headless=True)
        
        # Create a context with a realistic User-Agent to avoid detection
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            viewport={"width": 1280, "height": 720}
        )
        
        page = await context.new_page()
        
        print(f"Loading {URL}...")
        try:
            # Go to the page and wait until the network is idle (page is fully loaded)
            await page.goto(URL, wait_until="networkidle", timeout=60000)
        except Exception as e:
            print(f"Error loading page: {e}")
            await browser.close()
            return

        # --- SCRAPING LOGIC ---
        # Find all containers that look like a game row
        # We look for divs with class 'col-xs-12' that contain a '.game-num'
        rows = page.locator("div.col-xs-12:has(.game-num)")
        count = await rows.count()
        print(f"Found {count} potential draws.")

        new_data = []

        for i in range(count):
            row = rows.nth(i)
            
            try:
                # 1. Extract Game ID
                # The ID is inside an anchor tag <a> inside .game-num
                game_id_el = row.locator(".game-num a")
                game_id = await game_id_el.inner_text()
                game_id = game_id.strip()

                # 2. Extract Timestamp
                time_el = row.locator(".game-date")
                timestamp = await time_el.inner_text()
                timestamp = timestamp.strip()

                # 3. Extract Numbers
                # The numbers are in .game-draw, separated by spaces
                draw_el = row.locator(".game-draw")
                raw_numbers = await draw_el.inner_text()
                
                # Clean up the numbers: replace non-breaking spaces with normal spaces, then split
                # This turns "22  18  70" into ['22', '18', '70']
                numbers_list = [num for num in raw_numbers.replace('\u00a0', ' ').split(' ') if num.strip()]
                numbers_str = "-".join(numbers_list) # Format as 1-2-3-4

                # Validate we actually got data
                if game_id and numbers_list:
                    print(f"Scraped Game {game_id}: {numbers_str}")
                    new_data.append({
                        "Game ID": game_id,
                        "Timestamp": timestamp,
                        "Numbers": numbers_str,
                        "Scraped At": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
            except Exception as e:
                print(f"Skipping a row due to error: {e}")
                continue

        await browser.close()

        # --- SAVING DATA ---
        if not new_data:
            print("No data scraped.")
            return

        df_new = pd.DataFrame(new_data)

        # Check if CSV exists to handle deduplication
        if os.path.exists(CSV_FILE):
            try:
                df_existing = pd.read_csv(CSV_FILE)
                # Filter out rows where 'Game ID' is already in the existing file
                # We convert to string to ensure types match
                existing_ids = df_existing["Game ID"].astype(str).tolist()
                df_final = df_new[~df_new["Game ID"].astype(str).isin(existing_ids)]
                
                if not df_final.empty:
                    # Append strictly new rows without writing the header again
                    df_final.to_csv(CSV_FILE, mode='a', header=False, index=False)
                    print(f"Added {len(df_final)} new draws.")
                else:
                    print("No new draws found. Data is up to date.")
            except pd.errors.EmptyDataError:
                # If file exists but is empty, write fresh
                df_new.to_csv(CSV_FILE, mode='w', header=True, index=False)
                print(f"File was empty. Wrote {len(df_new)} draws.")
        else:
            # File doesn't exist, create it
            df_new.to_csv(CSV_FILE, mode='w', header=True, index=False)
            print(f"Created new file with {len(df_new)} draws.")

# Run the async function
asyncio.run(run())
