/*
  @autor: Ciccio Gancitano
  @date: 20/01/26

  @description:
    questa procedura serve a semplificare l'inserimento dei parametri nel codice
*/


DELIMITER //

CREATE OR REPLACE PROCEDURE insert_system_metrics(
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

DELIMITER ;
