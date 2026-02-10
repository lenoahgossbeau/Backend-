import os
import re

PROJECT_ROOT = os.getcwd()

def fix_template_response(content):
    """
    Corrige :
    TemplateResponse(request, "file.html")
    -> TemplateResponse(request, "file.html")
    """
    pattern = re.compile(
        r'TemplateResponse\(\s*"([^"]+)"\s*,\s*\{\s*"request"\s*:\s*(\w+)\s*\}\s*\)'
    )

    return pattern.sub(
        r'TemplateResponse(\2, "\1")',
        content
    )


def fix_pytest_return(content):
    """
    Corrige :
    return True / return False
    -> assert True / assert False
    """
    content = re.sub(r'^\s*return\s+True\s*$', '    assert True', content, flags=re.MULTILINE)
    content = re.sub(r'^\s*return\s+False\s*$', '    assert False', content, flags=re.MULTILINE)
    return content


def process_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        original = f.read()

    modified = original
    modified = fix_template_response(modified)
    modified = fix_pytest_return(modified)

    if modified != original:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(modified)
        print(f"✔ Corrigé : {filepath}")


def scan_project():
    print("🔍 Scan du projet en cours...\n")
    for root, _, files in os.walk(PROJECT_ROOT):
        if "venv" in root or "__pycache__" in root:
            continue

        for file in files:
            if file.endswith(".py"):
                process_file(os.path.join(root, file))

    print("\n✅ Nettoyage terminé.")


if __name__ == "__main__":
    scan_project()
