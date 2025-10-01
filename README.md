# Terraform Drift Detection on AWS 🚀

Automated **drift detection pipeline** built on **Terraform + AWS CodeBuild/CodePipeline** with optional **AI summarization via Amazon Bedrock**.  
This project is the AWS equivalent of the adapted to use **S3, DynamoDB, Bedrock, Comprehend, SES, and Chime**.

---

## 📌 Features

- Detects **infrastructure drift** via `terraform plan -detailed-exitcode`.
- Stores Terraform state in **S3** with optional **DynamoDB locking**.
- Runs on a **scheduled basis** (via EventBridge cron).
- Pushes drift reports to:
  - **Amazon Chime** (webhook notifications)
  - **Amazon SES / SMTP** (email alerts)
- Optional **AI summarization** of drift using **Amazon Bedrock** (with fallback to Comprehend).
- Filters out **tag-only changes** (ignores noise).

---

## 🔄 Architecture

```mermaid
flowchart TD
    EB["EventBridge Rule (cron)"] --> CB["CodeBuild Job"]
    CB --> TF["Terraform Plan"]
    TF -->|Plan JSON| S3[("S3 Drift Reports")]
    TF --> PY["analyze_drift.py"]
    PY -->|AI Summary| BR["Amazon Bedrock"]
    PY -->|Email| SES["Amazon SES"]
    PY -->|Webhook| CH["Amazon Chime"]
