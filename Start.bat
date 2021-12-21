call venv\Scripts\activate

:MAIN
python bot.py
ECHO "Server crashed. Restarting in 5 seconds."
timeout 5
GOTO MAIN