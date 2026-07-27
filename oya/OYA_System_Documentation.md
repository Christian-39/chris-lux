OYA System Documentation
Okpo Youths Association Management System
Comprehensive Technical & Functional Overview
 
1. Executive Summary
The Okpo Youths Association Management System (OYA) is a production-ready, web-based association management platform built on Django 5.2+. It is designed specifically for the Okpo Youths Association to digitize and streamline all administrative, financial, electoral, and operational processes.
Purpose: To replace manual/paper-based association management with a centralized digital system that ensures accountability, transparency, and efficiency in managing members, finances, elections, projects, and day-to-day operations.
Target Users: - Administrators — Full system control, user management, settings configuration - Executives — Operational management of members, finances, projects, and elections - Floor Members — Self-service profile viewing and limited personal data editing
 
2. What the System Does
OYA serves as the single source of truth for the entire association. It handles:
1.	Identity & Access Management — Every user logs in with a unique serial number (e.g., OYA-2026-0001) and a 6-digit PIN. No passwords, no email-based auth.
2.	Membership Lifecycle — From registration to automatic status changes based on age (active members become past members at age 56).
3.	Financial Transparency — Every naira received (dues, donations, event fees) and every naira spent is recorded with receipts, categorized, and summarized.
4.	Project Tracking — Association projects are tracked from conception (Future) through execution (At Hand) to completion (Finished), with donation drives linked directly to projects.
5.	Democratic Elections — 4-year election cycles with candidate registration, manifesto storage, and handover ledger generation.
6.	Operational Accountability — Task force assignments, motorcycle fleet management, and case file tracking with resolution workflows.
7.	Audit Trail — Every significant action (create, update, delete, login, PIN reset) is logged with timestamps and IP addresses for full accountability.
 
