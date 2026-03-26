Как запускать сайт одной командой

1) Запуск:
   - Открой PowerShell
   - Выполни:
       powershell -ExecutionPolicy Bypass -File "C:\Users\Louis\Documents\01\bazar_site\tools\start_server.ps1"

2) Остановка:
       powershell -ExecutionPolicy Bypass -File "C:\Users\Louis\Documents\01\bazar_site\tools\stop_server.ps1"

Логи:
  C:\Users\Louis\Documents\01\bazar_site\tools\run-logs\
  - django.log
  - tunnel.log (в нём будет ссылка https://...trycloudflare.com)
  - postgres.log

Важно:
  - Перед запуском убедись, что существует:
      C:\Users\Louis\Desktop\pgsql\bin\pg_ctl.exe
      C:\Users\Louis\Documents\pgdata\
      C:\Users\Louis\Documents\01\tools\cloudflared.exe
