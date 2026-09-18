@echo off
cd /d "%~dp0"
"C:\Users\yugpa\AppData\Local\Python\pythoncore-3.14-64\python.exe" -m app.scraper.run_all_scrapers --window T+15 >> logs\sweep_t15.log 2>&1
