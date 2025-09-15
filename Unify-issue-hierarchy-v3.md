### No entry 🚫
No entries detected.

### Breaking Changes 💥
No entries detected.

### New Features 🎉
- PR: #3303 _#3186-improve-authorization-in-feedmanagement-context_
    - Improves and optimizes the authorization in the feed management context.

### Bugfixes 🛠
No entries detected.

### Infrastructure ⚙️
No entries detected.

### Silent-live 🤫
No entries detected.

### Documentation 📜
No entries detected.

### New Epics
- Feature: _Promote from Pre-prod to prod and copy from Prod to IJAT_ #3655

### Silent Live Epics
- Epic: _Make formula builder more user-friendly_ #1188
- Epic: _Implement some of the missing info about individual domains_ #1343
- Epic: _Group By + Aggregations after Join(s)_ #1668
- Epic: _Add automation to GitHub project_ #1674
- Epic: _Implement data controls for foundation domains_ #1857
- Epic: _UI unit tests_ #2319
- Epic: _Update Cypress tests_ #2847
    - #3555 _Update Login e2e test_ in #3604
- Epic: _Manual once-off run for a range of dates_ #2873
- Epic: _Support AD security group access assignment for domain roles and consumers_ #2883
- Epic: _Event-based scheduling MVP _ #2960
    - Feature: _Sending events about runs to EventBus_ #3580
        - #3638 _Add location type into GetJobRunsResult and GetJobErrorDetailsResult_ in
    - Feature: _Create an ADR for Event-based scheduling of domains_ #3620
        - #3621 _Create an ADR for event-based domain scheduling_ in #3636
        - #3622 _Consult an ADR about event-based domain scheduling with the team for having the consensus_ in
    - Feature: _Use Glue Tables explicitly as feed data sources_ #3674
        - #3705 _Make `DataSource#location` an ADT instead of String_ in #3715
            - Introduces possibility to define location of a data source by either using Glue table or S3 access point.
    - Feature: _Marking dataset ready for the current day and triggering runs_ #3686
        - #3690 _Implement DDL for the state management_ in #3711
        - #3691 _Implement DB function for the state management_ in #3729
            * EventBus integration: implementing state management DB functions for reacting on incoming events and changes in domain automatic triggering
        - #3702 _Implement DB function that resets the domain freshness_ in
        - #3703 _Implement BE DTO & API that will represent `ProcessAvailableDatasetCommand`_ in #3713
            - added `ProcessAvailableDatasetCommand` API (without implementation)
    - Feature: _Event-based scheduling mode selection_ #3688
        - #3716 _Add and implement `GetDomainMajorVersionDefaultDataSourcesQuery`_ in #3763
            - added `GetDomainMajorVersionDefaultDataSourcesQuery` which returns all data sources used in latest `Ready` feed versions for a given domain major version
        - #3719 _Add event based scheduling option to `Schedule` DTO_ in #3727
            - added Schedule.DailyWindowEventBasedSchedule option of Schedule in domain-execution API
        - #3721 _Implement DB function to upsert scheduling in EBS DB tables for a domain major version_ in #3760
        - #3722 _Implement DB function to remove domain major version from EBS DB tables_ in #3759
    - Feature: _`runs` topic events consumption_ #3687
    - Feature: _Exclusion of data sources from the scheduling_ #3689
- Epic: _Allow cross-account granting & revoking READ access to domain Glue tables_ #3006
    - Feature: _Listing AWS accounts with access to a domain's Glue table_ #3246
    - Feature: _Revoking readonly access for domain's Glue tables to AWS account_ #3525
- Epic: _Solution for externalized configs_ #3201
- Epic: _Send execution completion events to an tenant-specified SQS queue_ #3203
- Epic: _API 1-shot test - reach 100% coverage_ #3206
- Epic: _Setup Glue jobs and enable running the Spark compute engine on Glue_ #3219
- Epic: _Enable ARO Data segregation - RTSIS (Tanzania ABT requirement)_ #3251
    - Feature: _Country code selection for ARO_ #3297
