# Amazon Bedrock Setup Guide

## 1. Enable Bedrock

1. Go to [AWS Console](https://console.aws.amazon.com/) and sign in
2. Open **Amazon Bedrock** (search for it in the top search bar)
3. In the left sidebar, click **Model access** (under "Get started")
4. Click **Manage model access**
5. Enable **Claude Sonnet 4.6** (under Anthropic)
6. Click **Save changes**

## 2. Create an IAM user with Bedrock permissions

1. Go to **IAM** → **Users** → **Create user**
2. Name the user (e.g. `bedrock-autopilot`)
3. Attach the policy `AmazonBedrockFullAccess` (or create a custom policy with `bedrock:InvokeModel` on the model you need)
4. Create the user and go to **Security credentials** → **Create access key**
5. Choose "Command Line Interface (CLI)" → Create
6. Copy the **Access Key ID** and **Secret Access Key**

## 3. Configure credentials

**Option A: Environment variables**
```bash
export AWS_ACCESS_KEY_ID=AKIA...
export AWS_SECRET_ACCESS_KEY=...
export AWS_DEFAULT_REGION=us-east-1
```

**Option B: AWS config files**

`~/.aws/credentials`:
```
[default]
aws_access_key_id = AKIA...
aws_secret_access_key = ...
```

`~/.aws/config`:
```
[default]
region = us-east-1
```

**Option C: In the app sidebar** — Paste the values into the Sidebar fields.

## 4. Verify

Run the app and click **Create Strategy**. If Bedrock is set up correctly, the strategy will generate without errors.
