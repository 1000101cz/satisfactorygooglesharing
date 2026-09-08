# Satisfactory Google Drive Sharing

Desktop application for synchronization of **Satisfactory** save files with your friends via **Google Drive**.

## Requirements

If you want to run the python code by your own, I suggest to use this Python version:

`Python 3.13.9`

otherwise you can just download the release .exe file and roll.

### How to start the application via Python

Run: `python main.py`

### How to create .exe file on your own

You can use the following PowerShell scripts:

Build exe: `.\build.ps1`

Clear project folder: `.\clear.ps1`

## Shared google folder creation

Create folder in your Google Drive, set it as shared - via link and allow everyone with the link to read and write in there.

Copy the link:

`https://drive.google.com/drive/folders/<SECRET-1>?usp=sharing`

You will need the `<SECRET-1>` value later

## Google App Script creation

Create new project in Google Apps Script (script.google.com).

Use this code:

```js
function doPost(e) {
  try {
    // Google Drive shared folder's ID
    var folderId = "<SECRET-1>"; 
    var folder = DriveApp.getFolderById(folderId);
    
    var data = JSON.parse(e.postData.contents);
    var fileName = data.fileName;
    var fileData = Utilities.base64Decode(data.fileContent);
    var blob = Utilities.newBlob(fileData, data.mimeType, fileName);
    
    // File creation
    var file = folder.createFile(blob);
    
    return ContentService.createTextOutput(JSON.stringify({
      "status": "success",
      "fileId": file.getId()
    })).setMimeType(ContentService.MimeType.JSON);
    
  } catch (error) {
    return ContentService.createTextOutput(JSON.stringify({
      "status": "error",
      "message": error.toString()
    })).setMimeType(ContentService.MimeType.JSON);
  }
}

function doGet(e) {
  try {
    var folderId = "<SECRET-1>"; 
    
    if (e && e.parameter && e.parameter.fileId) {
      var file = DriveApp.getFileById(e.parameter.fileId);
      var bytes = file.getBlob().getBytes();
      var base64Data = Utilities.base64Encode(bytes);
      
      return ContentService.createTextOutput(JSON.stringify({
        "status": "success",
        "fileName": file.getName(),
        "updated": file.getLastUpdated().toISOString(),
        "fileContent": base64Data
      })).setMimeType(ContentService.MimeType.JSON);
    }
    
    var folder = DriveApp.getFolderById(folderId);
    var files = folder.getFiles();
    var fileList = [];
    
    while (files.hasNext()) {
      var f = files.next();
      fileList.push({
        "id": f.getId(),
        "name": f.getName(),
        "size": f.getSize(),
        "updated": f.getLastUpdated().toISOString()
      });
    }
    
    return ContentService.createTextOutput(JSON.stringify({
      "status": "success",
      "files": fileList
    })).setMimeType(ContentService.MimeType.JSON);
    
  } catch (error) {
    return ContentService.createTextOutput(JSON.stringify({
      "status": "error",
      "message": error.toString()
    })).setMimeType(ContentService.MimeType.JSON);
  }
}
```

Replace the `<SECRET-1>` value with the one from Google Drive folder share link. Now:

1. Save the project

2. Click on Deploy

3. Set **type**: `Web app`

4. Set **Execute as**: `Me`

5. Set **Who has access**: `Anyone`.

6. Click on Deploy button.

Copy the app URL.

`https://script.google.com/macros/s/<SECRET-2>/exec`

You will need to share `<SECRET-2>` value with your friend. All of you will need to use in the the Sync app.

