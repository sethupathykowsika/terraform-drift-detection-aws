import json, os, subprocess, shlex
from typing import List, Dict
from ai_summarizer import summarize_rule_based
from notifier import notify_chime, notify_email

TF_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "terraform"))

def run(cmd, cwd=None, check=True):
    print(f"[RUN] {cmd}")
    res = subprocess.run(shlex.split(cmd), cwd=cwd, capture_output=True, text=True)
    if check and res.returncode not in (0,2):
        print(res.stdout); print(res.stderr); raise RuntimeError(f"Command failed: {cmd}")
    return res

def terraform_plan_json(plan_out="plan.out"):
    run("terraform init -upgrade", cwd=TF_DIR)
    res = run("terraform plan -refresh=true -detailed-exitcode -out plan.out", cwd=TF_DIR, check=False)
    exit_code = res.returncode
    print(f"[PLAN] detailed-exit-code={exit_code}")
    show = subprocess.run(f"terraform show -json {plan_out}", cwd=TF_DIR, shell=True, capture_output=True, text=True)
    if show.returncode != 0: print(show.stdout); print(show.stderr); raise RuntimeError("terraform show failed")
    return json.loads(show.stdout), exit_code

def extract_changes(plan_json: Dict) -> List[Dict]:
    result=[]
    for rc in plan_json.get("resource_changes", []):
        address=rc.get("address"); change=rc.get("change", {}); actions=change.get("actions", []); action="+".join(actions) if actions else "unknown"
        before=change.get("before", {}); after=change.get("after", {})
        def is_tag_only(b,a):
            if not isinstance(b, dict) or not isinstance(a, dict): return False
            keys=set(b.keys()).union(a.keys())
            diffs=[k for k in keys if k!="tags" and b.get(k)!=a.get(k)]
            return (b.get("tags")!=a.get("tags")) and not diffs
        important=True; details={}
        if "delete" in actions or "create" in actions:
            important=True; details={"before": before, "after": after}
        elif "update" in actions:
            if is_tag_only(before, after):
                important=False; details={"changed": "tags only"}
            else:
                important=True
                if isinstance(before, dict) and isinstance(after, dict):
                    hints=[]
                    for k in set(before.keys()).union(after.keys()):
                        if k=="tags": continue
                        if before.get(k)!=after.get(k): hints.append(f"{k}: {before.get(k)} -> {after.get(k)}")
                    details={"changed": ", ".join(hints)[:240]}
        else:
            important=False
        result.append({"address": address, "action": action, "important": important, "details": details})
    return result

def main():
    plan, code = terraform_plan_json()
    changes = extract_changes(plan)
    summary = summarize_rule_based(changes)
    print("\n===== SUMMARY =====\n" + summary + "\n===================\n")
    # Notifications (skip if envs not set)
    notify_chime(os.getenv("CHIME_WEBHOOK_URL",""), summary)
    notify_email(os.getenv("SMTP_HOST",""), int(os.getenv("SMTP_PORT","0") or 0),
                 os.getenv("SMTP_USERNAME",""), os.getenv("SMTP_PASSWORD",""),
                 os.getenv("MAIL_FROM",""), os.getenv("MAIL_TO",""),
                 "Drift Report", summary)
    print("[RESULT]", "No drift detected." if code==0 else "Drift detected/changes present." if code==2 else "Unknown exit code.")

if __name__ == "__main__":
    main()
