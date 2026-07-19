# Meaning-risk policy

Meaning-risk weights express communicative priority, not speaker quality or linguistic importance.

## Initial levels

| Weight | Definition |
|---:|---|
| 1.00 | The unit belongs to a verified contrast where a tone change can change lexical or grammatical interpretation. |
| 0.50 | Tone is important for intelligibility, but no controlled alternative is documented in this release. |
| 0.25 | Ordinary contextual tone target without a documented high-risk contrast. |

## Assignment rules

- derive high-risk status from frozen contrast groups;
- document the intended meanings on both sides of a contrast;
- never infer a high-risk label solely from an AI system's error;
- require fluent-speaker review before release;
- freeze weights before model training;
- report an all-weights-equal ablation.

The numerical values are provisional hyperparameters. The scientific claim concerns predeclared differential weighting, not the optimality of these exact constants.

