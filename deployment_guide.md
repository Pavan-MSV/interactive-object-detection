# Deployment Guide: Firebase & Cloud Run

Since your application has a **Python Backend** (AI Models) and a **Static Frontend** (HTML/JS), you cannot deploy everything to Firebase Hosting alone. Firebase Hosting only supports static files.

**The Solution:**
1.  Deploy the **Backend** to **Google Cloud Run** (a serverless container platform).
2.  Deploy the **Frontend** to **Firebase Hosting**.
3.  Connect them so the frontend can talk to the backend.

I have created the necessary configuration files (`Dockerfile` and `firebase.json`) for you. Follow these steps:

## Prerequisites
1.  Install the [Google Cloud CLI](https://cloud.google.com/sdk/docs/install).
2.  Install [Node.js](https://nodejs.org/) (required for Firebase CLI).
3.  Install Firebase CLI:
    ```bash
    npm install -g firebase-tools
    ```
4.  Login to Google Cloud:
    ```bash
    gcloud auth login
    gcloud config set project YOUR_PROJECT_ID
    ```
5.  Login to Firebase:
    ```bash
    firebase login
    ```

## Step 1: Deploy Backend to Cloud Run

1.  Open your terminal in the project root (`d:\object`).
2.  Run the deploy command (this builds the Docker container and deploys it):
    ```bash
    gcloud run deploy object-detection-api --source . --region us-central1 --allow-unauthenticated
    ```
    *   *Note: This might take a few minutes to upload the model files.*
    *   *If asked to enable APIs (Artifact Registry, Cloud Run, Cloud Build), say **yes**.*

3.  Once finished, keep the Service Name (`object-detection-api`) and Region (`us-central1`) in mind.

## Step 2: Configure Firebase

1.  Initialize Firebase in your project folder:
    ```bash
    firebase init hosting
    ```
    *   **Select**: "Use an existing project" (select your Google Cloud project).
    *   **Public directory**: Type `frontend` (Important!).
    *   **Configure as a single-page app?**: No.
    *   **Set up automatic builds and deploys with GitHub?**: No.
    *   **File overwrite warnings**: If it asks to overwrite `index.html`, say **NO**. If it asks to overwrite `firebase.json`, say **NO** (use the one I created).

## Step 3: Connect Frontend to Backend

I have already created a `firebase.json` file that "rewrites" traffic.
It tells Firebase: *"If anyone visits `/detect`, send that request to the Cloud Run service named `object-detection-api`."*

**Verify `firebase.json`:**
Ensure your `firebase.json` looks like this (I created it for you):
```json
{
  "hosting": {
    "public": "frontend",
    "rewrites": [
      {
        "source": "/detect",
        "run": {
          "serviceId": "object-detection-api",  <-- Must match your Cloud Run service name
          "region": "us-central1"               <-- Must match your Cloud Run region
        }
      }
    ]
  }
}
```

## Step 4: Deploy Frontend

1.  Run the deploy command:
    ```bash
    firebase deploy
    ```

2.  Firebase will give you a **Hosting URL** (e.g., `https://your-project.web.app`).
3.  Open that URL and test your app!

---
**Troubleshooting:**
*   **"Error: 404 on /detect"**: This means the rewrite isn't working. Check if your Cloud Run service name in `firebase.json` matches exactly what you deployed.
*   **"Service Unavailable"**: Cloud Run might be cold-starting. Wait a moment and try again.