- Epic: _Display overall stats on the landing page_ #3262
- Feature: _Manually add Glue & Hive partitions when possible_ #3284
- Feature: _Allow active domain major version compatible schema evolution_ #3292
    - #3479 _Implement model layer domain major versions merge and mergeablility functionality_ in #3633
        - Introduces functionality related to merging of domain major versions to Domain model layer
    - #3481 _Implement `MergeBackDomainMajorVersionCommand` handler_ in #3666
        - Introduces `MergeBackDomainMajorVersionCommandHandler` in domain-management bounded context
    - #3483 _Handle `DomainMajorVersionMergedBackEvent` event in data-cataloging_ in #3696
        - Add and implement new service: `updateDomainMajorVersionLiveTables`
        - Add Appropriate controller endpoint for the above
        - Utilize the above in domainmajorversionmergedbackevent handler to update tables in place
        - Truncate and delete merging data after
        - implement tetst
    - #3485 _Handle `DomainMajorVersionMergedBackEvent` in feed-management_ in #3573
        - Introduces `DomainMajorVersionMergedBackEventHandler` to handle `DomainMajorVersionMergedBackEvent`
        - Adds `feed_management.update_feeds_for_merged_domain_major_versions` plpgsql function that updates feed versions for domain major versions related to merge operation
    - #3714 _SchemaCompatibilityChecker should return incompatible when columns are being removed._ in #3733
        - Currently the SchemaCompatibilityChecker returns compatible if fields are removed but this can be seen as a breaking change to existing schema's, therefore it has been changed to return incompatible when fields are removed.
- Feature: _Feed management - Delete data feed version_ #3457
- Epic: _Improve UI testing_ #3498
- Feature: _PWD Rotation [dev] - keytab replacement and unify service rotation_ #3619
    - #3640 _Migrate LDAP account to rotatable ssm param object_ in #3670, #3641
        - Unify LDAP service account credentials are now loaded from /datassets/{aul-dev|aul-uat|unify}/service-accounts/ad-service-account-credentials.
        - Unify LDAP service account credentials are now loaded from `/datassets/aul-dev/ad-service-account-credentials`.
    - #3643 _Create UAT+PROD ldap-svc records_ in
    - #3680 _DEV+UAT to share common non-prod service accounts space (config change)_ in #3681
        - Unify LDAP service account credentials for UAT and DEV are now loaded from `/datassets/aul-nonprod/service-accounts/ad-service-account-credentials`.
    - #3660 _Migrate hive-keytab usage to password-rotation compatible location_ in
    - #3661 _Employ password/keytab rotation solution_ in
    - #3662 _Create a wokflow integrating rotation step_ in
    - #3693 _setup hive-service account params in param store to be rotated_ in
    - #3741 _Manual rotation of `svc-ursa-unify-prd` and `svc-ursa-aul-dev`_ in
    - #3740 _svc-ursa-unify accounts rotation support_ in #3748
        - webapp-svc-account credentials are now loaded from `/datassets/{aul-nonprod|unify}/service-accounts/spring-service-account-credentials`

### Closed Epics
- Feature: _Include error message in failed runs endpoint and view_ #3426
- Feature: _Domain management - Delete domain version_ #3456
    - #3470 _FE: Ability to delete draft/testing version_ in #3663
    - #3644 _Model validation failing after removal of non-latest major version_ in #3645

### Closed Issues without Pull Request ⚠️
- Feature: _Include error message in failed runs endpoint and view_ #3426
- Feature: _Domain management - Delete domain version_ #3456
    - #3470 _FE: Ability to delete draft/testing version_ in #3663
    - #3644 _Model validation failing after removal of non-latest major version_ in #3645

### Closed Issues without User Defined Labels ⚠️
- Feature: _Include error message in failed runs endpoint and view_ #3426

### Merged PRs without Issue and User Defined Labels ⚠️
- PR: #3639 _#3638 Add location type to runs service, DB, and UI_
    - added location type (Live/Testing) for which a run was triggered to related endpoints and UI view

### Closed PRs without Issue and User Defined Labels ⚠️
All closed PRs are linked to issues.

### Merged PRs Linked to 'Not Closed' Issue ⚠️
All merged PRs are linked to Closed issues.

### Direct commits ⚠️
All direct commits are linked pull requests.

### Others - No Topic ⚠️
- PR: #3303 _#3186-improve-authorization-in-feedmanagement-context_
    - Improves and optimizes the authorization in the feed management context.
- PR: #3639 _#3638 Add location type to runs service, DB, and UI_
    - added location type (Live/Testing) for which a run was triggered to related endpoints and UI view

#### Full Changelog
https://github.com/absa-group/AUL/compare/v1.2.0...v1.3.0