3. Core Features & Capabilities
3.1 Authentication & Security
•	Serial Number-Based Login: Users authenticate with a unique association serial number and a 6-digit numeric PIN.
•	Custom Authentication Backend: SerialNumberAuthBackend handles credential verification independently of Django’s default username/password system.
•	PIN Hashing: All PINs are hashed using Django’s robust password hashing algorithms (not stored in plain text).
•	PIN Reset: Administrators can reset PINs for other users; resets are fully audited.
•	Session Management: 24-hour session expiry with secure cookie handling.
•	Role-Based Access Control (RBAC): Three distinct roles with granular permissions.
3.2 Member Management
•	Clan-Based Organization: Members are grouped into clans (Umu Nna), reflecting the community’s traditional structure.
•	Age-Based Automation: Members aged 18–55 are ACTIVE. Members who reach 56+ are automatically transitioned to PAST_MEMBER status via a management command.
•	Photo Upload: Members can have profile photos stored via cloud storage (Backblaze B2/S3).
•	Full CRUD: Admins and executives can register, update, and manage member records.
•	Male-Only Validation: The system enforces male-only membership during registration.
3.3 Executive Management
•	16 Executive Posts: Predefined roles (Chairman, Secretary, Treasurer, etc.) with full tenure tracking.
•	Tenure Lifecycle: Track when an executive starts, update records, and formally end tenures.
•	Current vs. Past: Clear distinction between current serving executives and past executives.
•	Handover Support: Integration with election handover ledgers for seamless power transitions.
3.4 Election Engine
•	4-Year Election Cycle: Configurable election cycle aligned with the association’s constitutional requirements.
•	Candidate Management: Register candidates with manifestos and campaign details.
•	Vote Counting: Record and tally votes per candidate.
•	Handover Ledger: Generate formal handover documents listing assets, financial status, and responsibilities transferred from outgoing to incoming executives.
3.5 Finance Engine
•	Income Tracking: Record all incoming funds with categorization:
–	DUES — Annual membership dues
–	DONATION — General donations
–	EVENT — Event-specific income
–	OTHER — Miscellaneous income
•	Expense Tracking: Record all expenditures with mandatory receipt uploads.
•	Treasury Balance: Real-time calculation of total income minus total expenses.
•	Financial Summaries: Dashboard-level aggregation of financial health.
•	Linked Records: Income records can be linked to specific dues payments or project donations for traceability.
3.6 Project Donations Engine
•	Project-Tied Donations: Donations are not just generic income — they are explicitly linked to specific association projects.
•	Automatic Income Creation: When a project donation is recorded, the system automatically creates a corresponding Income record in the Finance module, ensuring the treasury balance is always accurate without double entry.
•	Donor Flexibility: Supports both member donors (linked to their profile) and external/non-member donors (manual name entry).
•	Status Tracking: Donations move through statuses — Pending, Confirmed, Cancelled.
•	Project Summaries: View total donations raised per project, remaining budget needs, and donor lists.
3.7 Project Management
•	Three Status Levels:
–	Future — Planned but not yet started
–	At Hand — Currently in progress
–	Finished — Completed
•	Budget Tracking: Set project budgets and track spending against them.
•	Progress Percentage: Visual progress indicators for ongoing projects.
•	Lifecycle Management: Full CRUD from project creation to archival.
3.8 Operations Engine
•	Task Force Assignment: Assign members to specific operational task forces with role tracking.
•	Motorcycle Fleet Management: Track association motorcycles with condition statuses:
–	Excellent
–	Needs Service
–	Grounded
•	Case File Management: Track community/operational cases with statuses:
–	Open
–	In Progress
–	Resolved
•	Fine Tracking: Record and track fines associated with cases or operational violations.
3.9 Audit Logging
•	Comprehensive Action Logging: Every create, update, and delete action is logged automatically.
•	Login/Logout Tracking: Session events are recorded with IP addresses.
•	PIN Reset Logging: Security-sensitive actions like PIN resets are heavily audited.
•	IP Address Tracking: All audit entries capture the user’s IP for forensic purposes.
•	Module Coverage: Elections, finance, projects, cases, members, and user management actions are all logged.
3.10 Notifications System
•	Multi-Type Notifications: Info, Success, Warning, Error, and Alert types.
•	Global vs. User-Specific: Broadcast notifications to all users or target specific individuals.
•	Read/Unread Tracking: Users see unread notification badges; mark individual or all notifications as read.
•	In-App Delivery: No external email/SMS dependency; all notifications are delivered within the application.
3.11 Dashboard & Analytics
•	KPI Aggregation: Key metrics (total members, active executives, treasury balance, open cases, ongoing projects) are computed and cached.
•	Admin Dashboard: Specialized view for administrators with system-wide statistics and quick-action links.
•	Member Dashboard: Personalized view showing relevant notifications and profile status.
3.12 System Settings
•	Configurable Parameters: Currency symbol (₦), election cycle duration, minimum member age, past member age threshold, and serial number prefix are all configurable via the settings app.
•	Runtime Configuration: Admins can modify system behavior without code changes or redeployment.
3.13 Global Search
•	Q()-Based Search: Advanced search across all major modules using Django’s Q objects for complex, multi-field queries.
•	Cross-Module: Search members, executives, projects, finances, and cases from unified search interfaces.
3.14 Performance Optimizations
•	ORM Optimization: Extensive use of select_related and prefetch_related to eliminate N+1 query problems.
•	Database Indexing: Strategic indexes on status fields, foreign keys, search fields (serial_number, full_name), and date fields.
•	Caching: Redis-backed caching for dashboard KPIs and frequently accessed data.
•	Pagination: All list views are paginated to handle large datasets gracefully.
 
