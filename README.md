# Misc Mirror

Spiegelt Binary Blobs aus dem Internet via Artifactory ins SMN

Die zu spiegelenden Artifakte werden in der Datei config.yaml definiert.

Diese Datei wird via puppet ausgeliefert.

Aktuell werden 3 Downloadtypen unterstützt:
    * Statische URLs
    * Github Releases
    * VSCode Extensions

Siehe Selenium.md für experimentellen Selenium support


# Config File
> Todo: Doku 

# Use
> Todo: Doku 

# Downloadtypen

## GitHub Releases
> Todo: Doku 

Type in config:  ```github_release```

## Statische Dateien
> Todo: Doku 

Type in config:  ```static_file```

## VSCode Plugins
> Todo: Doku 

VSCode Extensions
Type in config:  ```vscode```

## Selenium Download-Datei
Type in config: ```selenium````

Nachdem mit _scripts/build_venv das virtuelle environment und damid auch selenium installiert wurde muss nun noch google chrome und die "chromedriver" api insatlliert werden.

Aus epel repository bekommt man beides in einer abgestimmten version mit `yum install -y chromium chromedriver`


# Plugins
## Download von Windows 10 ISO-Dateien 
Dieses Plugin lädt bei Ausführung sämtliche Windows 10 ISO-Dateien herunter, welche noch nicht in der Datei "winversions.txt" enthalten sind. 
Neue Downloads werden automatisch in die Datei ergänzt, um doppeltes downloaden zu vermeiden.

Um eine Datei erneut herunter zu laden, muss der entsprechende Name dieser Datei aus dem .txt-File gelöscht werden.

Das Plugin ist nur für Windows 10 Enterprise 64Bit Versionen auf Deutsch!


> Achtung: Da Selenium nicht auf den Download-Status zugreifen kann, schließt sich das Programm erst (und somit auch das Browser-Fenster mit dem Download), wenn keine ".crdownload" im Download-Ordner mehr ist. (Sind dort mehrere solcher Dateien enthalten, muss das Programm nach Abschluss des Downloads händisch beendet werden)!


Das Plugin hat keine 100%ige Erfolgsquote, da der Katalon-Teil nicht immer funktioniert / alle Klicks/Elemente durchführt/findet.

Zwischen den einzelnen Klicks wurde immer ein sleep eingefügt, da das Programm sonst nicht funktioniert hat.

Wenn der Katalon Teil abgeschlossen ist, wird aus der Tabelle von Win10 Enterp. 64Bit die Namen mit der Datei "winversions.txt" verglichen, da sich in der Tabelle auch alte Versionen und z.B.: auch für ARM befinden.

Falls eine Datei in dem File nicht vorhanden ist, wird dies mit einem Klick gedownloaded.

Danach wird der Download-Ordner "überwacht" und das Programm läuft solange (also auch der Download), solange sich .crdownload - Dateien im Download-Ordner befinden, danach wird das Programm beendet.

