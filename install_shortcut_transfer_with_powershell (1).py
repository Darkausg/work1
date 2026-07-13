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

    powershell_script_content = r'''$ErrorActionPreference = "Stop"

try {
    $DesktopPublic = "C:\Users\Public\Desktop"
    $TempHolder = "C:\Users\Public\ShortcutHolder"

    # Get the Desktop folder of the currently logged-in user
    $Dest = [Environment]::GetFolderPath([Environment+SpecialFolder]::DesktopDirectory)

    # Fallback in case Windows returns an empty path
    if ([string]::IsNullOrWhiteSpace($Dest)) {
        $Dest = Join-Path $env:USERPROFILE "Desktop"
    }

    # Hidden per-user marker folder
    $MarkerFolder = Join-Path $env:LOCALAPPDATA "ShortcutTransfer"
    $ReadmePath = Join-Path $MarkerFolder "README_ShortcutTransfer.txt"

    Write-Host "Bureau public : $DesktopPublic"
    Write-Host "Dossier temporaire : $TempHolder"
    Write-Host "Bureau utilisateur : $Dest"
    Write-Host "Fichier README marqueur : $ReadmePath"
    Write-Host ""

    # Create ShortcutHolder if needed
    if (-not (Test-Path $TempHolder)) {
        Write-Host "Creation du dossier ShortcutHolder..."
        New-Item -ItemType Directory -Path $TempHolder -Force | Out-Null
    }

    # Create the marker folder if needed
    if (-not (Test-Path $MarkerFolder)) {
        Write-Host "Creation du dossier marqueur..."
        New-Item -ItemType Directory -Path $MarkerFolder -Force | Out-Null
    }

    # Make the marker folder hidden
    attrib +h "$MarkerFolder"

    # Create the current user's Desktop folder if needed
    if (-not (Test-Path $Dest)) {
        Write-Host "Creation du bureau utilisateur..."
        New-Item -ItemType Directory -Path $Dest -Force | Out-Null
    }

    # Move .lnk shortcuts from Public Desktop to ShortcutHolder.
    # This can require administrator rights depending on Windows permissions.
    if (Test-Path $DesktopPublic) {
        Write-Host "Recherche des raccourcis dans le bureau public..."

        Get-ChildItem -Path $DesktopPublic -File -Filter "*.lnk" | ForEach-Object {
            $SourcePath = $_.FullName
            $Target = Join-Path $TempHolder $_.Name

            if (-not (Test-Path $Target)) {
                try {
                    Write-Host "Deplacement : $SourcePath -> $Target"
                    Move-Item -Path $SourcePath -Destination $Target -ErrorAction Stop
                }
                catch {
                    Write-Host "Erreur lors du deplacement de : $SourcePath"
                    Write-Host $_.Exception.Message
                    Write-Host ""
                }
            }
            else {
                Write-Host "Ignore, deja present dans ShortcutHolder : $($_.Name)"
            }
        }
    }
    else {
        Write-Host "Le dossier Public Desktop n'existe pas : $DesktopPublic"
    }

    Write-Host ""

    # If the README marker already exists, do not transfer shortcuts again
    if (Test-Path $ReadmePath) {
        Write-Host "README deja present."
        Write-Host "Les raccourcis ne seront pas recopies sur le bureau utilisateur."
    }
    else {
        # Copy .lnk shortcuts from ShortcutHolder to the current user's Desktop
        if (Test-Path $TempHolder) {
            Write-Host "Copie des raccourcis vers le bureau utilisateur..."

            Get-ChildItem -Path $TempHolder -File -Filter "*.lnk" | ForEach-Object {
                $SourcePath = $_.FullName
                $Target = Join-Path $Dest $_.Name

                if (-not (Test-Path $Target)) {
                    try {
                        Write-Host "Copie : $SourcePath -> $Target"
                        Copy-Item -Path $SourcePath -Destination $Target -ErrorAction Stop
                    }
                    catch {
                        Write-Host "Erreur lors de la copie de : $SourcePath"
                        Write-Host $_.Exception.Message
                        Write-Host ""
                    }
                }
                else {
                    Write-Host "Ignore, deja present sur le bureau utilisateur : $($_.Name)"
                }
            }
        }

        # Create README marker at the end of script execution
        $ReadmeContent = @"
README - Shortcut Transfer

Ce fichier a ete cree automatiquement par le script de transfert des raccourcis.

Fonctionnement :
- Au premier lancement pour cet utilisateur, le script copie les raccourcis stockes dans :
  C:\Users\Public\ShortcutHolder

  vers le bureau de l'utilisateur courant :
  $Dest

- Une fois le transfert termine, ce fichier README est cree dans :
  $MarkerFolder

- Lors des prochains demarrages ou connexions utilisateur, le script verifie si ce fichier README existe.

- Si ce fichier README est present, le script ne recopie pas les icones sur le bureau utilisateur.

Pourquoi ce fichier existe :
Ce fichier evite qu'une icone supprimee manuellement par l'utilisateur soit automatiquement remise sur le bureau au prochain redemarrage.

Pour reactiver le transfert pour cet utilisateur :
Supprimez ce fichier README, puis redemarrez la session utilisateur ou relancez le script.

Fichier utilise comme marqueur :
$ReadmePath
"@

        Write-Host ""
        Write-Host "Creation du README marqueur..."
        Set-Content -Path $ReadmePath -Value $ReadmeContent -Encoding UTF8

        # Make the README marker hidden too
        attrib +h "$ReadmePath"

        Write-Host "README cree : $ReadmePath"
    }

    Write-Host ""
    Write-Host "Script termine correctement."
}
catch {
    Write-Host ""
    Write-Host "ERREUR GENERALE DU SCRIPT"
    Write-Host $_.Exception.Message
}
finally {
    Write-Host ""
    Read-Host "Appuyez sur Entree pour fermer cette fenetre"
}
    '''
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
