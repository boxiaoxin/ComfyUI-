Set objFSO = CreateObject("Scripting.FileSystemObject")
Set objShell = CreateObject("WScript.Shell")

' Get script directory
strScriptPath = objFSO.GetParentFolderName(WScript.ScriptFullName)

' Change to script directory
objShell.CurrentDirectory = strScriptPath

' Run the batch file silently
objShell.Run "silent_launcher.bat", 0, False

WScript.Quit
