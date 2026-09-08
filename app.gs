/**
 * Satisfactory Google Sharing - secure Apps Script backend
 *
 * REQUIRED SCRIPT PROPERTIES:
 *
 * SAVE_FOLDER_ID
 * TOKEN_HASH
 *
 * The actual token is NOT stored in this script.
 *
 * Deploy:
 *   Execute as: Me
 *   Who has access: Anyone
 *
 * IMPORTANT:
 * The Google Drive folder itself should NOT be public.
 */

/**
 * Configuration
 */
const MAX_FILE_SIZE = 100 * 1024 * 1024; // 100 MB
const MAX_FILENAME_LENGTH = 200;


/**
 * Handle all API requests.
 *
 * Supported operations:
 *
 * UPLOAD:
 * {
 *   "token": "...",
 *   "fileName": "save.sav",
 *   "fileContent": "base64..."
 * }
 *
 * LIST:
 * {
 *   "token": "...",
 *   "action": "list"
 * }
 *
 * DOWNLOAD:
 * {
 *   "token": "...",
 *   "action": "download",
 *   "fileId": "..."
 * }
 */
function doPost(e) {
  try {
    if (!e || !e.postData || !e.postData.contents) {
      return errorResponse("Invalid request");
    }

    const data = JSON.parse(e.postData.contents);

    // Authenticate first.
    if (!isValidToken(data.token)) {
      return errorResponse("Unauthorized");
    }

    /**
     * ================================================================
     * DOWNLOAD
     * ================================================================
     */
    if (data.action === "download") {
      const fileId = data.fileId;

      if (!fileId || typeof fileId !== "string") {
        return errorResponse("Missing file ID");
      }

      const folder = getSaveFolder();

      let file;

      try {
        file = DriveApp.getFileById(fileId);
      } catch (error) {
        return errorResponse("File not found");
      }

      if (!fileBelongsToFolder(file, folder)) {
        return errorResponse("File not found");
      }

      if (!isValidSaveFilename(file.getName())) {
        return errorResponse("Invalid file");
      }

      const bytes = file.getBlob().getBytes();

      if (bytes.length > MAX_FILE_SIZE) {
        return errorResponse("File too large");
      }

      const base64Data = Utilities.base64Encode(bytes);

      return successResponse({
        status: "success",
        fileName: file.getName(),
        updated: file.getLastUpdated().toISOString(),
        fileContent: base64Data
      });
    }


    /**
     * ================================================================
     * LIST FILES
     * ================================================================
     */
    if (data.action === "list") {
      const folder = getSaveFolder();
      const files = folder.getFiles();
      const fileList = [];

      while (files.hasNext()) {
        const file = files.next();

        // Never expose anything except .sav files.
        if (!isValidSaveFilename(file.getName())) {
          continue;
        }

        fileList.push({
          id: file.getId(),
          name: file.getName(),
          size: file.getSize(),
          updated: file.getLastUpdated().toISOString()
        });
      }

      return successResponse({
        status: "success",
        files: fileList
      });
    }


    /**
     * ================================================================
     * UPLOAD
     * ================================================================
     *
     * This remains compatible with the existing google_drive.py.
     */
    const fileName = data.fileName;
    const fileContent = data.fileContent;

    // Only allow Satisfactory save files.
    if (!isValidSaveFilename(fileName)) {
      return errorResponse("Invalid file name");
    }

    if (!fileContent || typeof fileContent !== "string") {
      return errorResponse("Missing file content");
    }

    // Base64 is larger than the original file.
    if (fileContent.length > MAX_FILE_SIZE * 1.4) {
      return errorResponse("File too large");
    }

    const fileData = Utilities.base64Decode(fileContent);

    if (fileData.length > MAX_FILE_SIZE) {
      return errorResponse("File too large");
    }

    const folder = getSaveFolder();

    const blob = Utilities.newBlob(
      fileData,
      "application/octet-stream",
      fileName
    );

    /**
     * Remove an existing save with the same name.
     *
     * This prevents every sync from creating another copy.
     */
    const existingFiles = folder.getFilesByName(fileName);

    while (existingFiles.hasNext()) {
      const existingFile = existingFiles.next();

      // Extra safety: make sure this is actually in our folder.
      if (existingFile.getParents().hasNext()) {
        existingFile.setTrashed(true);
      }
    }

    const file = folder.createFile(blob);

    return successResponse({
      status: "success",
      fileId: file.getId()
    });

  } catch (error) {
    console.error(error);

    // Do NOT expose internal error details.
    return errorResponse("Internal server error");
  }
}


/**
 * Authenticate the supplied token.
 *
 * The real token is NEVER stored here.
 * Only its SHA-256 hash is stored in Script Properties.
 */
function isValidToken(token) {
  if (!token || typeof token !== "string") {
    return false;
  }

  const suppliedHash = sha256(token);

  const properties =
    PropertiesService.getScriptProperties().getProperties();

  for (const propertyName in properties) {
    if (!propertyName.endsWith("_HASH")) {
      continue;
    }

    if (!propertyName.startsWith("TOKEN_")) {
      continue;
    }

    const storedHash = properties[propertyName];

    if (constantTimeEquals(storedHash, suppliedHash)) {
      return true;
    }
  }

  return false;
}


