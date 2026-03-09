@echo off
cd /d D:\project\CIMS
git add -A
git commit -m "feat: update key metrics, market config and add crypto utils

- Remove profit_to_op, roe_waa, roe_dt from key metrics
- Add market priority: HK, US, IN, CH, JP
- Add password encryption for MySQL
- Add crypto_utils module for secure storage"
