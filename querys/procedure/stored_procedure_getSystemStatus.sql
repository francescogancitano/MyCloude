/*
  @autor: Ciccio Gancitano
  @date: 20/01/26

  @description:
    questa è una stored procedure che serve a sapere lo stato del sistema
*/

DELIMITER //

CREATE OR REPLACE PROCEDURE get_system_status()
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

DELIMITER ;
