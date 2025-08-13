#!/bin/bash
cd /root/test
python3 -c "
from data_quality_system.core.true_prediction_engine import OutcomeEvaluator
evaluator = OutcomeEvaluator()
count = evaluator.evaluate_pending_predictions()
print(f'Evaluated {count} pending predictions')
" >> logs/evaluation.log 2>&1
