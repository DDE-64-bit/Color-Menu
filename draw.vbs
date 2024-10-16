Set objShell = CreateObject("WScript.Shell")
' Vervang hieronder de paden naar de Python-interpreter en het script
objShell.Run "pythonw.exe ""./draw.py""", 0, False
