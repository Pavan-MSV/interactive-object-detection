# Deployment Guide: Hugging Face Spaces (Free)

This is the easiest and free way to host your AI application.

## 1. Create a Space on Hugging Face
1.  Go to [huggingface.co/spaces](https://huggingface.co/spaces).
2.  Click **"Create new Space"**.
3.  **Space Name**: `interactive-object-detection` (or similar).
4.  **License**: `MIT` or `OpenRAIL`.
5.  **SDK**: Select **Docker** (Blank).
6.  **Space Hardware**: `CPU Basic` (Free).
7.  Click **"Create Space"**.

### Option C: Command Line Only (Git from Scratch)
If you haven't set up Git yet, run these commands inside your `d:\object` folder:

1.  **Initialize Git**:
    ```bash
    git init
    ```

2.  **Add Remote** (Replace with your Space URL):
    ```bash
    git remote add space https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE_NAME
    ```

3.  **Setup Large File Storage (Important for Models)**:
    Since `yolov8x.pt` is >100MB, you need `git-lfs`.
    ```bash
    git lfs install
    git lfs track "*.pt"
    git add .gitattributes
    ```

4.  **Pull Existing Files** (Sync with Hugging Face):
    ```bash
    git pull space main --allow-unrelated-histories
    ```

5.  **Push Everything**:
    ```bash
    git add .
    git commit -m "Deploy from CLI"
    git push space main
    ```
### 🔑 Important: Authentication
When you run `git push`, it will ask for a **Username** and **Password**.
*   **Username**: Your Hugging Face username (e.g., `Pavan7382`).
*   **Password**: You **MUST** use an **Access Token** (not your login password).

**How to get an Access Token:**
1.  Go to [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens).
2.  Click **"New token"**.
3.  Name: `deploy-token`.
4.  Role: **Write**.
5.  Click **"Generate"** and **Copy** the token (starts with `hf_...`).
6.  Paste *that token* when Git asks for the password.

## 3. Watch it Build
1.  Go to the **"App"** tab in your Space.
2.  You will see a "Building" status.
3.  Once finished, your app will appear!

## ⚠️ Important Notes
*   **Startup Time**: Since we are using large AI models, the "Build" phase might take 5-10 minutes the first time.
*   **Sleep**: Free Spaces "sleep" after 48 hours of no activity. It takes a minute to wake up when you visit again.
