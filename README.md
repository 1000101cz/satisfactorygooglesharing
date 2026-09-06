## Shared google folder creation

Create folder in your google Drive, set it as shared - via link and allow everyone with the link to read and write in there.

Copy the link

`https://drive.google.com/drive/folders/<SECRET-1>?usp=sharing`

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
```

Save the project

Click on Deploy

Set `Web app` as type.

Set `Execute as` as Me.

Set `Who has access` as Anyone.

Click on Deploy button.

Copy the app URL.

`https://script.google.com/macros/s/<SECRET-2>/exec`

