# MyCloude - Remote Dashboard

MyCloude è una potente applicazione web per il monitoraggio remoto del sistema e la gestione tramite terminale, dotata di un'interfaccia elegante, reattiva e "mobile-friendly". L'app fornisce statistiche in tempo reale sullo stato della macchina (System Pulse) ed espone un terminale SSH multi-scheda direttamente accessibile dal tuo browser web.

## Funzionalità Principali
- **System Pulse**: Monitoraggio in tempo reale (CPU, RAM, Temperatura, Spazio Disco, Traffico Rete In/Out) senza ricaricare la pagina.
- **Terminale SSH Web**: Console interattiva integrata con `xterm.js` per comunicare via SSH con la macchina host o server remoto. Supporta tab multipli e le shortcut di sistema.
- **Design Adattivo (Mobile)**: L'interfaccia si adatta dinamicamente agli smartphone e ai tablet. Permette inoltre la visualizzazione "Full-Screen" del terminale nascondendo a scomparsa la barra laterale della dashboard.
- **Sicurezza Asincrona**: Backend FastAPI moderno ed asincrono, con autenticazione basata su JWT Token tramite database MySQL.
- **Containerizzato**: Architettura pronta all'uso basata su Docker e Docker Compose nativo per un'installazione rapida.

---

## 🚀 Installazione

1. Assicurati di avere installato sia [Docker](https://docs.docker.com/get-docker/) che la sua estensione [Docker Compose](https://docs.docker.com/compose/install/) sul tuo server (Linux/Ubuntu ecc.).
2. Clona o sposta i file di questo progetto all'interno di una cartella nel tuo server (es. `/home/ciccio/MyCloude`).
3. Crea un file nominato `.env` nella directory principale del progetto copiando lo schema spiegato nel capitolo sottostante e inserendo i tuoi dati personali. 
4. Assicurati che il database abbia lo schema e l'utente amministratore corretto inserito nella tabella.
5. Dal terminale del tuo server, entra nella cartella ed esegui il comando di build e avvio:
   ```bash
   docker compose up -d --build
   ```
6. Apri il browser web e collegati alla porta esposta dal container (es. `http://IP_DEL_SERVER:8080`).

---

## ⚙️ Variabili d'Ambiente (`.env`)

Il file `.env` è il cuore pulsante delle configurazioni segrete (e per questo non andrebbe **mai** pubblicato online o inserito nei repository Git).
Ecco le variabili richieste per far funzionare correttamente tutto il container:

### 🗄️ Connessione Database (MySQL)
Permettono all'applicazione Python di dialogare col container database o con un db esterno.
- `MYSQL_HOST`: L'hostname del db (se usi docker-compose solitamente è il nome del servizio db es. `mysql`, o un IP).
- `MYSQL_PORT`: La porta del database (normalmente `3306`).
- `MYSQL_USER`: L'utente del database.
- `MYSQL_PASSWORD`: La password del database.
- `MYSQL_DATABASE`: Il nome del database specifico (schema) utilizzato dall'app e in cui sono presenti le tabelle degli utenti e della piattaforma.

### 🔐 Sicurezza e Login (JWT)
Gestiscono la robustezza crittografica dei tuoi login sul portale.
- `SECRET_KEY`: Una lunga stringa alfanumerica causale, usata come "chiave di cifratura principale" per generare i pacchetti sicuri della sessione.
- `ALGORITHM`: L'algoritmo di firma crittografica. Usa `HS256` di default.
- `ACCESS_TOKEN_EXPIRE_MINUTES`: La durata di validità (espressa in minuti, ad esempio `30`) del login, dopo la quale dovrai ripetere l'accesso inserendo nome utente e password nel sito.

### 💻 Connessione SSH (Terminale Web)
Per permettere al terminale web integrato di collegarsi alla tua macchina vera senza chiederti la password ripetutamente, le credenziali vengono dichiarate qui. L'app fingerà di essere l'utente reale per permetterti di dare comandi tramite sito.
- `REMOTE_SSH_USER`: Il vero nome utente (es. `ciccio` o `admin`) che ha i privilegi sulla macchina fisica o sul server.
- `REMOTE_SSH_PASSWORD`: La password di sistema connessa a tale utente.
- `REMOTE_SSH_HOST`: L'indirizzo IP del server bersaglio. In setup virtuali, si usa spesso `172.17.0.1` per connettersi via proxy all'Host di Docker saltando l'isolamento della rete del container.
- `REMOTE_SSH_PORT`: La porta su cui il server host accetta connessioni SSH. Di default Linux usa la `22`, ma un setup custom potrebbe avere impostata un'altra porta (es. `4222`).
- `SSH_AUTO_ADD_HOST_KEY`: Va impostato a `true` per permettere al programma Python di bypassare le conferme manuali interattive di validità dei "known_hosts" al primo avvio.

---

## 🛠️ Come Utilizzarlo

1. **Accesso**: Carica la pagina web del portale ed esegui l'accesso coi dati dell'utente configurato in pancia al Database MySql.
2. **Dashboard Sensori (Pulse)**: Appena loggato, osserverai fin da subito che i Widget si colorano di statistiche verdi e i dati vengono aggiornati automaticamente dal worker in sottofondo in base all'uso speso dalle componenti Linux.
3. **Pannello Terminale Web**:
   - Clicca sul tasto azzurro **`Connect`** collocato nella Navbar in alto.
   - Il Socket aprirà un canale asincrono live verso il Server, facendoti atterrare nella console di accoglienza Linux.
   - Per un'esperienza più profonda o immersiva, specialmente dove è richiesto uso della tastiera lungo, **clicca sul bottone a freccia `<`** sul separatore al centro dello schermo. Il sito chiuderà il Widget Dashboard di sinistra e passerà il terminale in **modalità Full Screen**. Ripremi `>` per far rispuntare le metriche di sistema.
   - Clicca sul tasto grigio `+ Tab` se hai bisogno di aprire sessioni multiple per comandi multipli contemporaneamente, il server SSH regge istanze multiple parallele in Python.
4. **Chiusura dei Lavori**: Per questione di pulizia, clicca `Disconnect` prima di svuotare le schede o clicca direttamente `Logout` per disconnettere forzatamente i canali aperti chiudendo il tuo canale cifrato e rigettandoti nella pagina di sbarco Auth.

> ⚠️ RACCOMANDAZIONE SULLA PRODUZIONE: Assicurati di esporre `MyCloude` al mondo pubblico solo attraverso un proxy server come NGINX in aggiunta ad un certificato SSL (HTTPS). In assenza del prefisso `https://`, i tuoi pacchetti di login viaggiano sul server in chiaro e possono essere spiati da malintenzionati connessi nella stessa rete WIFI.
