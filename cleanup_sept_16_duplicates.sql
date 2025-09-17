
    -- Keep only one outcome per unique entry/exit price combination per day
    -- This preserves the most recent evaluation for each price pattern
    
    DELETE FROM outcomes 
    WHERE outcome_id NOT IN (
        SELECT MAX(outcome_id) 
        FROM outcomes 
        WHERE DATE(evaluation_timestamp) = '2025-09-16'
        GROUP BY ROUND(entry_price, 2), ROUND(exit_price, 2), ROUND(actual_return, 4)
    )
    AND DATE(evaluation_timestamp) = '2025-09-16';
    