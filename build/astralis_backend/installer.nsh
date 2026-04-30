!macro customInstall
  MessageBox MB_YESNO "Create a desktop shortcut?" IDYES createDesktop IDNO skipDesktop
  createDesktop:
    CreateShortCut "$DESKTOP\Astralis.lnk" "$INSTDIR\Astralis.exe"
  skipDesktop:

  MessageBox MB_YESNO "Add to Start Menu?" IDYES createStart IDNO skipStart
  createStart:
    CreateDirectory "$SMPROGRAMS\Astralis"
    CreateShortCut "$SMPROGRAMS\Astralis\Astralis.lnk" "$INSTDIR\Astralis.exe"
  skipStart:
!macroend