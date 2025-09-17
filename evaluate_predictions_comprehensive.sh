#!/bin/bash
cd /root/test
echo "$(date): Starting evaluation with CORRECTED pricing logic"
python3 -c "from corrected_outcome_evaluator_updated import CorrectedOutcomeEvaluator; evaluator = CorrectedOutcomeEvaluator(); count = evaluator.run_corrected_evaluation(); print(f'Evaluated {count} predictions with corrected pricing')"
echo "$(date): Evaluation completed"
