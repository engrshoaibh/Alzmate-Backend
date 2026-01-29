# Firebase Credentials Setup Guide

This guide explains how to configure Firebase credentials for the AlzMate Backend API.

## Overview

The application supports three methods for providing Firebase credentials (in priority order):

1. **FIREBASE_SERVICE_ACCOUNT_JSON_B64** (Recommended) - Base64-encoded service account JSON
2. **FIREBASE_SERVICE_ACCOUNT_JSON** - Direct JSON string of service account
3. **FIREBASE_CREDENTIALS_PATH** - Path to a service account JSON file

## Method 1: Base64-encoded JSON (Recommended)

This is the recommended method for cloud platforms (Render, Heroku, etc.) as it avoids file system dependencies.

### Steps:

1. **Get your Firebase service account key:**
   - Go to [Firebase Console](https://console.firebase.google.com/)
   - Select your project
   - Go to Project Settings → Service Accounts
   - Click "Generate new private key"
   - Save the JSON file

2. **Encode to base64:**
   
   **Option A: Using the provided script**
   ```bash
   python encode_firebase_credentials.py path/to/service-account-key.json
   ```
   
   **Option B: Using command line (Linux/Mac)**
   ```bash
   base64 -i service-account-key.json | tr -d '\n'
   ```
   
   **Option C: Using PowerShell (Windows)**
   ```powershell
   [Convert]::ToBase64String([IO.File]::ReadAllBytes("service-account-key.json"))
   ```

3. **Set the environment variable:**
   
   **Bash/Zsh:**
   ```bash
   export FIREBASE_SERVICE_ACCOUNT_JSON_B64="<base64-encoded-string>"
   ```
   
   **PowerShell:**
   ```powershell
   $env:FIREBASE_SERVICE_ACCOUNT_JSON_B64="<base64-encoded-string>"
   ```
   
   **Windows CMD:**
   ```cmd
   set FIREBASE_SERVICE_ACCOUNT_JSON_B64=<base64-encoded-string>
   ```
   
   **In .env file:**
   ```env
   FIREBASE_SERVICE_ACCOUNT_JSON_B64=<base64-encoded-string>
   ```
   
   **On Render.com:**
   - Go to your service settings
   - Add environment variable: `FIREBASE_SERVICE_ACCOUNT_JSON_B64`
   - Paste the base64-encoded string as the value

## Method 2: Direct JSON String

Use this method if you prefer to store the JSON directly (less secure for production).

### Steps:

1. **Get your Firebase service account key** (same as Method 1)

2. **Set the environment variable with the JSON content:**
   
   **Bash/Zsh:**
   ```bash
   export FIREBASE_SERVICE_ACCOUNT_JSON='{"type":"service_account","project_id":"...",...}'
   ```
   
   **PowerShell:**
   ```powershell
   $env:FIREBASE_SERVICE_ACCOUNT_JSON='{"type":"service_account","project_id":"...",...}'
   ```
   
   **In .env file:**
   ```env
   FIREBASE_SERVICE_ACCOUNT_JSON={"type":"service_account","project_id":"...",...}
   ```
   
   **Note:** Be careful with quotes and escaping. The JSON must be valid and properly escaped.

## Method 3: File Path

Use this method for local development or when you have access to the file system.

### Steps:

1. **Get your Firebase service account key** (same as Method 1)

2. **Place the file in a secure location:**
   - For local development: Place in your project directory (but **DO NOT commit to git**)
   - For servers: Upload to a secure location on the server

3. **Set the environment variable with the file path:**
   
   **Bash/Zsh:**
   ```bash
   export FIREBASE_CREDENTIALS_PATH="/path/to/service-account-key.json"
   ```
   
   **PowerShell:**
   ```powershell
   $env:FIREBASE_CREDENTIALS_PATH="C:\path\to\service-account-key.json"
   ```
   
   **In .env file:**
   ```env
   FIREBASE_CREDENTIALS_PATH=/path/to/service-account-key.json
   ```

## Verification

After setting up credentials, you can verify the configuration by:

1. **Starting the application:**
   ```bash
   python -m uvicorn main:app --reload
   ```

2. **Check the logs** - You should see:
   ```
   [firebase] Using FIREBASE_SERVICE_ACCOUNT_JSON_B64 (recommended)
   [firebase] Successfully initialized using FIREBASE_SERVICE_ACCOUNT_JSON_B64
   ```

3. **Test an endpoint:**
   ```bash
   curl http://localhost:8000/
   ```

## Troubleshooting

### Error: "Invalid JWT Signature" or "invalid_grant"

This error occurs when:
- Credentials are missing or invalid
- The service account key has expired or been revoked
- Application Default Credentials (ADC) are being used on non-Google infrastructure

**Solution:**
- Ensure one of the three credential methods is properly configured
- Verify your service account key is valid and not expired
- Re-download the service account key from Firebase Console if needed

### Error: "Firebase credentials not configured"

**Solution:**
- Check that at least one of the environment variables is set
- Verify the environment variable name is correct (case-sensitive)
- For .env files, ensure `python-dotenv` is installed and the file is being loaded

### Error: "Invalid base64 encoding"

**Solution:**
- Re-encode your service account JSON using the provided script
- Ensure no extra whitespace or line breaks in the base64 string
- Check that the entire base64 string is included (it can be very long)

### Error: "File not found" (Method 3)

**Solution:**
- Verify the file path is correct and absolute
- Check file permissions
- Ensure the file exists on the server (for cloud deployments, Method 1 or 2 is recommended)

## Security Best Practices

1. **Never commit credentials to version control**
   - Add `*.json` (service account files) to `.gitignore`
   - Add `.env` to `.gitignore` if it contains credentials

2. **Use Method 1 (Base64) for production**
   - More secure than Method 2 (direct JSON)
   - Works on all platforms without file system access

3. **Rotate credentials regularly**
   - Generate new service account keys periodically
   - Revoke old keys after updating

4. **Limit service account permissions**
   - Only grant necessary Firestore permissions
   - Use principle of least privilege

## Example Service Account JSON Structure

A valid Firebase service account JSON should look like:

```json
{
  "type": "service_account",
  "project_id": "your-project-id",
  "private_key_id": "key-id",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
  "client_email": "firebase-adminsdk-xxxxx@your-project.iam.gserviceaccount.com",
  "client_id": "123456789",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/..."
}
```

## Additional Resources

- [Firebase Admin SDK Documentation](https://firebase.google.com/docs/admin/setup)
- [Service Account Keys](https://cloud.google.com/iam/docs/service-accounts)
- [Firebase Console](https://console.firebase.google.com/)

