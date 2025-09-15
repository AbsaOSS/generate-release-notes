### No entry 🚫
No entries detected.

### Breaking Changes 💥
No entries detected.

### New Features 🎉
- #3186 _Improve authorization in FeedManagement context_ in #3701
    - Improves and optimizes the authorization in the feed management context.
- #3207 _Allow Unify app admins and data ops roles to run TriggerManualExecutionCommand_ in #3762
    -  Added app-admins and data-ops to allowed users
- PR: #3303 _#3186-improve-authorization-in-feedmanagement-context_
    - Improves and optimizes the authorization in the feed management context.
- #3470 _FE: Ability to delete draft/testing version_ in #3663
- #3479 _Implement model layer domain major versions merge and mergeablility functionality_ in #3633
    - Introduces functionality related to merging of domain major versions to Domain model layer
- #3481 _Implement `MergeBackDomainMajorVersionCommand` handler_ in #3666
    - Introduces `MergeBackDomainMajorVersionCommandHandler` in domain-management bounded context

### Bugfixes 🛠
- #3637 _Partitions fetched from the glue catalog are not imported correctly_ in #3699
    - Fix importing partitions from glue table
- #3644 _Model validation failing after removal of non-latest major version_ in #3645
- #3683 _Owners and stewards cannot edit domain through UI if change involves PatchDomainCommand_ in #3692
    - fixed domain secondary owners and stewards not being able to edit certain domain properties through UI even though they should be authorized to do so (like description), by not performing authorization on `PatchDomainCommand` parts that didn't change but were sent in the request anyway
- #3714 _SchemaCompatibilityChecker should return incompatible when columns are being removed._ in #3733
    - Currently the SchemaCompatibilityChecker returns compatible if fields are removed but this can be seen as a breaking change to existing schema's, therefore it has been changed to return incompatible when fields are removed.
- #3726 _Output partition column is missing after editing target schema_ in #3743
    - Bug Fix: fix output partition column disappearing after editing target schema and add a dedicated Cypress scenario to prevent regressions.
- #3750 _Final DF is not cached in the Spark Job_ in #3751
    - removed cache on primary dataset DF and added one on final (post-interpretation) DF to improve dual-write performence
- #3756 _DB: Missing DB function permissions (ownership / execution)_ in #3757

### Infrastructure ⚙️
- PR: #3732 _Add UI team ownership for ci-ui-checks.yml_
- #3768 _Unify: Add business value chapter to issue templates_ in #3769

### Silent-live 🤫
No entries detected.

### Documentation 📜
- #3621 _Create an ADR for event-based domain scheduling_ in #3636

### New Epics
- Feature: _Promote from Pre-prod to prod and copy from Prod to IJAT_ #3655
- Feature: _Use Glue Tables explicitly as feed data sources_ #3674
- Feature: _Marking dataset ready for the current day and triggering runs_ #3686
- Feature: _`runs` topic events consumption_ #3687
- Feature: _Event-based scheduling mode selection_ #3688
- Feature: _Exclusion of data sources from the scheduling_ #3689

### Silent Live
- Epic: _Make formula builder more user-friendly_ #1188
- Epic: _Group By + Aggregations after Join(s)_ #1668
- Epic: _Add automation to GitHub project_ #1674
- Epic: _Implement data controls for foundation domains_ #1857
- Epic: _UI unit tests_ #2319
- Epic: _Update Cypress tests_ #2847
- Epic: _Manual once-off run for a range of dates_ #2873
- Epic: _Allow cross-account granting & revoking READ access to domain Glue tables_ #3006
- Feature: _Listing AWS accounts with access to a domain's Glue table_ #3246
- Feature: _Manually add Glue & Hive partitions when possible_ #3284
- Feature: _Allow active domain major version compatible schema evolution_ #3292
- Feature: _Country code selection for ARO_ #3297
- Feature: _Feed management - Delete data feed version_ #3457
- Epic: _Improve UI testing_ #3498
- Feature: _Revoking readonly access for domain's Glue tables to AWS account_ #3525
- Epic: _Update System tests_ #3571
- Feature: _PWD Rotation [dev] - keytab replacement and unify service rotation_ #3619

### Closed Epics
- Feature: _Include error message in failed runs endpoint and view_ #3426
- Feature: _Domain management - Delete domain version_ #3456
- Feature: _Sending events about runs to EventBus_ #3580
- Feature: _Create an ADR for Event-based scheduling of domains_ #3620

### Closed Issues without Pull Request ⚠️
- 🔔 Feature: _Include error message in failed runs endpoint and view_ #3426
- 🔔 Feature: _Domain management - Delete domain version_ #3456
- 🔔 Feature: _Sending events about runs to EventBus_ #3580
- 🔔 Feature: _Create an ADR for Event-based scheduling of domains_ #3620

