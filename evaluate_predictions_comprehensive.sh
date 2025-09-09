#!/bin/bash
cd "$(dirname "$0")"
echo "$(date): Starting evaluation"
python -c "from fixed_outcome_evaluator import FixedOutcomeEvaluator; evaluator = FixedOutcomeEvaluator(); count = evaluator.evaluate_pending_predictions(); print(f'Evaluated {count} predictions')"
echo "$(date): Evaluation completed"