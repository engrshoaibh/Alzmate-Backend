# Render.com Deployment Guide

## Quick Start

### Start Command for Render.com

```
uvicorn main:app --host 0.0.0.0 --port $PORT
```

## Deployment Steps

### 1. Create a New Web Service on Render.com

1. Go to [Render.com Dashboard](https://dashboard.render.com)
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Select the `BackendModel` directory as the root directory

### 2. Configure Build & Start Commands

**Build Command:**
```bash
pip install -r requirements.txt
```

**Start Command:**
```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

### 3. Set Environment Variables

In Render.com dashboard, go to Environment tab and add:

#### Required Firebase Variables:
```
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_SERVICE_ACCOUNT_JSON={"type":"service_account","project_id":"...","private_key_id":"...","private_key":"...","client_email":"...","client_id":"...","auth_uri":"...","token_uri":"...","auth_provider_x509_cert_url":"...","client_x509_cert_url":"..."}
```

**OR** if using credentials file:
```
FIREBASE_CREDENTIALS_PATH=/opt/render/project/src/credentials.json
```

#### Optional Cloudinary Variables (defaults are in config.py):
```
CLOUDINARY_CLOUD_NAME=dkiqc4jru
CLOUDINARY_API_KEY=659932293576982
CLOUDINARY_API_SECRET=1f7M0nZpCLZ1F7ytj1CYwaV2xo8
CLOUDINARY_UPLOAD_PRESET=alzMate
```

### 4. Python Version

Render.com will auto-detect Python version from `runtime.txt` or you can specify:
- Python 3.11 (recommended)

### 5. Deploy

Click "Create Web Service" and Render will:
1. Build your application
2. Install dependencies
3. Start the server using the start command

## Configuration Details

### Start Command Breakdown

```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

- `uvicorn`: ASGI server
- `main:app`: Points to `app` in `main.py`
- `--host 0.0.0.0`: Listen on all interfaces (required for Render)
- `--port $PORT`: Use Render's provided PORT environment variable

### Alternative Start Commands

#### With Workers (for better performance):
```bash
uvicorn main:app --host 0.0.0.0 --port $PORT --workers 2
```

#### With Logging:
```bash
uvicorn main:app --host 0.0.0.0 --port $PORT --log-level info --access-log
```

#### Production with all options:
```bash
uvicorn main:app --host 0.0.0.0 --port $PORT --workers 2 --log-level info --access-log --no-use-colors
```

## Environment Variables Setup

### Option 1: Using Service Account JSON String (Recommended for Render)

1. Get your Firebase service account JSON file
2. Convert it to a single-line JSON string
3. Set `FIREBASE_SERVICE_ACCOUNT_JSON` environment variable in Render

**Example:**
```json
{"type":"service_account","project_id":"your-project","private_key_id":"...","private_key":"-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n","client_email":"...","client_id":"...","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","client_x509_cert_url":"..."}
```

### Option 2: Using Credentials File

1. Upload your `service-account-key.json` to Render
2. Set `FIREBASE_CREDENTIALS_PATH` to the file path
3. Note: This requires file system access

## Render.com Settings

### Plan Selection
- **Starter Plan**: Good for development/testing
- **Standard Plan**: Recommended for production (better performance, more resources)

### Auto-Deploy
- Enable auto-deploy from main branch
- Render will redeploy on every push

### Health Check
Render automatically checks: `GET /`
Your API has a root endpoint that returns API information.

## Troubleshooting

### Build Fails
- Check Python version compatibility
- Verify all dependencies in `requirements.txt`
- Check build logs for specific errors

### Service Won't Start
- Verify start command is correct
- Check environment variables are set
- Review logs for initialization errors

### Firebase Connection Issues
- Verify `FIREBASE_SERVICE_ACCOUNT_JSON` is valid JSON
- Check that service account has Firestore permissions
- Ensure project ID is correct

### Model Loading Issues
- First request may be slow (model download)
- Consider using Render's persistent disk for model caching
- Check memory limits (models require ~1GB RAM)

## Performance Tips

1. **Enable Auto-Sleep Prevention**: For free tier, use a cron job to ping your service
2. **Use Workers**: Add `--workers 2` for better concurrency
3. **Monitor Logs**: Check Render logs for performance issues
4. **Set Timeouts**: Adjust timeout settings if needed

## Custom Domain

1. Go to Settings → Custom Domains
2. Add your domain
3. Update DNS records as instructed
4. Update Flutter app `api_config.dart` with new URL

## Monitoring

- **Logs**: Available in Render dashboard
- **Metrics**: CPU, Memory, Network usage
- **Alerts**: Set up alerts for service downtime

## Quick Reference

**Start Command:**
```
uvicorn main:app --host 0.0.0.0 --port $PORT
```

**Build Command:**
```
pip install -r requirements.txt
```

**Root Directory:**
```
BackendModel
```

**Python Version:**
```
3.11 (or as specified in runtime.txt)
```