/**
 * Return the configured private Drive folder.
 */
function getSaveFolder() {
  const folderId = PropertiesService
    .getScriptProperties()
    .getProperty("SAVE_FOLDER_ID");

  if (!folderId) {
    throw new Error("SAVE_FOLDER_ID is not configured");
  }

  return DriveApp.getFolderById(folderId);
}


/**
 * Make sure a file is actually contained in our configured folder.
 *
 * This prevents someone from supplying an arbitrary Google Drive
 * file ID and using our Apps Script as a Drive file reader.
 */
function fileBelongsToFolder(file, folder) {
  const parents = file.getParents();

  while (parents.hasNext()) {
    const parent = parents.next();

    if (parent.getId() === folder.getId()) {
      return true;
    }
  }

  return false;
}


/**
 * Strict Satisfactory save filename validation.
 */
function isValidSaveFilename(fileName) {
  if (!fileName || typeof fileName !== "string") {
    return false;
  }

  if (fileName.length > MAX_FILENAME_LENGTH) {
    return false;
  }

  /*
   * Only allow:
   *
   * letters
   * numbers
   * spaces
   * underscores
   * hyphens
   * dots
   *
   * and require .sav at the end.
   */
  return /^[A-Za-z0-9_.-]+\.sav$/i.test(fileName);
}


/**
 * SHA-256.
 */
function sha256(value) {
  const digest = Utilities.computeDigest(
    Utilities.DigestAlgorithm.SHA_256,
    value,
    Utilities.Charset.UTF_8
  );

  return digest
    .map(function(byte) {
      const unsignedByte = byte < 0 ? byte + 256 : byte;
      return ("0" + unsignedByte.toString(16)).slice(-2);
    })
    .join("");
}


/**
 * Constant-time string comparison.
 */
function constantTimeEquals(a, b) {
  if (typeof a !== "string" || typeof b !== "string") {
    return false;
  }

  if (a.length !== b.length) {
    return false;
  }

  let result = 0;

  for (let i = 0; i < a.length; i++) {
    result |= a.charCodeAt(i) ^ b.charCodeAt(i);
  }

  return result === 0;
}


/**
 * Standard successful JSON response.
 */
function successResponse(data) {
  return ContentService
    .createTextOutput(JSON.stringify(data))
    .setMimeType(ContentService.MimeType.JSON);
}


/**
 * Standard error response.
 *
 * We intentionally don't return exception details.
 */
function errorResponse(message) {
  return ContentService
    .createTextOutput(JSON.stringify({
      status: "error",
      message: message
    }))
    .setMimeType(ContentService.MimeType.JSON);
}


/**
 * ================================================================
 * SETUP FUNCTIONS
 * ================================================================
 *
 * Run these manually from the Apps Script editor.
 *
 * Do NOT put the generated token in this source code.
 */


/**
 * Generate a new random token for a client and save only its hash.
 *
 * Example:
 *
 *     generateToken("alice")
 *
 * This creates/replaces:
 *
 *     TOKEN_ALICE_HASH
 *
 * The plaintext token is printed to the execution log.
 *
 * Give that plaintext token to Alice.
 *
 * IMPORTANT:
 * Running this again for the same client INVALIDATES
 * the previous token.
 */
function generateToken(client) {

  // Validate client ID.
  if (!client || typeof client !== "string") {
    throw new Error(
      'You must provide a client ID, e.g. generateToken("alice")'
    );
  }

  client = client.trim();

  if (!/^[A-Za-z0-9_-]{1,50}$/.test(client)) {
    throw new Error(
      "Invalid client ID. Use only letters, numbers, underscores and hyphens."
    );
  }

  // Generate a cryptographically random, high-entropy token.
  const token =
    Utilities.getUuid().replace(/-/g, "") +
    Utilities.getUuid().replace(/-/g, "") +
    Utilities.getUuid().replace(/-/g, "");

  // Store ONLY the hash.
  const hash = sha256(token);

  const propertyName =
    "TOKEN_" + client.toUpperCase() + "_HASH";

  PropertiesService
    .getScriptProperties()
    .setProperty(propertyName, hash);

  // Show the plaintext token to the administrator.
  console.log("========================================");
  console.log("NEW GOOGLE APP TOKEN");
  console.log("Client: " + client);
  console.log("Property: " + propertyName);
  console.log("");
  console.log(token);
  console.log("========================================");
  console.log(
    "Give this token to the client. " +
    "It will NOT be stored in Apps Script."
  );

  return token;
}


/**
 * Configure the private Drive folder.
 *
 * Run this manually once:
 *
 * setSaveFolder("YOUR_GOOGLE_DRIVE_FOLDER_ID")
 */
function setSaveFolder(folderId) {
  if (!folderId || typeof folderId !== "string") {
    throw new Error("Invalid folder ID");
  }

  // Verify that the folder exists and is accessible.
  DriveApp.getFolderById(folderId);

  PropertiesService
    .getScriptProperties()
    .setProperty("SAVE_FOLDER_ID", folderId);

  console.log("SAVE_FOLDER_ID configured.");
}