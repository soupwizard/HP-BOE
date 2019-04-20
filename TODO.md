To Do

Config:
- Command line arguments (url, which item types to parse)
- Config file?

Item Data:
- Parse item description (model column) for sub-items (model, OS, cpu, memory, hd, etc)
- Better error handling when page data doesn't match what we expect (when using bs4)

Output:
- Export directly to .csv file
- Export directly to .xlsx file, with sheets for each item type
- Store in DB for a web front end to use?

Portability:
- Ensure works with windows, mac, linux

Resilience:
- If error parsing, warn on that row but keep processing
- In general, warn if you can keep valid data and continue
