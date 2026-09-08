# Satisfactory Google Drive Sharing

Desktop application for synchronization of **Satisfactory** save files with your friends via **Google Drive**.

## Requirements

If you want to run the python code by your own, I suggest to use this Python version:

`Python 3.13.9`

otherwise you can just download the release .exe file and roll.

### How to start the application via Python

Run: 
```powershell
pip install -r requirements.txt

python main.py
```

### How to create .exe file on your own

You can use the following PowerShell scripts:

Build exe: `.\build.ps1`

Clear project folder: `.\clear.ps1`

## Shared google folder creation

Create folder in your Google Drive, set it as shared - via link and set assess as `Limited - Only me`.

Copy the link:

`https://drive.google.com/drive/folders/<SECRET-1>?usp=sharing`

You will need the `<SECRET-1>` value later

## Google App Script creation

Create new project in Google Apps Script (script.google.com).

Use the code from file `app.gs`. Next steps:

1. Save the project

2. Under **Project settings**, set `<SECRET-1>` as value for property `SAVE_FOLDER_ID`

3. Generate tokens for users and send it to them.

4. Click on Deploy

5. Set **type**: `Web app`

6. Set **Execute as**: `Me`

7. Set **Who has access**: `Anyone`.

8. Click on Deploy button.

9. Copy the app URL.

`https://script.google.com/macros/s/<SECRET-2>/exec`

You will need to share this URL with your friends. All of you will need to use in the the Sync app.

