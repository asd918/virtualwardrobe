@echo off
echo Starting Rasa AI Stylist Chatbot...
echo.

echo Starting Rasa Server on port 5005...
start "Rasa Server" cmd /k "rasa run --enable-api --cors * --port 5005"

echo Waiting 3 seconds for Rasa server to start...
timeout /t 3 /nobreak > nul

echo Starting Action Server on port 5055...
start "Rasa Action Server" cmd /k "rasa run actions --port 5055"

echo.
echo Rasa services are starting...
echo - Rasa Server: http://localhost:5005
echo - Action Server: http://localhost:5055
echo.
echo Keep these terminal windows open while using the chatbot.
echo Press any key to exit this startup script...
pause > nul 