4. Architecture & Technology Stack
Layer	Technology
Backend Framework	Django 5.2+
Language	Python 3.11+
Database	MySQL 8.0 (utf8mb4 charset, InnoDB)
Cache	Redis (optional, for session/cache)
Task Queue	Celery (optional, for background jobs)
Static/Media Storage	Backblaze B2 / S3-compatible object storage
Web Server	Gunicorn (production)
Authentication	Custom SerialNumberAuthBackend
Currency	Nigerian Naira (₦)
4.1 Application Architecture (Modular Monolith)
The system follows Django’s app-based modular architecture:
oya/
├── accounts/           # Custom User model, serial auth, PIN management, RBAC
├── auditlogs/          # Action logging middleware, audit trail models
├── core/               # Base models, shared utilities, custom middleware,
│                       # exception handlers, permission classes
├── dashboard/          # KPI aggregation, cached statistics, dashboard views
├── elections/          # Election cycles, candidates, voting, handover ledgers
├── executives/         # Executive posts, tenure tracking, roster management
├── finance/            # Income, expenses, treasury balance, receipt uploads
├── members/            # Member profiles, clans, age-based status automation
├── notifications/      # In-app notification engine, read/unread tracking
├── operations/         # Task force, motorcycles, case files, fines
├── oya/                # Project settings, URLs, WSGI/ASGI config
├── projects/           # Project lifecycle, budget, progress tracking
├── project_donations/  # Project-specific donations, auto-income linkage
├── settingsapp/        # System-wide configurable parameters
└── templates/          # Shared HTML templates (base.html, etc.)
4.2 Key Design Patterns
1.	Custom User Model: Extends AbstractBaseUser with serial number as the unique identifier instead of email/username.
2.	AuditLog Middleware: Automatically intercepts requests and logs create/update/delete actions without developers manually adding logging code to every view.
3.	Soft Deletes: Records are marked as removed rather than permanently deleted, preserving data integrity and audit trails.
4.	Service Layer: Business logic is encapsulated in service modules (e.g., finance services, member services) rather than bloating views.
5.	Custom Permissions: Fine-grained permission classes (has_admin_access, is_executive, etc.) control access at the view and template level.
6.	Context Processors: Global template variables (unread notifications, system settings, user member profile) are injected automatically.
 
5. User Roles & Permission Matrix
5.1 Administrator (Admin)
•	Scope: Full system access
•	Capabilities:
–	Create, update, delete any record across all modules
–	Access and modify System Settings
–	Manage user roles and permissions
–	Reset any user’s PIN
–	Assign task force members
–	View the Admin Dashboard with system-wide KPIs
–	Access and filter Audit Logs
–	Delete income/expense records (with audit trail)
5.2 Executive
•	Scope: Operational management
•	Capabilities:
–	CRUD access to members, finances, projects, operations, and elections
–	Cannot access System Settings
–	Cannot manage user permissions or roles
–	Can view Audit Logs (read-only)
–	Can create and manage project donations
–	Cannot delete critical financial records (varies by implementation)
5.3 Floor Member
•	Scope: Self-service and viewing
•	Capabilities:
–	View-only access to most modules
–	Edit own phone number and state of residence
–	Cannot access admin URLs or settings
–	View own profile and membership status
–	View public projects, elections, and notifications
–	Cannot create, edit, or delete any association records
 
6. Detailed Module Workflows
6.1 Member Registration & Lifecycle Workflow
[Admin/Executive] → Create Member Record
    ↓
[Validation] → Check age (must be male, 18+)
    ↓
[Clan Assignment] → Assign to Umu Nna (Clan)
    ↓
[Status Assignment] → ACTIVE (if 18-55) or PAST_MEMBER (if 56+)
    ↓
[User Account] → Auto-create login account with serial number
    ↓
[Ongoing] → Annual dues tracking, event participation
    ↓
[Age 56+] → Management command updates status to PAST_MEMBER
    ↓
[Audit Log] → All actions logged with IP and timestamp
6.2 Financial Recording Workflow
[Income Recording]
Admin/Executive records income → Specify type (DUES/DONATION/EVENT/OTHER)
    ↓
If DUES → Link to specific member's dues payment record
If PROJECT DONATION → Auto-create income linked to project
    ↓
Treasury Balance auto-recalculated
    ↓
Audit log entry created

[Expense Recording]
Admin/Executive records expense → Upload mandatory receipt
    ↓
Categorize expense
    ↓
Treasury Balance auto-recalculated
    ↓
Audit log entry created
6.3 Project Donation Workflow
[Create Project Donation]
User selects a Project → Enters donor details (member or external)
    ↓
Enters amount and donation status (Pending/Confirmed/Cancelled)
    ↓
[System Action] → Auto-creates Income record in Finance module
    ↓
Income is linked back to the Project Donation for traceability
    ↓
Project's total donation amount is updated
    ↓
Audit log entry created
    ↓
[Viewing] → Income detail page shows linked project donation
6.4 Election Workflow
[Schedule Election]
Admin creates election → Sets date and positions
    ↓
