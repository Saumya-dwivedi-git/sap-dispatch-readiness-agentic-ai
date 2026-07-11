# GitHub Upload Steps For Beginners

Use this guide for uploading the showcase copy, not the live demo folder.

## Folder To Upload

```text
SDRA_Dispatch_Readiness_GitHub_Showcase
```

Do not upload:

```text
SDRA_Dispatch_Readiness_SAP_Agent_VSCode/run_outputs
```

## Step 1: Create Repository On GitHub

1. Open GitHub dashboard.
2. Click the green **New** button near **Top repositories**.
3. Repository name:

```text
sap-dispatch-readiness-agentic-ai
```

4. Description:

```text
SAP-connected Agentic AI prototype for sales order dispatch readiness and controlled delivery approval.
```

5. Select **Public** if you want it visible on your profile.
6. Do not add README, `.gitignore`, or license on GitHub because this folder already has files.
7. Click **Create repository**.

## Step 2: Open Terminal In VS Code

Open Git Bash or PowerShell and go to this showcase folder:

```bash
cd <your-local-folder>/SDRA_Dispatch_Readiness_GitHub_Showcase
```

If you are using PowerShell:

```powershell
cd <your-local-folder>\SDRA_Dispatch_Readiness_GitHub_Showcase
```

## Step 3: Initialize Git

```bash
git init
git status
```

## Step 4: Add Files

```bash
git add .
git status
```

Before committing, confirm `run_outputs/` is not listed.

## Step 5: Commit

```bash
git commit -m "Add SAP dispatch readiness agentic AI showcase"
```

## Step 6: Connect To GitHub

After GitHub creates the repository, it will show your repository URL. It will look like:

```text
https://github.com/YOUR-GITHUB-USERNAME/sap-dispatch-readiness-agentic-ai.git
```

Run:

```bash
git remote add origin https://github.com/YOUR-GITHUB-USERNAME/sap-dispatch-readiness-agentic-ai.git
git branch -M main
git push -u origin main
```

Replace `YOUR-GITHUB-USERNAME` with your actual GitHub username.

## Step 7: Pin It On Your GitHub Profile

1. Go to your GitHub profile.
2. Click **Customize your pins**.
3. Select `sap-dispatch-readiness-agentic-ai`.
4. Save.

## Step 8: What To Show In Demo

Show these in order:

1. GitHub README.
2. Architecture and SAP object list.
3. UI screenshots or live local UI.
4. Search/filter by customer or material.
5. Action card with next step.
6. Explain approval-first controlled autonomy.
