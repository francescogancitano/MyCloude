/*
  @autor: Ciccio Gancitano
  @date: 20/01/26

  @description:
      questa tabella ha lo scopo di registrare le attività delle risorse del computer.
      Con lo scopo di essere utilizzata per un piccolo servizio di cloude
      
      la seguente tabella registra:

      l'utilizzo di CPU e la sua temperatura
      l'utilizzo di RAM in megabyte e in percentuale
      l'utilizzo del disco in megabyte e in percentuale
      il traffico di rete 
      lo stato del computer (OK, WARNING, CRITICAL)
*/


CREATE TABLE resource_usage (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,

    -- CPU e Temperatura
    cpu_usage DECIMAL(5, 2) NOT NULL,
    cpu_temp DECIMAL(4, 1) NOT NULL, 

    -- RAM (Megabyte)
    ram_used_mb INT UNSIGNED NOT NULL,
    ram_total_mb INT UNSIGNED NOT NULL,
    ram_usage_pct DECIMAL(5, 2) AS ((ram_used_mb / ram_total_mb) * 100) VIRTUAL,

    -- DISCO (Megabyte - BIGINT per supportare oltre i 4TB)
    disk_used_mb BIGINT UNSIGNED NOT NULL,
    disk_total_mb BIGINT UNSIGNED NOT NULL,
    disk_usage_pct DECIMAL(5, 2) AS ((disk_used_mb / disk_total_mb) * 100) VIRTUAL,

    -- RETE (KB/s)
    net_in_kbps INT UNSIGNED NOT NULL DEFAULT 0,
    net_out_kbps INT UNSIGNED NOT NULL DEFAULT 0,

    -- STATUS AUTOMATICO
    -- Una riga è CRITICAL se: CPU > 90% o Temp > 80°C o RAM > 95% o Disco > 95%
    status VARCHAR(10) AS (
        CASE
            WHEN cpu_usage > 90 OR cpu_temp > 80 OR (ram_used_mb / ram_total_mb) > 0.95 OR (disk_used_mb / disk_total_mb) > 0.95 THEN 'CRITICAL'
            WHEN cpu_usage > 70 OR cpu_temp > 70 OR (ram_used_mb / ram_total_mb) > 0.80 OR (disk_used_mb / disk_total_mb) > 0.85 THEN 'WARNING'
            ELSE 'OK'
        END
    ) VIRTUAL,

    -- Timestamp
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    -- Unico indice necessario per i report temporali
    INDEX idx_recorded_at (recorded_at),
    -- Indice per estrarre velocemente solo gli errori
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
