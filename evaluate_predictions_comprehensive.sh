#!/bin/bash
cd /root/test
echo "$(date): Starting evaluation"
python3 -c "from fixed_outcome_evaluator import FixedOutcomeEvaluator; evaluator = FixedOutcomeEvaluator(); count = evaluator.evaluate_pending_predictions(); print(f'Evaluated {count} predictions')"
echo "$(date): Evaluation completed"