## REMOVED Requirements

### Requirement: Strike full-chain validation SHALL reject stale mission-progress readings after mission replacement
**Reason**: Mission replacement and temporary attack missions have been eliminated. There is no longer a need to sync mission sequence progress across dynamic uploads.
**Migration**: Validation runs naturally test the continuous preburned mission + GUIDED takeover.