### Closed Issues without User Defined Labels ⚠️
- #2836 _Fix ESLint config _ in #3731
- #3300 _Add `executionID` match assertions to domain major versions flow API tests_ in #3728, #3523
    - added tests in getJobs to assert executionID returned in response is evaluated to match actual vs expected
    - Timeout increased to wait few mins for eventual consistency
- 🔔 Feature: _Include error message in failed runs endpoint and view_ #3426
- #3483 _Handle `DomainMajorVersionMergedBackEvent` event in data-cataloging_ in #3696
    - Add and implement new service: `updateDomainMajorVersionLiveTables`
    - Add Appropriate controller endpoint for the above
    - Utilize the above in domainmajorversionmergedbackevent handler to update tables in place
    - Truncate and delete merging data after
    - implement tetst
- #3485 _Handle `DomainMajorVersionMergedBackEvent` in feed-management_ in #3573
    - Introduces `DomainMajorVersionMergedBackEventHandler` to handle `DomainMajorVersionMergedBackEvent`
    - Adds `feed_management.update_feeds_for_merged_domain_major_versions` plpgsql function that updates feed versions for domain major versions related to merge operation
- #3555 _Update Login e2e test_ in #3604
- #3630 _Remove redundant DTOs from DE bounded ctx_ in #3631
- #3640 _Migrate LDAP account to rotatable ssm param object_ in #3670, #3641
    - Unify LDAP service account credentials are now loaded from /datassets/{aul-dev|aul-uat|unify}/service-accounts/ad-service-account-credentials.
    - Unify LDAP service account credentials are now loaded from `/datassets/aul-dev/ad-service-account-credentials`.
- #3646 _Update Dashboard system test_ in #3668
- #3647 _Update Data-feed system test_ in #3673
- #3678 _Remove typescript files from /assets folder_ in #3677
- #3680 _DEV+UAT to share common non-prod service accounts space (config change)_ in #3681
    - Unify LDAP service account credentials for UAT and DEV are now loaded from `/datassets/aul-nonprod/service-accounts/ad-service-account-credentials`.
- #3690 _Implement DDL for the state management_ in #3711
- #3691 _Implement DB function for the state management_ in #3729
    * EventBus integration: implementing state management DB functions for reacting on incoming events and changes in domain automatic triggering
- #3703 _Implement BE DTO & API that will represent `ProcessAvailableDatasetCommand`_ in #3713
    - added `ProcessAvailableDatasetCommand` API (without implementation)
- #3705 _Make `DataSource#location` an ADT instead of String_ in #3715
    - Introduces possibility to define location of a data source by either using Glue table or S3 access point.
- #3716 _Add and implement `GetDomainMajorVersionDefaultDataSourcesQuery`_ in #3763
    - added `GetDomainMajorVersionDefaultDataSourcesQuery` which returns all data sources used in latest `Ready` feed versions for a given domain major version
- #3719 _Add event based scheduling option to `Schedule` DTO_ in #3727
    - added Schedule.DailyWindowEventBasedSchedule option of Schedule in domain-execution API
- #3721 _Implement DB function to upsert scheduling in EBS DB tables for a domain major version_ in #3760
- #3722 _Implement DB function to remove domain major version from EBS DB tables_ in #3759
- #3730 _Add an ESLint rule to check for skipped/focused unit tests_ in #3731
- #3740 _svc-ursa-unify accounts rotation support_ in #3748
    - webapp-svc-account credentials are now loaded from `/datassets/{aul-nonprod|unify}/service-accounts/spring-service-account-credentials`

### Merged PRs without Issue and User Defined Labels ⚠️
- PR: #3639 _#3638 Add location type to runs service, DB, and UI_
    - added location type (Live/Testing) for which a run was triggered to related endpoints and UI view
- PR: #3739 _rename db file_
- PR: #3752 _Add missing MergeBackDomainMajorVersionCommand to AuthorizationManager_
- PR: #3753 _Fix order of arguments in DomainMajorVersionMergedBack_
- PR: #3761 _api tests fixes_

### Closed PRs without Issue and User Defined Labels ⚠️
All closed PRs are linked to issues.

### Merged PRs Linked to 'Not Closed' Issue ⚠️
- 🔔 Epic: _Update System tests_ #3571

### Direct commits ⚠️
All direct commits are linked pull requests.

### Others - No Topic ⚠️
- 🔔 PR: #3303 _#3186-improve-authorization-in-feedmanagement-context_
    - Improves and optimizes the authorization in the feed management context.

#### Full Changelog
https://github.com/absa-group/AUL/compare/v1.2.0...v1.3.0
