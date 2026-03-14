USE mycloude;

-- this table is the "core" it registers raw hardware resources data
-- some data are saved as numbers and others like disk_usage_pct are stored as a formula
-- just to save a bit of memory
-- it will save even a status of the resources, and it can be ok, warning or CRITICAL
-- i put so I can register if any spike appened during my work

CREATE TABLE IF NOT EXISTS resource_usage (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    cpu_usage DECIMAL(5, 2) NOT NULL,
    cpu_temp DECIMAL(4, 1) NOT NULL,
    ram_used_mb INT UNSIGNED NOT NULL,
    ram_total_mb INT UNSIGNED NOT NULL,
    ram_usage_pct DECIMAL(5, 2) AS ((ram_used_mb / ram_total_mb) * 100) VIRTUAL,
    disk_used_mb BIGINT UNSIGNED NOT NULL,
    disk_total_mb BIGINT UNSIGNED NOT NULL,
    disk_usage_pct DECIMAL(5, 2) AS ((disk_used_mb / disk_total_mb) * 100) VIRTUAL,
    net_in_kbps INT UNSIGNED NOT NULL DEFAULT 0,
    net_out_kbps INT UNSIGNED NOT NULL DEFAULT 0,
    status VARCHAR(10) AS (
        CASE
            WHEN cpu_usage > 90 OR cpu_temp > 80 OR (ram_used_mb / ram_total_mb) > 0.95 OR (disk_used_mb / disk_total_mb) > 0.95 THEN 'CRITICAL'
            WHEN cpu_usage > 70 OR cpu_temp > 70 OR (ram_used_mb / ram_total_mb) > 0.80 OR (disk_used_mb / disk_total_mb) > 0.85 THEN 'WARNING'
            ELSE 'OK'
        END
    ) VIRTUAL,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    INDEX idx_recorded_at (recorded_at),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- this table is only used to store user data
CREATE TABLE IF NOT EXISTS users (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DELIMITER //

-- this procedure is used to insert system metrics into the database
-- it is called by the python script every 2 seconds
CREATE PROCEDURE insert_system_metrics(
    p_cpu FLOAT,
    p_temp FLOAT,
    p_ram_u INT,
    p_ram_t INT,
    p_disk_u INT,
    p_disk_t INT,
    p_net_in INT,
    p_net_out INT
)
BEGIN
    INSERT INTO resource_usage (
        cpu_usage,
        cpu_temp,
        ram_used_mb,
        ram_total_mb,
        disk_used_mb,
        disk_total_mb,
        net_in_kbps,
        net_out_kbps
    ) VALUES (
        p_cpu,
        p_temp,
        p_ram_u,
        p_ram_t,
        p_disk_u,
        p_disk_t,
        p_net_in,
        p_net_out
    );
END //

-- this procedure is used to get the system status
-- it is called by the python script every 2 seconds
CREATE PROCEDURE get_system_status()
BEGIN
    SELECT
        cpu_usage AS cpu,
        cpu_temp AS temp,
        ram_usage_pct AS ram,
        disk_usage_pct AS disk,
        net_in_kbps AS net_in,
        net_out_kbps AS net_out,
        status
    FROM resource_usage
    ORDER BY recorded_at DESC
    LIMIT 1;
END //

-- this procedure is used to get the user by username
-- it's used mainly for the login
CREATE PROCEDURE get_user_by_username(IN p_username VARCHAR(50))
BEGIN
    SELECT
        id,
        username,
        password_hash
    FROM users
    WHERE username = p_username;
END //

CREATE PROCEDURE insert_user(
    p_username VARCHAR(50),
    p_password_hash VARCHAR(255)
)
BEGIN
    INSERT INTO users (
        username,
        password_hash
    ) VALUES (
        p_username,
        p_password_hash
    );
END //

DELIMITER ;
