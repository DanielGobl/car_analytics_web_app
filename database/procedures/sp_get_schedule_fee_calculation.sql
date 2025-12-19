USE `routing_slips_data`;
DROP procedure IF EXISTS `sp_get_schedule_fee_calculation`;

USE `routing_slips_data`;
DROP procedure IF EXISTS `routing_slips_data`.`sp_get_schedule_fee_calculation`;
;

DELIMITER $$
USE `routing_slips_data`$$
CREATE PROCEDURE `sp_get_schedule_fee_calculation`(p_id_location BIGINT, p_coinsurance_prct VARCHAR(10))
this_proc: BEGIN
	-- ------------------------------------------------------------
	-- Action: GET
	-- To do: Select
	-- Target: GUI
	-- Triggered: GUI
	-- ------------------------------------------------------------
	-- Changes:
    -- 12/19/2025 - [DT-3424] - DGobl - create

	DECLARE v_proc_start_time DATETIME(3) DEFAULT NOW();
	DECLARE v_proc_name VARCHAR(255) DEFAULT 'routing_slips_data.sp_get_schedule_fee_calculation';
	DECLARE v_coinsurance_prct DECIMAL(6,4);

    DECLARE CONTINUE HANDLER FOR SQLEXCEPTION
    BEGIN
    GET DIAGNOSTICS CONDITION 1
        @err_no = MYSQL_ERRNO,
        @mes_text = MESSAGE_TEXT;
        CALL system_admin_db.sp_handle_error(v_proc_name , v_proc_start_time , NOW(3), @err_no, @mes_text, 'Exception');
        RESIGNAL;
    END;

	DECLARE CONTINUE HANDLER FOR SQLWARNING
	BEGIN
	GET DIAGNOSTICS CONDITION 1
		@err_no = MYSQL_ERRNO,
		@mes_text = MESSAGE_TEXT;
		IF @err_no <> 3237 THEN
			CALL system_admin_db.sp_handle_error(v_proc_name, v_proc_start_time, NOW(3), @err_no, @mes_text, 'Warning');
			RESIGNAL;
		END IF;
	END;

    IF p_coinsurance_prct IS NULL OR p_coinsurance_prct NOT REGEXP '^[0-9]{1,2}%$|^100%$' THEN
        LEAVE this_proc;
    END IF;

    SET v_coinsurance_prct = (CAST(TRIM(REPLACE(p_coinsurance_prct, '%', '')) AS DECIMAL(6,2)) / 100);

    SELECT
        cfs.cpt_code,
        ROUND(cfs.fee_amount * v_coinsurance_prct, 2) AS calculated_copay
    FROM routing_slips_data.cpt_fee_schedule cfs
    JOIN routing_slips_data.practice_fee_schedule pfs
        ON cfs.fee_schedule = pfs.fee_schedule
	JOIN customer_data.tb_offices o
		ON pfs.office_num = o.office_num
    WHERE o.id_location = p_id_location
    ORDER BY
        CASE
            WHEN cfs.cpt_code LIKE '92%' THEN 1
            WHEN cfs.cpt_code LIKE '99%' THEN 2
            ELSE 3
        END,
        cfs.cpt_code ASC;

END$$

DELIMITER ;
;
