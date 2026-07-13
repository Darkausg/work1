def transfer_shortcuts() -> int:
    """
    Move public desktop shortcuts into a shared folder, then copy them once
    to the current user's Desktop.

    Returns:
        0 if execution finishes successfully.
        1 if a critical error occurs.

    Important:
        Administrator rights may be required to move shortcuts from:
        C:\\Users\\Public\\Desktop
    """
    import ctypes
    import os
    import shutil
    from pathlib import Path

    public_desktop = Path(r"C:\Users\Public\Desktop")
    shortcut_holder = Path(r"C:\Users\Public\ShortcutHolder")

    # Retrieve the actual Desktop folder of the current user.
    desktop_buffer = ctypes.create_unicode_buffer(260)

    result = ctypes.windll.shell32.SHGetFolderPathW(
        None,
        0x0010,  # CSIDL_DESKTOPDIRECTORY
        None,
        0,
        desktop_buffer,
    )

    if result == 0 and desktop_buffer.value.strip():
        destination_desktop = Path(desktop_buffer.value)
    else:
        user_profile = os.environ.get("USERPROFILE")

        if user_profile:
            destination_desktop = Path(user_profile) / "Desktop"
        else:
            destination_desktop = Path.home() / "Desktop"

    # Determine the per-user marker location.
    local_app_data = os.environ.get("LOCALAPPDATA")

    if local_app_data:
        marker_folder = Path(local_app_data) / "ShortcutTransfer"
    else:
        marker_folder = (
            Path.home()
            / "AppData"
            / "Local"
            / "ShortcutTransfer"
        )

    readme_path = marker_folder / "README_ShortcutTransfer.txt"

    try:
        shortcut_holder.mkdir(parents=True, exist_ok=True)
        marker_folder.mkdir(parents=True, exist_ok=True)
        destination_desktop.mkdir(parents=True, exist_ok=True)
    except (OSError, PermissionError) as error:
        print(f"Erreur pendant la création des dossiers : {error}")
        input("Appuyez sur Entrée pour fermer.")
        return 1

    # Windows file attributes.
    FILE_ATTRIBUTE_HIDDEN = 0x02
    INVALID_FILE_ATTRIBUTES = 0xFFFFFFFF

    # Hide the marker folder without removing its existing attributes.
    try:
        attributes = ctypes.windll.kernel32.GetFileAttributesW(
            str(marker_folder)
        )

        if attributes != INVALID_FILE_ATTRIBUTES:
            ctypes.windll.kernel32.SetFileAttributesW(
                str(marker_folder),
                attributes | FILE_ATTRIBUTE_HIDDEN,
            )
    except (OSError, AttributeError):
        pass

    # Move .lnk files from the Public Desktop to ShortcutHolder.
    #
    # This operation is attempted on every execution, including when the
    # current user already has their README marker. This matches the original
    # PowerShell script.
    if public_desktop.exists():
        try:
            public_shortcuts = list(public_desktop.glob("*.lnk"))
        except OSError:
            public_shortcuts = []

        for shortcut in public_shortcuts:
            if not shortcut.is_file():
                continue

            target = shortcut_holder / shortcut.name

            # Do not overwrite a shortcut already stored in ShortcutHolder.
            if target.exists():
                continue

            try:
                shutil.move(str(shortcut), str(target))
            except (OSError, PermissionError, shutil.Error):
                # Moving files from Public Desktop may require administrator
                # privileges. Ignore the failure and continue.
                continue

    # If the marker already exists, shortcuts must not be copied again.
    if readme_path.exists():
        return 0

    # Copy the stored shortcuts to the current user's Desktop.
    if shortcut_holder.exists():
        try:
            stored_shortcuts = list(shortcut_holder.glob("*.lnk"))
        except OSError:
            stored_shortcuts = []

        for shortcut in stored_shortcuts:
            if not shortcut.is_file():
                continue

            target = destination_desktop / shortcut.name

            # Do not overwrite an existing desktop shortcut.
            if target.exists():
                continue

            try:
                shutil.copy2(shortcut, target)
            except (OSError, PermissionError, shutil.Error):
                # Ignore individual copying errors and continue.
                continue

    readme_content = f"""README - Shortcut Transfer

Ce fichier a été créé automatiquement par le script de transfert des raccourcis.

Fonctionnement :
- Au premier lancement pour cet utilisateur, le script copie les raccourcis stockés dans :
  {shortcut_holder}

  vers le bureau de l'utilisateur courant :
  {destination_desktop}

- Une fois le transfert terminé, ce fichier README est créé dans :
  {marker_folder}

- Lors des prochains démarrages ou connexions utilisateur, le script vérifie si ce fichier README existe.

- Si ce fichier README est présent, le script ne recopie pas les icônes sur le bureau utilisateur.

Pourquoi ce fichier existe :
Ce fichier évite qu'une icône supprimée manuellement par l'utilisateur soit automatiquement remise sur le bureau au prochain redémarrage.

Pour réactiver le transfert pour cet utilisateur :
Supprimez ce fichier README, puis redémarrez la session utilisateur ou relancez le script.

Fichier utilisé comme marqueur :
{readme_path}
"""

    try:
        readme_path.write_text(
            readme_content,
            encoding="utf-8",
        )
    except (OSError, PermissionError) as error:
        print(f"Impossible de créer le fichier marqueur : {error}")
        input("Appuyez sur Entrée pour fermer.")
        return 1

    # Hide the README marker without removing its existing attributes.
    try:
        attributes = ctypes.windll.kernel32.GetFileAttributesW(
            str(readme_path)
        )

        if attributes != INVALID_FILE_ATTRIBUTES:
            ctypes.windll.kernel32.SetFileAttributesW(
                str(readme_path),
                attributes | FILE_ATTRIBUTE_HIDDEN,
            )
    except (OSError, AttributeError):
        pass

    print()
    print("Script terminé. Appuyez sur Entrée pour fermer.")
    input()

    return 0
