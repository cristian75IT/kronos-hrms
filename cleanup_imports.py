import os

files = [
    "backend/src/services/hr_reporting/routers/dashboard.py",
    "backend/src/services/hr_reporting/routers/reports.py",
    "backend/src/services/hr_reporting/routers/admin.py",
    "backend/src/services/notifications/router.py",
    "backend/src/services/leaves/routers/balances.py",
    "backend/src/services/audit/router.py",
    "backend/src/services/approvals/routers/config.py",
    "backend/src/services/expensive_wallet/routers/wallet.py",
    "backend/src/services/expenses/router.py",
    "backend/src/services/leaves_wallet/routers/wallet.py",
    "backend/src/services/auth/router.py",
    "backend/src/services/config/router.py",
    "backend/src/core/__init__.py"
]

to_remove = [
    "require_admin",
    "require_manager",
    "require_approver",
    "require_hr"
]

for fp in files:
    full_path = os.path.abspath(fp)
    if not os.path.exists(full_path):
        print(f"File not found: {fp}")
        continue

    with open(full_path, 'r') as f:
        content = f.read()
    
    original_content = content
    
    # Process line by line to target imports
    lines = content.split('\n')
    new_lines = []
    
    for line in lines:
        if "from src.core.security import" in line or (fp.endswith("__init__.py") and "require_" in line):
            for item in to_remove:
                # remove with preceding comma and space
                line = line.replace(f", {item}", "")
                # remove with following comma and space
                line = line.replace(f"{item}, ", "")
                # remove standalone (if it was the last one or only one) - check bounds to be safe? 
                # Assuming imports are well spaced.
                # Only replace if permissions/other imports remain, otherwise we might leave "import "
                # But we added require_permission to all of them, so it's fine.
                line = line.replace(item, "")
            
            # Cleanup multiple commas if any
            line = line.replace(", ,", ",")
            line = line.replace("import ,", "import ")
            # strip trailing comma?
            if line.strip().endswith(","):
                line = line.rstrip().rstrip(",")
        
        new_lines.append(line)
    
    new_content = '\n'.join(new_lines)

    if original_content != new_content:
        with open(full_path, 'w') as f:
            f.write(new_content)
        print(f"Updated {fp}")
    else:
        print(f"No changes for {fp}")
