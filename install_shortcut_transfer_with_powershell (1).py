from pathlib import Path
import subprocess


def install():
    """
    Installer for the shortcut-transfer PowerShell script.

    What this program does:
    1. Creates the public ShortcutHolder folder if needed.
    2. Writes the PowerShell shortcut-transfer script.
    3. Creates a .bat launcher in the all-users Startup folder.
    4. Executes the PowerShell script once immediately.

    Important:
    - Run this Python script once as administrator.
    - The Startup folder used here applies to all users.
    - The PowerShell script creates a hidden per-user README marker in AppData.
      If that marker exists, shortcuts are not copied again for that user.
    """

    startup_folder = Path(
        r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs\Startup"
    )

    script_folder = Path(r"C:\Users\Public\ShortcutHolder")
    script_folder.mkdir(parents=True, exist_ok=True)

    powershell_script_path = script_folder / "shortcut_transfer.ps1"
    launcher_path = startup_folder / "shortcut_transfer_launcher.bat"

    powershell_script_content = '$DesktopPublic = "C:\\Users\\Public\\Desktop"\n$TempHolder = "C:\\Users\\Public\\ShortcutHolder"\n\n# Get the Desktop folder of the currently logged-in user\n$Dest = [Environment]::GetFolderPath([Environment+SpecialFolder]::DesktopDirectory)\n\n# Fallback in case Windows returns an empty path\nif ([string]::IsNullOrWhiteSpace($Dest)) {\n    $Dest = Join-Path $env:USERPROFILE "Desktop"\n}\n\n# Hidden per-user marker folder\n$MarkerFolder = Join-Path $env:LOCALAPPDATA "ShortcutTransfer"\n$ReadmePath = Join-Path $MarkerFolder "README_ShortcutTransfer.txt"\n\n# If the README marker already exists, do not transfer shortcuts again\nif (Test-Path $ReadmePath) {\n    exit 0\n}\n\n# Create ShortcutHolder if needed\nif (-not (Test-Path $TempHolder)) {\n    New-Item -ItemType Directory -Path $TempHolder -Force | Out-Null\n}\n\n# Create the marker folder if needed\nif (-not (Test-Path $MarkerFolder)) {\n    New-Item -ItemType Directory -Path $MarkerFolder -Force | Out-Null\n}\n\n# Make the marker folder hidden\nattrib +h $MarkerFolder\n\n# Create the current user\'s Desktop folder if needed\nif (-not (Test-Path $Dest)) {\n    New-Item -ItemType Directory -Path $Dest -Force | Out-Null\n}\n\n# Move .lnk shortcuts from Public Desktop to ShortcutHolder.\n# This can require administrator rights depending on Windows permissions.\nif (Test-Path $DesktopPublic) {\n    Get-ChildItem -Path $DesktopPublic -File -Filter "*.lnk" | ForEach-Object {\n        $Target = Join-Path $TempHolder $_.Name\n\n        # If duplicate exists in ShortcutHolder, ignore the shortcut we are trying to move\n        if (-not (Test-Path $Target)) {\n            try {\n                Move-Item -Path $_.FullName -Destination $Target -ErrorAction Stop\n            }\n            catch {\n                # If moving fails because of permissions, ignore and continue\n            }\n        }\n    }\n}\n\n# Copy .lnk shortcuts from ShortcutHolder to the current user\'s Desktop\nif (Test-Path $TempHolder) {\n    Get-ChildItem -Path $TempHolder -File -Filter "*.lnk" | ForEach-Object {\n        $Target = Join-Path $Dest $_.Name\n\n        # If duplicate exists on user\'s Desktop, ignore the shortcut we are trying to copy\n        if (-not (Test-Path $Target)) {\n            try {\n                Copy-Item -Path $_.FullName -Destination $Target -ErrorAction Stop\n            }\n            catch {\n                # If copying fails, ignore and continue\n            }\n        }\n    }\n}\n\n# Create README marker at the end of script execution\n$ReadmeContent = @"\nREADME - Shortcut Transfer\n\nCe fichier a ete cree automatiquement par le script de transfert des raccourcis.\n\nFonctionnement :\n- Au premier lancement pour cet utilisateur, le script copie les raccourcis stockes dans :\n  C:\\Users\\Public\\ShortcutHolder\n\n  vers le bureau de l\'utilisateur courant :\n  $Dest\n\n- Une fois le transfert termine, ce fichier README est cree dans :\n  $MarkerFolder\n\n- Lors des prochains demarrages ou connexions utilisateur, le script verifie si ce fichier README existe.\n\n- Si ce fichier README est present, le script ne recopie pas les icones sur le bureau utilisateur.\n\nPourquoi ce fichier existe :\nCe fichier evite qu\'une icone supprimee manuellement par l\'utilisateur soit automatiquement remise sur le bureau au prochain redemarrage.\n\nPour reactiver le transfert pour cet utilisateur :\nSupprimez ce fichier README, puis redemarrez la session utilisateur ou relancez le script.\n\nFichier utilise comme marqueur :\n$ReadmePath\n"@\n\nSet-Content -Path $ReadmePath -Value $ReadmeContent -Encoding UTF8\n\n# Make the README marker hidden too\nattrib +h $ReadmePath\n\nexit 0\n'

    # Write or update the PowerShell script
    powershell_script_path.write_text(
        powershell_script_content,
        encoding="utf-8"
    )

    # Do not put the .ps1 directly in the Startup folder.
    # A .ps1 placed directly there may open in Notepad instead of executing.
    accidental_ps1_in_startup = startup_folder / "shortcut_transfer.ps1"
    if accidental_ps1_in_startup.exists():
        accidental_ps1_in_startup.unlink()

    launcher_content = f"""@echo off
powershell.exe -NoProfile -ExecutionPolicy RemoteSigned -File "{powershell_script_path}"
"""

    # Create or update the .bat launcher in the all-users Startup folder
    launcher_path.write_text(
        launcher_content,
        encoding="utf-8"
    )

    # Execute the PowerShell script once immediately
    subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "RemoteSigned",
            "-File",
            str(powershell_script_path),
        ],
        check=False
    )

    return 0