[Candidate Registration]
Members register as candidates → Upload manifesto
    ↓
[Voting Phase]
Votes are recorded per candidate
    ↓
[Results]
Vote counts tallied → Winners determined
    ↓
[Handover]
Handover ledger generated → Outgoing executives transfer assets
    ↓
Audit log tracks every stage
6.5 Case File Resolution Workflow
[Create Case]
Admin/Executive logs case → Status: OPEN
    ↓
[Investigation]
Status updated to: IN PROGRESS
    ↓
[Resolution]
Status updated to: RESOLVED
    ↓
Fines recorded (if applicable)
    ↓
Audit log tracks status changes and assignments
 
7. Data Flows & Integrations
7.1 Internal Data Flows
Source Module	Target Module	Data Flow
project_donations	finance	Auto-creates Income record when donation is confirmed
members	finance	Member linked to dues payments and income records
members	executives	Member promoted to executive post with tenure
executives	elections	Current executives referenced in handover ledgers
finance	dashboard	Income/expense totals feed KPI calculations
projects	project_donations	Project receives donation totals and donor lists
operations	auditlogs	Case resolutions and task force changes are logged
7.2 External Integrations
•	Cloud Storage (Backblaze B2): Receipts, member photos, and manifesto documents are stored in S3-compatible object storage rather than local disk.
•	Redis: Optional caching layer and Celery message broker for background tasks.
•	MySQL: Primary relational database with optimized indexing and strict SQL mode.
 
8. Security & Compliance Features
1.	CSRF Protection: All state-changing forms include CSRF tokens.
2.	X-Frame-Options: Set to DENY to prevent clickjacking.
3.	Secure Headers: XSS filter and content-type nosniff enabled.
4.	Environment-Based Secrets: Database credentials, secret keys, and AWS keys are loaded from environment variables, never hardcoded.
5.	Audit Immutability: Audit logs are write-only; no user (including admins) can modify or delete audit entries.
6.	Permission Decorators: Views are protected with @login_required and custom role checks.
7.	Input Sanitization: Django’s ORM prevents SQL injection; templates auto-escape HTML to prevent XSS.
 
9. Notable Business Rules
1.	Male-Only Membership: The system enforces male gender during member registration.
2.	Age Brackets: Active membership is strictly 18–55. Past member status triggers at 56.
3.	Mandatory Receipts: Expense records cannot be created without an uploaded receipt.
4.	Auto-Income: Project donations automatically generate finance income records — no manual double-entry.
5.	Serial Number Format: All user serial numbers follow OYA-YYYY-XXXX format.
6.	4-Year Election Cycle: Hard-coded constitutional cycle for executive elections.
7.	16 Executive Posts: The executive roster has exactly 16 predefined positions.
 
10. Deployment & Operations
10.1 Development Setup
python manage.py runserver
10.2 Production Deployment
python manage.py collectstatic --noinput
gunicorn oya.wsgi:application --bind 0.0.0.0:8000 --workers 4
10.3 Background Tasks (Optional)
celery -A oya worker --loglevel=info
celery -A oya beat --loglevel=info
10.4 Maintenance Commands
# Update member statuses (run periodically via cron or Celery beat)
python manage.py update_member_status

# Seed sample data for testing
python manage.py seed_data --flush
 
11. Summary
The Okpo Youths Association Management System is a comprehensive, audit-ready, role-based digital platform that covers the full spectrum of association management:
•	Who it serves: Okpo Youths Association members, executives, and administrators.
•	What it does: Manages membership, finances, elections, projects, donations, operations, and accountability.
•	Why it matters: Eliminates manual record-keeping, ensures financial transparency, automates age-based status changes, secures democratic elections, and maintains an immutable audit trail for all actions.
•	How it works: Django 5.2+ monolith with modular apps, MySQL database, optional Redis caching, cloud-backed file storage, and a custom serial-number authentication system.
This system transforms association management from scattered spreadsheets and paper files into a unified, searchable, secure, and auditable digital platform.
 
Document Version: 1.0 System: OYA (Okpo Youths Association Management System) Framework: Django 5.2+ | Python 3.11+ | MySQL 8.0
