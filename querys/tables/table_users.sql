/*
  @autor: Ciccio Gancitano
  @date: 20/01/26

  @description:
    questa tabella ha lo scopo di registrare gli utenti e le loro attività
    quando si sono registrati, ultima sessione, ultimo ip etc
*/


CREATE TABLE users (
    -- ID univoco per ogni utente
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    
    -- Credenziali di base
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    
    -- Livelli di accesso personalizzati
    user_level ENUM('guest', 'ciccio') NOT NULL DEFAULT 'guest',
    
    -- Stato dell'account (1 = Attivo, 0 = Disattivato)
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    
    -- Tracciamento dell'ultimo accesso
    last_login DATETIME DEFAULT NULL,
    -- VARCHAR(45) per supportare sia IPv4 che IPv6
    last_ip VARCHAR(45) DEFAULT NULL,
    
    -- Data di creazione dell'account
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
























