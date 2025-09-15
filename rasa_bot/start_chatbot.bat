@echo off
echo ================================================
echo 🎭 Rasa AI Stylist Chatbot Startup (Developer Edition)
echo ================================================
echo.

echo Setting up Rasa Developer Edition License...
set RASA_LICENSE_KEY=eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiI1MDcwNGU3MC00MmUyLTQwZDctYWFlNS1mNmU0YmZkNDBmZWIiLCJpYXQiOjE3NTc4NDQ5NzcsIm5iZiI6MTc1Nzg0NDk3Mywic2NvcGUiOiJyYXNhOnBybyByYXNhOnBybzpjaGFtcGlvbiByYXNhOnZvaWNlIiwiZXhwIjoxODUyNTM5MzczLCJlbWFpbCI6InNpbndhaTAwMDBAZ21haWwuY29tIiwiY29tcGFueSI6IlJhc2EgQ2hhbXBpb25zIn0.F_6yQoo9XSrBgNG2mmuclIToFwJQ8Ykmfj3sddkQMDd-tcZtd0NsOuz8RM9R8WEGgsEMJBFxOPuQscIKolaJPSlkGYUudoxl4VgIqOwp4eRK6I8347fsaF8NhKALdea8HikOhu2MVwMMJcUNMpJT9LUvN-WfUZf6Vme3WrsCI82NuwkYM65L6YWQAUrSQyCM-HqiJiatitKhXoERJKNnqtPPtlTQwhV8Swi9R5uGWNAjExFwpgqx4Tth3GQYkrG3LzBmxVg0LZRi8hFWMyMcE6BPg3jVx6-RhwESdxWRFsodGbvMCCej3ZvMk6T6GZRcZBhEXb8mw4lM35U6jWBPLw

echo Starting Rasa Server on port 5005...
start "Rasa Server" cmd /k "rasa run --enable-api --cors * --port 5005"

echo Waiting 10 seconds for Rasa server to start...
timeout /t 10 /nobreak > nul

echo Starting Action Server on port 5055...
start "Rasa Action Server" cmd /k "rasa run actions --port 5055"

echo.
echo ================================================
echo 🎉 Rasa AI Stylist Chatbot is starting up!
echo ================================================
echo.
echo 📡 Services:
echo    • Rasa Server: http://localhost:5005
echo    • Action Server: http://localhost:5055
echo    • Django Chat: http://localhost:8000/stylist-chat/
echo.
echo 💡 Keep these terminal windows open while using the chatbot.
echo    Press any key to exit this startup script...
pause > nul
