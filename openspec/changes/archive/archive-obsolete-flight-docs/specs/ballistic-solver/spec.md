## REMOVED Requirements

### Requirement: ballistic-solver calculations
**Reason**: Striker assumes the provided external coordinate is the absolute spatial release point. Ballistic compensation is no longer part of the Striker runtime execution loop.
**Migration**: External systems (e.g., vision processing) are responsible for solving ballistics before submitting the coordinate to Striker.
