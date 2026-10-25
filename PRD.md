# Product Requirements Document (PRD)
## AI-Based Timetable Scheduler

| Document Attribute | Details |
|---|---|
| Project Title | AI-Based Timetable Scheduler |
| Document Version | 1.0 |
| Document Status | Draft — Proposed for Academic Project Approval |
| Project Category | Artificial Intelligence / Constraint Optimization / Academic Software |
| Target Platform | Web Application |
| Primary Technology | Python, Streamlit |
| Intended Audience | Project Team, Faculty Guide, Academic Evaluators, Developers, Testers |
| Document Owner | Project Team |
| Last Updated | 24 October 2026 |

---

# A. Document Information

## A.1 Purpose

This Product Requirements Document defines the functional behavior, business rules, user requirements, evaluation criteria, and acceptance conditions for the AI-Based Timetable Scheduler.

The document establishes what the application must accomplish and how its successful completion will be evaluated.

It is intended to serve as the primary reference for:
- Project planning and prioritization.
- Functional implementation.
- Dataset preparation.
- Algorithm development and integration.
- User interface development.
- Testing and validation.
- Experimental evaluation.
- Academic demonstration and reporting.

This document specifies product requirements rather than detailed implementation architecture. Source code, internal module design, class structures, API contracts, and low-level technical decisions will be documented separately in the Technical Requirements Document (TRD).

## A.2 Requirement Classification

Requirements are categorized according to their implementation priority.

| Priority | Meaning |
|---|---|
| Must Have | Essential for a usable and academically complete minimum viable product. |
| Should Have | Important functionality that should be implemented after essential requirements. |
| Could Have | Optional functionality that improves the product but is not essential to the minimum viable product. |
| Won't Have | Explicitly excluded from the current project scope. |

A priority designation describes implementation importance, not the difficulty of implementing a feature.

## A.3 Requirement Status

The following distinctions apply throughout this document:

- **Project requirement:** A capability explicitly included in the project brief.
- **Proposed assumption:** A decision suggested to make the project implementable and testable. It requires confirmation where appropriate.
- **Open question:** A decision that must be resolved before the relevant implementation or final evaluation.

The inclusion of a requirement in this PRD does not imply that it has already been implemented or tested.

---

# B. Executive Summary

## B.1 Overview

Academic timetable scheduling is a constraint-intensive planning problem. Educational institutions must assign classes, teachers, subjects, rooms, and time slots while respecting availability, workload limits, room suitability, subject-hour requirements, and other institutional rules.

Preparing timetables manually becomes increasingly difficult as the number of classes, teachers, rooms, and teaching sessions increases. Manual scheduling also makes it difficult to compare alternatives, identify conflicts, and consistently optimize teacher and student preferences.

The AI-Based Timetable Scheduler will provide an interactive application that automatically generates and evaluates academic timetables using Artificial Intelligence and search-based optimization techniques.

The application will be developed using Python and Streamlit. Users will be able to upload or configure datasets, validate scheduling inputs, select an algorithm, generate a timetable, inspect constraint violations, compare algorithm performance, manually edit schedules, and export the results.

## B.2 Proposed Solution

The application will model timetable generation as a Constraint Satisfaction Problem (CSP).

The primary algorithm will be a backtracking CSP solver enhanced with:

- Minimum Remaining Values (MRV).
- Degree Heuristic.
- Forward Checking.

The application will also support Min-Conflicts local search. Simulated Annealing and a Hybrid CSP + Simulated Annealing approach will be treated as bonus algorithms.

A separate constraint validator will evaluate the generated timetable independently of the scheduling algorithm. This separation is important because a solver's reported success must not be accepted as proof that its output is valid.

The system will distinguish between:

1. **Hard constraints:** Rules that must be satisfied for a timetable to be considered valid.
2. **Soft constraints:** Preferences that influence timetable quality but may be violated when necessary.

The scheduling process must prioritize hard-constraint satisfaction. Soft-constraint optimization must not silently turn a hard constraint into an optional preference.

## B.3 Target Users

The primary users are:

- Academic administrators.
- Timetable coordinators.
- Teachers.
- Students.
- Project evaluators.

The initial product is an academic prototype rather than a production university information system.

## B.4 Expected Outcome

The completed project is expected to demonstrate:

1. A working interactive timetable scheduling application.
2. A formal CSP representation of academic scheduling.
3. Multiple scheduling and optimization algorithms.
4. Independent hard-constraint validation.
5. Soft-constraint scoring.
6. Class-wise, teacher-wise, and room-wise timetable views.
7. Manual editing with automatic revalidation.
8. CSV and Excel export.
9. Reproducible experiments comparing algorithms on defined datasets.
10. A documented evaluation of algorithm strengths, limitations, and observed performance.

No particular algorithm is assumed to outperform all other algorithms. Performance conclusions will be based on experimental evidence.

---

# C. Problem Statement

## C.1 Background

An academic timetable determines when each teaching session takes place, which teacher conducts it, which class attends it, and which room hosts it.

A single teaching session can affect several resources simultaneously. For example, scheduling a mathematics lecture for Class A requires a suitable time slot, an available mathematics teacher, and an appropriate room.

The same time slot may be required by other classes and teachers. Assigning one session can therefore restrict the available choices for many other sessions.

This interdependence makes timetable scheduling a combinatorial optimization problem.

## C.2 Core Problems

### C.2.1 Teacher Conflicts

A teacher cannot conduct two sessions simultaneously.

The scheduler must also respect teacher availability and maximum workload restrictions.

### C.2.2 Class Conflicts

A class cannot attend two sessions at the same time.

The system must ensure that each required session is assigned without overlapping another session for the same class.

### C.2.3 Room Conflicts

A physical room can host at most one session in a time slot.

Even when two rooms are available, they may not be interchangeable because their capacities, equipment, or room types differ.

### C.2.4 Room Capacity and Suitability

A room must accommodate the number of students attending the session.

Laboratory sessions may require specialized rooms. A large lecture class must not be assigned to a room with insufficient capacity.

### C.2.5 Weekly Subject-Hour Requirements

Subjects require specified numbers of teaching periods each week.

The scheduler must generate the correct number of sessions for each applicable class-subject combination.

If a subject requires four weekly periods, the timetable must contain exactly four scheduled periods for that requirement unless the institution explicitly defines a different rule.

### C.2.6 Teacher Availability and Workload

Teachers may be unavailable during particular periods.

They may also have maximum daily or weekly teaching workloads. These restrictions must be respected.

Teacher availability can reduce the number of feasible assignments, particularly when several classes require the same teacher.

### C.2.7 Practical Scheduling Preferences

A timetable can be technically valid but still inconvenient.

Examples include:

- Long gaps between classes.
- Repeated sessions of the same subject on consecutive days.
- Excessive consecutive teaching periods.
- Teaching sessions scheduled at a teacher's least-preferred times.
- Laboratory sessions divided into separate periods when consecutive periods would be preferable.

The system must measure these preferences through soft-constraint penalties.

### C.2.8 Search Complexity

The number of possible schedules grows rapidly with the number of sessions and available time slots.

Exhaustively evaluating every possible assignment is generally impractical for larger datasets.

The application therefore requires intelligent variable selection, search-space reduction, and optimization strategies.

### C.2.9 Limited Comparability of Manual Scheduling

Manually generated timetables do not naturally provide standardized measurements of runtime, search effort, hard-constraint violations, or soft-constraint penalties.

The proposed application will provide a common evaluation framework so that different algorithms can be compared on the same datasets.

## C.3 Problem Definition

Given:

- A set of classes.
- A set of teachers.
- A set of subjects.
- A set of rooms.
- A set of available time slots.
- Required weekly teaching sessions.
- Teacher and room availability.
- Workload and capacity restrictions.
- Hard constraints and soft preferences.

The system must find an assignment of all required teaching sessions to valid time slots and resources such that:

1. Every required session is scheduled.
2. Every hard constraint is satisfied.
3. Soft-constraint penalties are minimized as far as reasonably possible.
4. The resulting timetable can be validated, reviewed, edited, and exported.

If no feasible solution exists under the supplied constraints, the system must report the failure rather than present an invalid timetable as a successful result.

---

# D. Goals and Objectives

## D.1 Primary Objectives

| ID | Objective | Expected Outcome |
|---|---|---|
| OBJ-001 | Automatically generate academic timetables. | Required teaching sessions are assigned to valid time slots and resources. |
| OBJ-002 | Model timetable scheduling as a CSP. | Variables, domains, and constraints are explicitly defined. |
| OBJ-003 | Implement Backtracking CSP. | The solver searches for assignments that satisfy hard constraints. |
| OBJ-004 | Implement MRV, Degree Heuristic, and Forward Checking. | The CSP solver incorporates intelligent variable selection and domain reduction. |
| OBJ-005 | Implement Min-Conflicts. | The application can optimize an initial assignment through local search. |
| OBJ-006 | Enforce hard constraints. | An independently validated timetable marked valid has zero hard-constraint violations. |
| OBJ-007 | Evaluate soft constraints. | Timetable quality is measured using a documented penalty model. |
| OBJ-008 | Provide an interactive Streamlit interface. | Users can configure, generate, inspect, edit, and export timetables. |
| OBJ-009 | Support different dataset sizes. | The system can be tested on small and larger datasets. |
| OBJ-010 | Compare algorithm performance. | Experiments produce comparable measurements across algorithms. |

## D.2 Secondary Objectives

| ID | Objective | Expected Outcome |
|---|---|---|
| OBJ-011 | Support multiple timetable views. | Users can inspect schedules by class, teacher, and room. |
| OBJ-012 | Support manual timetable editing. | Users can modify assignments and immediately revalidate them. |
| OBJ-013 | Support CSV and Excel export. | Users can obtain the generated schedule in reusable formats. |
| OBJ-014 | Provide informative error messages. | Users can identify invalid inputs and unsuccessful scheduling attempts. |
| OBJ-015 | Support reproducible experiments. | Algorithm configurations, random seeds where applicable, and results are recorded. |

## D.3 Bonus Objectives

| ID | Objective | Expected Outcome |
|---|---|---|
| OBJ-016 | Implement Simulated Annealing. | The application can explore alternative schedules through stochastic local search. |
| OBJ-017 | Implement Hybrid CSP + Simulated Annealing. | A CSP-generated solution can be improved through local search. |
| OBJ-018 | Provide experiment-level statistical summaries. | Repeated stochastic runs can be summarized using appropriate statistics. |
| OBJ-019 | Provide richer schedule diagnostics. | The application can identify recurring bottlenecks and explain common causes of infeasibility where possible. |

---

# E. Target Users and Stakeholders

## E.1 Academic Administrators

**Responsibilities:** Define academic scheduling policies, teaching requirements, and institutional restrictions.

**Needs:**
- Valid timetables.
- Compliance with room and workload policies.
- Clear scheduling status.
- Exportable schedules.

**Expected benefits:** Reduced manual scheduling effort and more consistent enforcement of institutional rules.

## E.2 Timetable Coordinators

**Responsibilities:** Prepare, review, adjust, and distribute academic timetables.

**Needs:**
- Dataset configuration.
- Algorithm selection.
- Timetable generation.
- Conflict identification.
- Manual editing.
- Multiple timetable views.
- Export functionality.

**Expected benefits:** Faster timetable preparation, fewer overlooked conflicts, and easier comparison of alternative schedules.

## E.3 Teachers

**Responsibilities:** Conduct assigned teaching sessions.

**Needs:**
- Accurate personal timetables.
- Respect for recorded availability.
- Visibility into teaching workload.
- Consideration of scheduling preferences.

**Expected benefits:** Better schedule visibility and fewer avoidable scheduling inconveniences.

## E.4 Students

**Responsibilities:** Attend assigned classes and practical sessions.

**Needs:**
- Clear class-wise timetables.
- No overlapping sessions for the same class.
- Correct subject-session allocation.
- Reasonable distribution of sessions.

**Expected benefits:** More understandable schedules and fewer conflicts between required sessions.

## E.5 Project Evaluators

**Responsibilities:** Assess the correctness, functionality, AI concepts, and experimental rigor of the academic project.

**Needs:**
- Clear CSP formulation.
- Demonstrable algorithms.
- Testable requirements.
- Independent validation.
- Measurable evaluation criteria.
- Documented experimental results.

**Expected benefits:** An auditable demonstration of Artificial Intelligence, search, constraint satisfaction, and optimization concepts.

## E.6 Project Team

**Responsibilities:** Design, implement, test, document, and demonstrate the system.

**Needs:**
- Clearly defined scope.
- Stable requirement identifiers.
- Testable acceptance criteria.
- Sample datasets.
- Algorithm comparison methodology.
- A phased implementation plan.

**Expected benefits:** Reduced ambiguity, better prioritization, and easier verification of project completion.

---

# F. User Personas and User Stories

The personas below represent proposed users for the academic prototype. They are not claims about actual institutional users.

## F.1 Persona: Academic Administrator

**Name:** Dr. Meera Sharma
**Role:** Academic Administrator
**Primary goal:** Produce valid institutional schedules.

**Pain points:**
- Multiple scheduling restrictions.
- Limited room availability.
- Conflicting teacher assignments.
- Difficulty identifying infeasible requirements.

### US-001: Configure Scheduling Data

**User story**

As an academic administrator, I want to configure classes, teachers, subjects, rooms, and teaching requirements, so that the scheduler uses accurate institutional data.

**Priority:** Must Have

**Acceptance criteria:**
1. The user can provide the required scheduling entities and their relevant attributes.
2. The system validates required fields before generation.
3. Invalid references are identified.
4. The system prevents timetable generation from proceeding with blocking validation errors.
5. The user receives actionable validation messages.

**Dependencies:** FR-001 to FR-005.

### US-002: Generate a Valid Timetable

As an academic administrator, I want the application to generate a timetable automatically, so that scheduling does not depend entirely on manual assignment.

**Priority:** Must Have

**Acceptance criteria:**
1. The user can select a supported algorithm.
2. The system attempts to schedule all required sessions.
3. The result is independently validated.
4. A timetable is marked valid only when all required sessions are scheduled and all hard constraints are satisfied.
5. Failure to find a valid schedule is reported clearly.

**Dependencies:** FR-006 to FR-015.

## F.2 Persona: Timetable Coordinator

**Name:** Rahul Verma
**Role:** Timetable Coordinator
**Primary goal:** Review and adjust schedules efficiently.

### US-003: Compare Algorithms

As a timetable coordinator, I want to compare different scheduling algorithms on the same dataset, so that I can evaluate their quality and efficiency.

**Priority:** Must Have

**Acceptance criteria:**
1. The user can run experiments using supported algorithms.
2. The experiment records runtime and hard-constraint violation counts.
3. The experiment records the soft-constraint penalty.
4. Search nodes or algorithm iterations are recorded when supported.
5. Results can be compared using consistent metric definitions.
6. Failed runs remain distinguishable from successful runs.

**Dependencies:** FR-006, FR-007, FR-018, FR-019, FR-020.

### US-004: Edit a Timetable

As a timetable coordinator, I want to change a scheduled session manually, so that I can accommodate a necessary adjustment.

**Priority:** Must Have

**Acceptance criteria:**
1. The user can select an existing session.
2. The user can request a different time slot or compatible room.
3. The system checks the proposed change against hard constraints.
4. An invalid edit is rejected or retained only as an explicitly invalid draft, depending on the confirmed editing policy.
5. The displayed validation results are refreshed after the edit.
6. The final exported schedule matches the selected saved schedule.

**Dependencies:** FR-021, FR-022, FR-023.

## F.3 Persona: Teacher

**Name:** Priya Singh
**Role:** Faculty Member
**Primary goal:** Access an accurate personal teaching schedule.

### US-005: View a Personal Timetable

As a teacher, I want to view my timetable, so that I can identify my assigned classes and teaching periods.

**Priority:** Must Have

**Acceptance criteria:**
1. The application provides a teacher-wise timetable view.
2. The view shows the correct teacher, class, subject, room, day, and period for each assignment.
3. A teacher does not appear in two simultaneous sessions in a timetable marked valid.
4. Filtering by teacher displays only relevant sessions.

**Dependencies:** FR-024, FR-025.

### US-006: Respect Teacher Availability

As a teacher, I want the scheduler to respect my recorded availability, so that I am not assigned to unavailable periods.

**Priority:** Must Have

**Acceptance criteria:**
1. Teacher availability can be represented in the input dataset.
2. The scheduler excludes unavailable slots from valid assignments.
3. The independent validator detects any assignment that violates availability.
4. The system identifies insufficient availability when it prevents successful scheduling and the relevant limitation can be diagnosed.

**Dependencies:** FR-003, FR-004, FR-013.

## F.4 Persona: Student

**Name:** Aarav Gupta
**Role:** Student
**Primary goal:** Access a clear class timetable.

### US-007: View a Class Timetable

As a student, I want to view my class timetable, so that I can identify when and where each subject takes place.

**Priority:** Must Have

**Acceptance criteria:**
1. The application provides a class-wise timetable view.
2. Each scheduled session displays its subject, teacher, room, day, and period.
3. A valid timetable contains no overlapping sessions for the same class.
4. The view reflects the same underlying schedule as the teacher-wise and room-wise views.

**Dependencies:** FR-024, FR-025.

## F.5 Persona: Project Evaluator

**Name:** Prof. Arjun Mehta
**Role:** Faculty Evaluator
**Primary goal:** Verify the correctness of the AI implementation.

### US-008: Verify Scheduling Constraints

As a project evaluator, I want to inspect hard-constraint validation results, so that I can determine whether a generated timetable is valid.

**Priority:** Must Have

**Acceptance criteria:**
1. The application displays the validation status.
2. It reports the total hard-constraint violation count.
3. Detected violations include the affected session or resource wherever possible.
4. The evaluator can distinguish invalid schedules from incomplete or failed scheduling attempts.
5. A valid status requires zero hard-constraint violations and complete fulfillment of required sessions.

**Dependencies:** FR-014, FR-015.

### US-009: Evaluate Algorithm Performance

As a project evaluator, I want to inspect algorithm performance metrics, so that I can compare the practical behavior of the implemented AI techniques.

**Priority:** Must Have

**Acceptance criteria:**
1. Experiments use documented datasets and configurations.
2. Runtime is recorded.
3. Solution validity and soft-constraint penalties are recorded.
4. Search effort is recorded where supported.
5. Results from stochastic algorithms include run-specific configuration and, where appropriate, repeated-run summaries.
6. The system does not claim that one algorithm is universally superior based on a single run.

**Dependencies:** FR-018 to FR-020.

---

# G. Functional Requirements

## G.1 Dataset Upload and Configuration

### FR-001: Dataset Upload

**Priority:** Must Have

**Description:** The application shall allow users to upload timetable input datasets in a documented supported format.

**Acceptance criteria:**
- The user can select a supported input file.
- The application confirms whether the file can be parsed.
- Unsupported formats and unreadable files produce an actionable error message.
- The application does not silently substitute missing input data.

**Dependencies:** None.

### FR-002: Dataset Selection and Sample Data

**Priority:** Must Have

**Description:** The application shall provide a way to select a bundled sample dataset and use it as an alternative to uploading data.

**Acceptance criteria:**
- At least one small sample dataset is available.
- The user can identify which dataset is currently active.
- Loading a sample dataset does not silently overwrite a previously edited schedule.
- The selected dataset is associated with the resulting experiment.

**Dependencies:** FR-001.

### FR-003: Entity Management

**Priority:** Must Have

**Description:** The application shall support the creation, review, and modification of the following entities and their relevant attributes:

- Teachers.
- Classes.
- Subjects.
- Rooms.
- Time slots.
- Teaching requirements.
- Teacher availability.
- Room availability and suitability.
- Workload restrictions.

**Acceptance criteria:**
- Each entity can be identified consistently.
- Required attributes can be reviewed.
- References between entities are validated.
- Invalid or duplicate identifiers are reported.
- Changes to scheduling inputs are reflected in subsequent generation attempts.

**Dependencies:** FR-001, FR-002.

### FR-004: Scheduling Requirement Configuration

**Priority:** Must Have

**Description:** The application shall allow users to configure weekly subject-hour requirements, room requirements, teacher assignments, and applicable availability restrictions.

**Acceptance criteria:**
- The user can specify required weekly teaching periods.
- The user can specify applicable room types and capacity requirements.
- The user can specify teacher availability and workload limits.
- The application validates whether configured values are meaningful.
- The configured requirements are used consistently by the solver and independent validator.

**Dependencies:** FR-003.

### FR-005: Dataset Validation

**Priority:** Must Have

**Description:** The application shall validate input data before timetable generation.

**Acceptance criteria:**
- Missing required fields are identified.
- Invalid entity references are identified.
- Duplicate identifiers are reported.
- Invalid availability and workload values are reported.
- Structurally invalid datasets cannot be submitted for generation.
- The validation report distinguishes blocking errors from warnings.

**Dependencies:** FR-001 to FR-004.

## G.2 Algorithm Selection and Generation

### FR-006: Algorithm Selection

**Priority:** Must Have

**Description:** The application shall provide a user interface for selecting the scheduling algorithm.

**Acceptance criteria:**
- All implemented algorithms are listed.
- Bonus algorithms are clearly identified if not enabled.
- The selected algorithm is visible before execution.
- The application does not report a disabled or unimplemented algorithm as executed.
- Algorithm-specific configuration options are displayed where applicable.

**Dependencies:** FR-005, FR-008 to FR-011.

### FR-007: Timetable Generation

**Priority:** Must Have

**Description:** The application shall generate a timetable by assigning required teaching sessions to valid combinations of time slots and resources.

**Acceptance criteria:**
- Generation starts only after blocking dataset errors have been resolved.
- The selected algorithm is used.
- All required sessions are accounted for in the result or explicitly identified as unscheduled.
- The output is passed to the independent validator.
- The application distinguishes valid, invalid, incomplete, and failed outcomes.
- The system does not label an incomplete or invalid result as a successful final timetable.

**Dependencies:** FR-005, FR-006, FR-012, FR-014.

### FR-008: Backtracking CSP Solver

**Priority:** Must Have

**Description:** The application shall implement a backtracking search algorithm that models scheduling as a CSP.

**Acceptance criteria:**
- The scheduling problem is represented using variables, domains, and constraints.
- The solver assigns values to scheduling variables.
- Assignments that violate hard constraints are rejected during search.
- The solver backtracks when an assignment prevents a feasible continuation.
- A complete assignment is independently validated before being marked valid.
- Search-limit termination is distinguishable from proof that no solution exists.

**Dependencies:** FR-004, FR-005, FR-012.

### FR-009: MRV and Degree Heuristic

**Priority:** Must Have

**Description:** The Backtracking CSP solver shall support Minimum Remaining Values and the Degree Heuristic for variable ordering.

**Acceptance criteria:**
- MRV selects a variable with the fewest remaining legal values.
- The Degree Heuristic is used to break relevant ties by considering the number of unassigned variables constrained by a candidate variable.
- The selected variable and ordering configuration are recorded in experiment metadata.
- The solver can be tested on a problem where MRV changes the next variable selected.
- The solver can be tested on a problem where the Degree Heuristic resolves an MRV tie.

**Dependencies:** FR-008.

### FR-010: Forward Checking

**Priority:** Must Have

**Description:** The Backtracking CSP solver shall use Forward Checking to remove inconsistent values from the domains of relevant unassigned variables.

**Acceptance criteria:**
- After a tentative assignment, affected domains are updated.
- Values inconsistent with the assignment are removed from the relevant domains.
- If an affected domain becomes empty, the solver recognizes the dead end and backtracks.
- The final timetable is independently validated.
- Tests demonstrate that Forward Checking detects at least one deliberately constructed domain failure.

**Dependencies:** FR-008, FR-009.

### FR-011: Min-Conflicts Local Search

**Priority:** Must Have

**Description:** The application shall implement Min-Conflicts as a local-search scheduling algorithm.

**Acceptance criteria:**
- The algorithm starts from a defined initial assignment or initialization procedure.
- It selects a variable involved in a conflict and attempts to reduce the number or cost of conflicts.
- The implementation records its iteration count.
- A configurable search limit is enforced.
- The final candidate is independently validated.
- The algorithm reports failure or an invalid candidate if it does not find a feasible solution within its search limit.

**Dependencies:** FR-004, FR-005, FR-012, FR-014.

**Product note:** The implementation must explicitly define how hard constraints are handled. A low-conflict result is not valid if any hard constraints remain violated.

## G.3 Bonus Algorithms

### FR-012: Simulated Annealing

**Priority:** Could Have

**Description:** The application shall support Simulated Annealing as an optional optimization algorithm.

**Acceptance criteria:**
- The user can select the algorithm when it is implemented and enabled.
- The algorithm uses a documented objective function and cooling configuration.
- The application records iterations and runtime.
- The resulting candidate is independently validated.
- A result that violates a hard constraint is not marked as valid.
- The experiment records the configuration needed to interpret the result.

**Dependencies:** FR-004, FR-005, FR-014.

### FR-013: Hybrid CSP + Simulated Annealing

**Priority:** Could Have

**Description:** The application shall support a hybrid approach that uses CSP search to establish a feasible schedule and Simulated Annealing to improve its soft-constraint quality.

**Acceptance criteria:**
- The hybrid algorithm has a documented CSP initialization stage.
- Simulated Annealing receives a feasible initial schedule, unless the hybrid's explicitly documented recovery procedure handles the absence of one.
- Optimization preserves hard-constraint validity.
- The initial and final soft-constraint scores are recorded.
- The result is independently validated.
- The hybrid result is distinguishable from results produced by the standalone algorithms.

**Dependencies:** FR-008, FR-012, FR-014, FR-015.

## G.4 Constraint Validation and Quality Evaluation

### FR-014: Independent Hard-Constraint Validator

**Priority:** Must Have

**Description:** The application shall provide a validator that checks timetable validity independently of the scheduling algorithm.

**Acceptance criteria:**
- The validator checks every configured hard constraint applicable to the schedule.
- It detects teacher, class, and room conflicts.
- It checks capacity, room suitability, teacher availability, workload limits, mandatory breaks, and laboratory continuity where applicable.
- It verifies required weekly session counts.
- It reports the total hard-constraint violation count.
- A timetable is marked valid only if all required sessions are scheduled and the hard-constraint violation count is zero.
- The validator can evaluate a timetable regardless of which algorithm produced it.

**Dependencies:** FR-003, FR-004.

### FR-015: Soft-Constraint Evaluation

**Priority:** Must Have

**Description:** The application shall evaluate timetable quality using a documented soft-constraint penalty model.

**Acceptance criteria:**
- Each enabled soft constraint has a defined penalty calculation.
- Individual penalty components are available for inspection.
- The application calculates an aggregate soft-constraint penalty.
- Lower penalties represent better scores under the same scoring configuration.
- Soft-constraint scoring does not change hard-constraint validity.
- Comparisons use the same weights and definitions unless differences are explicitly documented.

**Dependencies:** FR-004, FR-014.

### FR-016: Validation After Schedule Changes

**Priority:** Must Have

**Description:** The application shall revalidate a timetable whenever its assignments change.

**Acceptance criteria:**
- The application detects a change to the timetable.
- Validation is performed on the updated schedule before it is treated as the current valid version.
- Previous validation results are not presented as current after an edit.
- Hard-constraint violations introduced by an edit are reported.
- Soft-constraint penalties are recalculated after the change.

**Dependencies:** FR-014, FR-015, FR-021.

## G.5 Timetable Views

### FR-017: Class-Wise Timetable View

**Priority:** Must Have

**Description:** The application shall display a timetable for a selected class.

**Acceptance criteria:**
- The user can select a class.
- Sessions are displayed against their assigned days and periods.
- Each session identifies the subject, teacher, and room.
- Empty slots are represented consistently.
- The view reflects the underlying schedule.

**Dependencies:** FR-007.

### FR-018: Teacher-Wise Timetable View

**Priority:** Must Have

**Description:** The application shall display a timetable for a selected teacher.

**Acceptance criteria:**
- The user can select a teacher.
- Only sessions assigned to that teacher are displayed.
- Day and period information is accurate.
- The displayed sessions correspond to the underlying schedule.
- Conflicts are not hidden by filtering.

**Dependencies:** FR-007.

### FR-019: Room-Wise Timetable View

**Priority:** Must Have

**Description:** The application shall display the sessions assigned to a selected room.

**Acceptance criteria:**
- The user can select a room.
- The view shows all sessions assigned to the room.
- Each session identifies its class, subject, teacher, day, and period.
- Room conflicts are represented in validation results.
- The view is consistent with the class-wise and teacher-wise views.

**Dependencies:** FR-007.

## G.6 Manual Editing and Export

### FR-020: Manual Timetable Editing

**Priority:** Must Have

**Description:** The application shall allow authorized application users to modify timetable assignments manually.

**Acceptance criteria:**
- The user can select a session and propose a change.
- The application prevents accidental modification of unrelated sessions.
- The user can change supported assignment attributes.
- Proposed changes are checked against hard constraints.
- The application communicates whether the resulting schedule remains valid.
- The current schedule and any retained draft are clearly distinguished if invalid edits are permitted as drafts.

**Dependencies:** FR-014, FR-016, FR-017.

### FR-021: Revalidation After Manual Editing

**Priority:** Must Have

**Description:** The application shall run hard-constraint and soft-constraint evaluation after manual editing.

**Acceptance criteria:**
- Every accepted edit triggers revalidation.
- The latest hard-constraint count is displayed.
- The latest soft-constraint penalty is displayed.
- Newly introduced violations are identifiable.
- A previously valid schedule is not assumed to remain valid after a modification.

**Dependencies:** FR-014, FR-015, FR-020.

### FR-022: CSV and Excel Export

**Priority:** Must Have

**Description:** The application shall export timetable data in CSV and Excel formats.

**Acceptance criteria:**
- The user can export the selected timetable.
- The exported file contains the scheduled session information.
- CSV and Excel files represent the same underlying schedule.
- The export includes enough information to identify the class, subject, teacher, room, day, and period.
- Exported data matches the selected saved schedule.
- Export failures produce an understandable message.

**Dependencies:** FR-007, FR-020, FR-021.

## G.7 Experimentation and Reporting

### FR-023: Experiment Execution

**Priority:** Must Have

**Description:** The application shall allow users to run controlled experiments on selected datasets and algorithms.

**Acceptance criteria:**
- The user can select a dataset and an enabled algorithm.
- Relevant algorithm parameters can be configured.
- Runtime and final validation results are recorded.
- The experiment identifies the dataset and algorithm used.
- The experiment records the configuration required to interpret the result.
- A failed experiment is retained as a failed run rather than silently omitted.

**Dependencies:** FR-006 to FR-015.

### FR-024: Algorithm Comparison Dashboard

**Priority:** Must Have

**Description:** The application shall display comparable evaluation metrics for experiment runs.

**Acceptance criteria:**
- Results can be compared across supported algorithms.
- Runtime, hard-constraint violations, and soft-constraint penalties are displayed.
- Search nodes or iterations are included when supported.
- Incomplete and failed runs are distinguishable from valid solutions.
- Differences in dataset or configuration are visible.
- The dashboard does not rank invalid schedules as equivalent to valid schedules solely because of their soft-constraint scores.

**Dependencies:** FR-023.

### FR-025: Experiment Reproducibility

**Priority:** Should Have

**Description:** The application shall record the information needed to reproduce and interpret algorithm experiments.

**Acceptance criteria:**
- Each experiment has an identifiable run record.
- Dataset identity or version is recorded.
- Algorithm name and relevant configuration are recorded.
- Random seeds are recorded for stochastic algorithms when controllable.
- Runtime and termination status are recorded.
- Repeated runs can be distinguished.

**Dependencies:** FR-023.

## G.8 Error Handling and User Feedback

### FR-026: Input and Execution Error Reporting

**Priority:** Must Have

**Description:** The application shall provide actionable feedback when inputs are invalid or scheduling fails.

**Acceptance criteria:**
- Errors identify the relevant dataset, entity, or operation where possible.
- Messages explain what needs to be corrected.
- Internal technical errors are not presented as successful results.
- A failed generation attempt does not overwrite a valid schedule without an explicit user action.
- The application distinguishes invalid input, infeasibility, search-limit termination, timeout, and internal failure where possible.

**Dependencies:** FR-001 to FR-007.

### FR-027: Generation Progress and Status

**Priority:** Should Have

**Description:** The application shall communicate scheduling progress and completion status.

**Acceptance criteria:**
- The application indicates when generation starts.
- The application indicates when generation completes or terminates.
- The displayed status distinguishes success, failure, timeout, and search-limit termination.
- Progress indicators do not imply a guaranteed completion time.
- Progress information is shown only when supported by the algorithm's execution.

**Dependencies:** FR-007, FR-023.

### FR-028: Dataset and Schedule Change Management

**Priority:** Should Have

**Description:** The application shall make changes to datasets and schedules understandable and controlled.

**Acceptance criteria:**
- The active dataset and schedule are identifiable.
- Dataset changes are not silently confused with changes to an existing schedule.
- The application indicates when a schedule was generated using different input data from the currently active dataset.
- Unsaved edits are not silently discarded when a user initiates a conflicting action.

**Dependencies:** FR-002, FR-003, FR-020.

---

# H. Non-Functional Requirements

The requirements in this section describe the expected quality of the application.

Any numerical target introduced here is a proposed target for experimental verification, not an established performance guarantee.

## H.1 Performance

### NFR-001: Interactive Performance

**Priority:** Must Have

The application should remain usable while loading datasets, validating inputs, reviewing results, and performing ordinary interface operations.

**Acceptance criteria:**
- Dataset validation completes without requiring timetable generation.
- The application provides a clear indication when a long-running algorithm is executing.
- Runtime is measured for scheduling experiments.
- The application does not claim a universal runtime guarantee across arbitrary datasets.

**Proposed measurement:** Record interface responsiveness and algorithm runtime for the defined small and large datasets.

### NFR-002: Search Resource Limits

**Priority:** Must Have

Search algorithms shall support configurable limits where applicable.

**Acceptance criteria:**
- The user or application configuration can define a search limit.
- Reaching a limit produces a distinct termination status.
- A limit-triggered termination is not automatically interpreted as proof of infeasibility.
- Runtime and search effort are recorded.

## H.2 Reliability

### NFR-003: Consistent Validation

**Priority:** Must Have

The same timetable and constraint configuration must produce consistent hard-constraint validation results.

**Acceptance criteria:**
- Repeated validation of an unchanged schedule produces the same result.
- The validator uses the same authoritative definitions of hard constraints throughout the application.
- Validation failures do not silently result in a valid status.

### NFR-004: Safe Failure Handling

**Priority:** Must Have

The application shall handle algorithm failures without treating incomplete or invalid results as successful schedules.

**Acceptance criteria:**
- Failure status is explicit.
- Existing valid results are not silently replaced by failed results.
- Partial candidates are clearly labeled.
- A failed run can be distinguished from a run that completed without finding a solution.

## H.3 Usability

### NFR-005: Understandable Interface

**Priority:** Must Have

The application shall provide a user interface understandable to users who are familiar with academic timetables but not necessarily with AI algorithms.

**Acceptance criteria:**
- Input requirements are documented.
- Algorithm names are accompanied by concise descriptions.
- Validation messages identify actionable problems.
- Timetable views are clearly labeled.
- Users can distinguish hard-constraint validity from soft-constraint quality.

### NFR-006: Consistent Navigation

**Priority:** Should Have

The application should provide a consistent flow from dataset selection through generation, validation, review, editing, and export.

**Acceptance criteria:**
- Related actions are grouped logically.
- The active dataset and selected schedule are identifiable.
- Users can return to earlier workflow stages without losing data unexpectedly.

## H.4 Maintainability

### NFR-007: Separation of Responsibilities

**Priority:** Must Have

The application should separate scheduling algorithms, constraint validation, soft-constraint evaluation, dataset handling, and user interface behavior.

**Acceptance criteria:**
- Each algorithm can be tested independently of the Streamlit interface.
- The validator can evaluate schedules produced by different algorithms.
- Soft-constraint weights can be changed without redefining unrelated constraints.
- Changes to one supported algorithm do not require rewriting all timetable views.

## H.5 Portability

### NFR-008: Reproducible Application Setup

**Priority:** Must Have

The application shall be runnable in a documented Python environment on a supported development system.

**Acceptance criteria:**
- Required dependencies are documented.
- Setup instructions are provided.
- The application can be started using the documented procedure.
- Sample datasets are included or referenced through documented paths.

## H.6 Data Integrity

### NFR-009: Schedule Consistency

**Priority:** Must Have

All timetable views, validation reports, and exports shall refer to the same selected schedule version.

**Acceptance criteria:**
- Class-wise, teacher-wise, and room-wise views agree on the details of every session.
- Exported data matches the selected saved schedule.
- Manual edits invalidate outdated validation results.
- The application identifies the schedule version or state being evaluated.

### NFR-010: Requirement Completeness

**Priority:** Must Have

The system shall track required sessions independently from their assignments.

**Acceptance criteria:**
- Every required session is represented in the scheduling problem.
- Unscheduled sessions remain identifiable.
- Duplicate or missing session requirements are detected where the dataset rules permit detection.
- A schedule cannot be marked complete if required sessions are missing.

## H.7 Accessibility

### NFR-011: Readability and Interaction

**Priority:** Should Have

The interface should use readable labels, clear status indicators, and accessible controls.

**Acceptance criteria:**
- Important information is not communicated through color alone.
- Tables and controls have understandable labels.
- Error and success messages are readable.
- The interface remains usable at common desktop browser sizes.

Full accessibility conformance is outside the minimum prototype unless separately required.

## H.8 Security

### NFR-012: Safe File Handling

**Priority:** Must Have

The application shall validate uploaded files before using their contents.

**Acceptance criteria:**
- Unsupported file formats are rejected.
- Parsing failures are handled safely.
- Uploaded data is not executed as code.
- File size restrictions may be applied as configurable application safeguards.
- The application does not expose sensitive data in unnecessary error messages.

### NFR-013: Limited Data Retention

**Priority:** Should Have

The prototype should avoid retaining uploaded datasets or generated schedules beyond the intended application session unless persistence is explicitly configured.

**Acceptance criteria:**
- Data-retention behavior is documented.
- Temporary data handling is consistent with the chosen deployment environment.
- Users are informed if data is persisted.

Institutional authentication and role-based access control are outside the initial scope.

## H.9 Error Handling

### NFR-014: Actionable Errors

**Priority:** Must Have

Errors shall explain the failure in terms understandable to the user.

**Acceptance criteria:**
- Invalid input messages identify the problem.
- Scheduling failures identify the termination status.
- Export failures explain that the export did not complete.
- The application avoids presenting misleading success messages.

## H.10 Reproducibility

### NFR-015: Experiment Traceability

**Priority:** Must Have

The application shall preserve enough experiment metadata to interpret recorded results.

**Acceptance criteria:**
- Dataset identity, algorithm, configuration, runtime, and outcome are recorded.
- Stochastic algorithms record random seeds when controllable.
- Metric definitions are documented.
- Comparisons can distinguish differences in configuration.

### NFR-016: Fair Algorithm Comparison

**Priority:** Must Have

The evaluation process shall avoid presenting unfair or misleading algorithm comparisons.

**Acceptance criteria:**
- Algorithms are evaluated against the same scheduling requirements.
- Hard-constraint validity is evaluated using the same independent validator.
- Soft-constraint penalties use consistent weights.
- Search limits and termination conditions are documented.
- Stochastic algorithms can be evaluated over multiple runs when feasible.

---

# I. Business Rules and Scheduling Constraints

## I.1 Scheduling Model

The scheduler operates on a set of required teaching sessions.

Each session must be assigned a valid time slot and the appropriate resources.

A session may require:
- A class.
- A subject.
- A teacher.
- A room.
- A duration.
- A specific room type.
- A particular availability window.

For sessions that occur multiple times each week, the scheduling model must represent the required occurrences individually or otherwise guarantee that their total assigned duration satisfies the requirement.

The exact representation of a session and its duration is a technical design decision for the TRD.

## I.2 Hard Constraints

Hard constraints determine whether a timetable is valid.

A hard-constraint violation cannot be offset by a good soft-constraint score.

### HC-001: Teacher Conflict Prevention

A teacher cannot conduct two sessions during the same time slot.

**Validation rule:** No overlapping assignments may exist for the same teacher.

### HC-002: Class Conflict Prevention

A class cannot attend two sessions simultaneously.

**Validation rule:** No overlapping assignments may exist for the same class.

### HC-003: Room Conflict Prevention

A room cannot host two sessions simultaneously.

**Validation rule:** No overlapping assignments may exist for the same room.

### HC-004: Room Capacity

The room capacity must be sufficient for the number of students expected in the session.

**Validation rule:** Assigned room capacity must be greater than or equal to the required session capacity.

### HC-005: Room Type Compatibility

The assigned room must satisfy the session's room-type requirements.

**Example:** A laboratory session requiring a computer laboratory cannot be assigned to an ordinary lecture room.

### HC-006: Teacher Availability

A teacher must be available during every assigned teaching period.

**Validation rule:** No session may overlap a teacher's configured unavailable periods.

### HC-007: Weekly Subject-Hour Requirements

Every required class-subject combination must receive its specified number of weekly teaching periods.

**Validation rule:** The scheduled session count or total scheduled duration must equal the configured requirement, according to the selected duration model.

### HC-008: Teacher Maximum Workload

Teacher workload must not exceed the configured maximum.

**Validation rule:** The sum of applicable teaching periods or hours must remain within the configured daily and weekly limits.

### HC-009: Mandatory Lunch Breaks

Mandatory lunch breaks must be respected for every applicable class and teacher.

**Validation rule:** No prohibited teaching assignment may overlap a mandatory break.

**Assumption:** Lunch-break rules may differ between classes and teachers. Their scope must be explicitly configured.

### HC-010: Consecutive Laboratory Periods

Laboratory sessions that require consecutive periods must be scheduled into a sufficiently long, uninterrupted block.

**Validation rule:** The assigned periods must be adjacent according to the defined timetable ordering and must satisfy all relevant resource and availability restrictions.

**Assumption:** This constraint applies only to sessions explicitly marked as requiring consecutive periods.

## I.3 Soft Constraints

Soft constraints express preferences that improve timetable quality.

Violating a soft constraint may be acceptable when no better feasible alternative exists.

### SC-001: Minimize Unnecessary Class Gaps

Reduce avoidable gaps between teaching sessions for the same class.

A possible penalty is based on the number of empty periods between the first and last scheduled periods of a class on a given day.

### SC-002: Distribute Repeated Subjects Across Days

Prefer spreading repeated sessions of the same subject across different days.

This can reduce excessive concentration of one subject within a short period.

### SC-003: Limit Consecutive Teaching Periods

Avoid excessive consecutive teaching periods for teachers.

A configurable preference may penalize assignments exceeding a desired consecutive-period threshold.

### SC-004: Respect Teacher Time Preferences

Prefer teacher-approved time slots where possible.

The system must distinguish an unavailable period, which is a hard restriction, from a merely undesirable period, which is a soft preference.

### SC-005: Prefer Consecutive Laboratory Periods

When laboratory continuity is preferred but not mandatory, penalize fragmented laboratory sessions.

If the institution marks continuity as mandatory, HC-010 applies instead.

## I.4 Constraint Classification Rules

**A single rule must not be simultaneously treated as a hard constraint and a soft constraint for the same condition.**

For example:

- A teacher's declared unavailable period is a hard constraint.
- A teacher's preference to avoid early morning periods is a soft constraint.
- A laboratory that legally or academically requires a continuous double period is subject to HC-010.
- A laboratory that merely benefits from consecutive periods may use SC-005.

A rule may be configurable, but its active classification must be unambiguous for a particular experiment.

## I.5 Configurable Constraint Settings

The following should be configurable where applicable:

| Setting | Proposed Configuration |
|---|---|
| Teacher availability | Hard restriction |
| Room availability | Hard restriction |
| Room capacity | Hard restriction |
| Room type | Hard restriction |
| Maximum teacher workload | Hard restriction |
| Weekly subject requirements | Hard restriction |
| Mandatory lunch breaks | Hard restriction |
| Laboratory continuity | Hard or soft, according to session requirements |
| Teacher time preferences | Soft preference |
| Class gap minimization | Soft preference |
| Subject distribution | Soft preference |
| Maximum preferred consecutive teaching periods | Soft preference |

Changes to constraint classification must be reflected in validation, optimization, and experiment metadata.

## I.6 Soft-Constraint Penalty Model

The application shall calculate an aggregate penalty using enabled soft constraints.

A proposed general model is:

\[
P_{\text{soft}} = \sum_{i=1}^{m} w_i P_i
\]

Where:

- \(P_{\text{soft}}\) is the total soft-constraint penalty.
- \(m\) is the number of enabled soft constraints.
- \(w_i\) is the configured weight for soft constraint \(i\).
- \(P_i\) is the measured penalty for that constraint.

Lower values indicate better soft-constraint quality under the same configuration.

The penalty definitions and weights must be documented before experiments are compared.

**Important:** Soft-constraint penalties must not be used as a substitute for hard-constraint validation.

## I.7 Feasibility and Completeness

A timetable is considered **valid and complete** only when:

1. All required sessions have been assigned.
2. All hard constraints are satisfied.
3. No required session is duplicated or omitted.
4. The independent validator reports zero hard-constraint violations.

A timetable may be **invalid but useful for diagnosis** if it contains a partial assignment or a candidate solution with conflicts.

Such a timetable must not be presented as a valid final schedule.

---

# J. User Interface Requirements

## J.1 Interface Overview

The application will use Streamlit to provide an interactive dashboard.

The interface should guide the user through a sequence:

**Dataset → Validation → Algorithm Configuration → Generation → Evaluation → Review/Edit → Export**

The exact layout may change during implementation, but the workflow must remain understandable.

## J.2 Dataset Selection and Upload

The dataset interface should include:

- Sample dataset selection.
- File upload.
- Active dataset identification.
- Dataset summary.
- Entity counts.
- Input validation results.
- Missing-field and invalid-reference messages.

The user should be able to determine whether the selected dataset is ready for scheduling.

## J.3 Input Validation Messages

Validation results should distinguish:

- Blocking errors.
- Non-blocking warnings.
- Informational messages.

Examples:

| Situation | Expected Message |
|---|---|
| Missing teacher ID | Required teacher identifier is missing. |
| Unknown room reference | The specified room does not exist in the selected dataset. |
| Invalid workload | The configured workload limit is invalid. |
| Insufficient available periods | The configured availability may be insufficient to satisfy the required sessions. |
| Valid input | Dataset validation completed without blocking errors. |

The application should not claim that a dataset is feasible merely because its structure is valid.

## J.4 Algorithm Selection

The algorithm-selection interface should provide:

- Algorithm name.
- Short explanation.
- Implementation status.
- Relevant configuration settings.
- Search limits.
- Random seed controls where applicable.
- Run action.

Bonus algorithms should be marked as optional and should not appear executable before implementation.

## J.5 Generation Controls

The generation interface should provide:

- Generate timetable action.
- Current algorithm and dataset summary.
- Progress or running status.
- Completion status.
- Runtime information.
- Search nodes or iteration count where supported.
- Clear failure messages.

A user should be able to distinguish between a solver that completed successfully and one that stopped because of a configured limit.

## J.6 Timetable Tables and Filters

The timetable display should provide:

- Class-wise view.
- Teacher-wise view.
- Room-wise view.
- Day and period information.
- Subject, teacher, class, and room details.
- Search or filtering controls.
- A consistent representation of unassigned periods.

All views must derive from the same underlying schedule.

## J.7 Constraint-Validation Results

The validation interface should show:

- Overall validity status.
- Number of hard-constraint violations.
- Violation categories.
- Affected sessions or resources where possible.
- Missing required sessions.
- Soft-constraint penalty.
- Individual soft-constraint penalty components.

The interface must distinguish hard-constraint validity from schedule quality.

## J.8 Algorithm Comparison Dashboard

The dashboard should allow the user to compare experiment runs.

Suggested visualizations include:

- Runtime by algorithm.
- Soft-constraint penalty by algorithm.
- Hard-constraint violations by algorithm.
- Search nodes or iterations where comparable.
- Valid-solution success rate.
- Results across small and large datasets.

Failed runs must remain visible or explicitly represented in the experiment results.

## J.9 Manual Editing Interface

The editing interface should allow the user to:

- Select a session.
- Propose a new time slot.
- Change a room when supported.
- Review compatibility and availability.
- Validate the resulting schedule.
- Save or discard the change.

The interface must clearly communicate whether the current schedule is valid.

## J.10 Export Interface

The export interface should provide:

- CSV export.
- Excel export.
- Selection of the schedule to export.
- Export status.
- Failure feedback.

The export must correspond to the selected saved schedule, not an outdated view or an unsaved state that the user did not intend to export.

---

# K. Algorithm Requirements

## K.1 Backtracking CSP with MRV, Degree Heuristic, and Forward Checking

### Purpose

This is the primary constraint-solving algorithm.

Its purpose is to find a complete assignment satisfying all hard constraints while reducing unnecessary search.

### Product Behavior

The algorithm will:

1. Represent scheduling decisions as variables.
2. Define the legal values available to each variable.
3. Apply hard constraints to determine whether assignments are legal.
4. Select variables using MRV and the Degree Heuristic.
5. Use Forward Checking to eliminate inconsistent future assignments.
6. Backtrack when a partial assignment cannot lead to a valid solution.
7. Return a complete candidate or a documented failure status.

### Expected Output

- A candidate timetable.
- Validation status.
- Search-node count.
- Runtime.
- Termination status.
- Relevant algorithm configuration.

### Strengths

- Systematic search.
- Clear relationship between the CSP formulation and the scheduling rules.
- Ability to prove that no solution exists if the search is exhaustive and the model is correct.
- Useful baseline for demonstrating CSP concepts.

### Limitations

- Search can become expensive as the problem grows.
- Poorly constrained or highly interconnected problems may require extensive search.
- A search limit can prevent the algorithm from determining whether a solution exists.

### Comparison

Results should be compared using runtime, search nodes, solution validity, and soft-constraint penalties.

When the search is exhaustive and correctly implemented, failure to find a solution can establish infeasibility within the modeled problem. Failure caused by a timeout or search limit cannot.

## K.2 Min-Conflicts

### Purpose

Min-Conflicts will demonstrate local-search optimization for timetable scheduling.

### Product Behavior

The algorithm will:

1. Construct an initial assignment.
2. Identify a variable involved in a conflict.
3. Evaluate alternative assignments.
4. Select an alternative that reduces conflicts according to the configured selection strategy.
5. Continue until a valid assignment is found or a termination limit is reached.

### Expected Output

- Candidate timetable.
- Hard-constraint validation status.
- Iteration count.
- Runtime.
- Termination status.
- Soft-constraint score when available.

### Strengths

- Can be effective for large constraint problems.
- Focuses on repairing conflicts rather than systematically exploring every assignment.
- Provides a useful comparison with backtracking search.

### Limitations

- May become trapped in local optima or cycles.
- Performance depends on initialization and variable selection.
- May fail to find a valid schedule within the configured limit even when a valid schedule exists.

### Comparison

Compare valid-solution success rate, runtime, iterations, and soft-constraint penalty.

The project must document whether hard constraints are enforced through legal move restrictions or another explicitly defined strategy.

## K.3 Simulated Annealing

### Purpose

Simulated Annealing is a bonus algorithm intended to explore alternative schedules and improve the objective value.

### Product Behavior

The algorithm will:

1. Start from an initial candidate schedule.
2. Generate a neighboring candidate.
3. Evaluate the change in objective value.
4. Accept or reject the candidate according to the configured acceptance rule.
5. Gradually reduce its willingness to accept worse candidates.
6. Stop when the termination condition is reached.

### Expected Output

- Candidate timetable.
- Runtime.
- Iteration count.
- Hard-constraint validation status.
- Initial and final objective values where applicable.
- Termination status.

### Strengths

- Can explore solutions beyond immediate local improvements.
- Provides an additional optimization technique for comparison.
- Offers configurable exploration behavior.

### Limitations

- Results depend on initialization, neighborhood design, cooling configuration, and termination conditions.
- There is no general guarantee of finding the global optimum within a finite practical runtime.
- Poor objective design can encourage invalid schedules.

### Hard-Constraint Policy

The implementation must either preserve hard-constraint feasibility throughout optimization or provide a documented feasibility-restoration procedure.

A low objective value cannot override hard-constraint violations.

## K.4 Hybrid CSP + Simulated Annealing

### Purpose

The hybrid algorithm combines systematic constraint solving with stochastic optimization.

The intended goal is to establish a feasible timetable using CSP and then improve its soft-constraint quality using Simulated Annealing.

### Product Behavior

The algorithm will:

1. Attempt to construct a feasible timetable using the CSP solver.
2. Stop with an appropriate failure status if no feasible starting timetable is obtained within the applicable limits.
3. Pass the feasible timetable to the optimization stage.
4. Explore alternative schedules while preserving feasibility.
5. Compare the initial and final soft-constraint penalties.
6. Independently validate the final result.

### Expected Output

- Initial CSP timetable.
- Final optimized timetable.
- Initial and final soft-constraint penalties.
- Runtime for the overall run.
- Search and iteration statistics where available.
- Final validation status.

### Strengths

- Uses CSP to establish feasibility.
- Uses local search to improve timetable quality.
- Provides a useful experiment for evaluating the value of combining algorithms.

### Limitations

- May require more runtime than either stage alone.
- Depends on the CSP stage finding a feasible initial timetable.
- Improvement is not guaranteed.
- The two stages must use compatible constraint definitions.

### Comparison

The hybrid algorithm should be compared with standalone CSP and Simulated Annealing using identical datasets, consistent soft-constraint weights, and documented computational limits.

Its value should be determined experimentally rather than assumed.

## K.5 Common Algorithm Output Contract

Every algorithm must produce a result that the application can interpret consistently.

The result should identify:

- Algorithm name.
- Dataset identity.
- Candidate schedule, if one exists.
- Assigned sessions.
- Unassigned sessions, if any.
- Termination status.
- Runtime.
- Search nodes or iterations where supported.
- Algorithm configuration.
- Independent validation results.
- Soft-constraint score where meaningful.

The application must not assume that different algorithms produce valid schedules merely because they return a candidate.

---

# L. Evaluation Metrics

## L.1 Hard-Constraint Violation Count

**Definition:** The total number of hard-constraint violations detected by the independent validator.

A violation is a detected instance of a rule being broken. The counting policy must define whether a single conflict involving two sessions is counted as one conflict or multiple violations.

**Interpretation:**
- `0`: No hard-constraint violations detected.
- Greater than `0`: The timetable is invalid.

**Evaluation rule:** Only complete schedules with zero hard-constraint violations can be marked valid.

## L.2 Soft-Constraint Penalty Score

**Definition:** The weighted sum of enabled soft-constraint penalties.

\[
P_{\text{soft}} = \sum_{i=1}^{m} w_iP_i
\]

**Interpretation:**
- Lower is better.
- Scores are comparable only when their penalty definitions, weights, and relevant dataset requirements are consistent.

A score of zero means no penalty was incurred under the configured soft constraints. It does not automatically mean the timetable is globally optimal.

## L.3 Timetable Generation Success Rate

**Definition:** The proportion of completed experiment attempts that produce a valid, complete timetable.

\[
\text{Success Rate} =
\frac{\text{Valid Complete Solutions}}
{\text{Total Experiment Attempts}}
\times 100
\]

**Interpretation:** A higher rate indicates that an algorithm more frequently produces valid solutions under the tested conditions and limits.

The dataset and experiment configuration must accompany this metric. An infeasible dataset should not be treated as a valid-solution opportunity.

## L.4 Runtime

**Definition:** Elapsed time between the start of algorithm execution and its termination.

**Interpretation:**
- Lower runtime generally indicates faster execution under comparable conditions.
- Runtime depends on the dataset, machine, algorithm settings, and implementation.
- Runtime should not be compared without documenting relevant experimental conditions.

Where appropriate, separate input-validation time, algorithm runtime, and final-validation time.

## L.5 Search Nodes

**Definition:** The number of search states or nodes explored by a search algorithm.

**Interpretation:**
- Fewer nodes may indicate more effective pruning or variable ordering.
- Node counts are not directly comparable across algorithms unless the definition is standardized.
- Min-Conflicts and Simulated Annealing may use iterations rather than CSP search nodes.

The application must define the counting policy for each algorithm.

## L.6 Iteration Count

**Definition:** The number of iterations performed by a local-search algorithm.

**Interpretation:** Fewer iterations may indicate faster convergence, but iteration counts alone do not establish better performance because each iteration may have a different computational cost.

## L.7 Constraint-Validation Status

**Definition:** The independent validator's classification of the candidate schedule.

Proposed statuses:

- **Valid:** All required sessions are scheduled and no hard-constraint violations are detected.
- **Invalid:** A candidate exists but one or more hard constraints are violated.
- **Incomplete:** One or more required sessions remain unassigned.
- **No Candidate:** The algorithm did not produce a schedule that can be evaluated as a candidate.
- **Not Evaluated:** Validation has not yet been completed.

A separate algorithm termination status should identify success, exhaustive search completion, search-limit termination, timeout, or internal failure where applicable.

## L.8 Algorithm Performance Comparison

The application should compare algorithms across:

- Small and large datasets.
- Runtime.
- Hard-constraint violations.
- Valid-solution success rate.
- Soft-constraint penalty.
- Search nodes or iterations.
- Termination status.

For stochastic algorithms, repeated runs should be conducted when feasible.

Useful summary statistics include:
- Mean runtime.
- Median runtime.
- Minimum and maximum soft-constraint penalties among valid runs.
- Mean or median penalty across valid runs.
- Valid-solution success rate.

Invalid runs must be reported separately rather than hidden within aggregate soft-constraint scores.

No algorithm is assumed to be best across every dataset and metric.

---

# M. Dataset Requirements

## M.1 Dataset Design Principles

The application must support datasets containing the information needed to define and validate scheduling problems.

A dataset should represent:

- Classes.
- Teachers.
- Subjects.
- Rooms.
- Time slots.
- Teaching requirements.
- Teacher availability.
- Room availability.
- Capacity and room-type restrictions.
- Workload limits.
- Mandatory breaks.
- Laboratory duration requirements.
- Optional soft-constraint preferences.

The exact input-file schema will be specified in the TRD.

## M.2 Small Dataset

The initial small dataset is proposed to contain approximately:

| Entity or Parameter | Proposed Size |
|---|---:|
| Classes | 3 |
| Teachers | 6 |
| Rooms | 4 |
| Teaching days | 5 |
| Periods per day | 6 |
| Weekly periods per class | 30 available class-period positions before breaks |

The maximum of 30 available class-period positions is only a theoretical timetable capacity before accounting for mandatory breaks, subject requirements, teacher availability, room availability, and other restrictions.

The actual number of required teaching sessions must be derived from the dataset.

### Purpose

The small dataset will be used to:

- Verify CSP correctness.
- Demonstrate MRV and Degree Heuristic behavior.
- Test Forward Checking.
- Verify conflict detection.
- Validate weekly subject-hour fulfillment.
- Test manual editing.
- Establish an initial algorithm comparison baseline.

At least one small feasible dataset and one deliberately infeasible test case should be prepared.

## M.3 Large Dataset

The initial large dataset is proposed to contain at least:

| Entity or Parameter | Proposed Minimum |
|---|---:|
| Classes | 8 |
| Teachers | 15 |
| Rooms | 8 |
| Teaching days | 5 |
| Periods per day | 7 |
| Weekly periods per class | 35 available class-period positions before breaks |

The total theoretical class-period capacity is 280 positions across eight classes before accounting for restrictions.

This figure does not represent the number of sessions that can necessarily be scheduled because teacher availability, room suitability, workload limits, subject requirements, and other constraints may substantially reduce feasibility.

### Purpose

The large dataset will be used to:

- Evaluate algorithm behavior as problem size increases.
- Measure runtime and search effort.
- Compare solution success rates.
- Evaluate the effects of heuristics and local search.
- Identify performance limitations.

## M.4 Dataset Feasibility

Dataset size alone does not determine whether a timetable is feasible.

Feasibility depends on factors including:

- Total required sessions.
- Available periods for each class.
- Teacher availability.
- Teacher workload limits.
- Room availability.
- Room capacity.
- Specialized room requirements.
- Mandatory breaks.
- Consecutive laboratory requirements.
- Competition for shared resources.

A dataset can be structurally valid but infeasible.

The application should distinguish these conditions:

1. **Structurally invalid:** Input data cannot be interpreted reliably.
2. **Structurally valid but potentially infeasible:** Input data is valid, but no solution may exist.
3. **Feasible:** At least one complete assignment satisfies all hard constraints.
4. **Unknown feasibility:** The search terminated without establishing whether a valid solution exists.

## M.5 Dataset Quality Requirements

Each sample dataset should include:

- A unique dataset identifier.
- A dataset description.
- Entity counts.
- Scheduling assumptions.
- Constraint configuration.
- Expected feasibility status where known.
- Expected validation outcomes for relevant test cases.

The team must not label a dataset as infeasible merely because an algorithm fails to find a solution within a search limit.

## M.6 Dataset Coverage

The project should include test datasets representing:

- A small feasible problem.
- A larger feasible problem.
- A problem with a teacher conflict in a supplied candidate.
- A problem with insufficient room capacity.
- A problem with incompatible room types.
- A problem with insufficient teacher availability.
- A problem with conflicting workload and session requirements.
- A problem requiring consecutive laboratory periods.
- A problem containing an invalid input reference.

These datasets will help evaluate correctness rather than relying only on successful demonstrations.

---

# N. User Workflows

## N.1 Workflow 1: Loading a Dataset

1. The user opens the application.
2. The user selects a bundled sample dataset or uploads a supported file.
3. The application parses the dataset.
4. The application displays the dataset name and entity summary.
5. The user reviews the loaded data.
6. The application makes the dataset available for validation.

**Expected outcome:** The selected dataset is loaded and identifiable.

## N.2 Workflow 2: Validating Input Data

1. The user initiates dataset validation.
2. The application checks required fields.
3. The application checks entity identifiers and references.
4. The application checks scheduling parameters.
5. The application reports errors and warnings.
6. The user corrects blocking errors.
7. The user reruns validation.

**Expected outcome:** The dataset is structurally valid and ready for scheduling attempts.

Structural validation does not guarantee feasibility.

## N.3 Workflow 3: Selecting an Algorithm

1. The user opens the algorithm-selection interface.
2. The application displays implemented algorithms.
3. The user selects an algorithm.
4. The application displays the relevant configuration options.
5. The user sets search limits or random seeds where applicable.
6. The application confirms the selected dataset and configuration.

**Expected outcome:** The scheduling run has a defined algorithm and configuration.

## N.4 Workflow 4: Generating a Timetable

1. The user selects Generate Timetable.
2. The application verifies that the dataset has no blocking validation errors.
3. The selected algorithm begins execution.
4. The application reports progress or status where supported.
5. The algorithm returns a candidate schedule or a termination status.
6. The independent validator evaluates any candidate.
7. The soft-constraint evaluator calculates the candidate's quality.
8. The application displays the result.

**Expected outcome:** A validated timetable is displayed, or a clear failure status is provided.

## N.5 Workflow 5: Reviewing Constraints

1. The user opens the validation results.
2. The application displays the hard-constraint violation count.
3. The user inspects individual violations where available.
4. The user reviews missing or unassigned sessions.
5. The user reviews the soft-constraint penalty and its components.
6. The user decides whether the schedule is acceptable or requires another attempt.

**Expected outcome:** The user understands whether the timetable is valid and how well it satisfies scheduling preferences.

## N.6 Workflow 6: Comparing Algorithms

1. The user selects a dataset.
2. The user chooses one or more implemented algorithms.
3. The user configures relevant search parameters.
4. The application executes the selected experiments.
5. The application records runtime, validity, soft penalties, and search effort where supported.
6. The user reviews the comparison dashboard.
7. The user identifies the best result according to the selected evaluation priorities.

**Expected outcome:** Comparable experiment results are available.

The selected best result must be valid if the objective is to produce a final timetable.

## N.7 Workflow 7: Manually Editing a Timetable

1. The user opens a timetable.
2. The user selects a session.
3. The user proposes a new time slot or compatible room.
4. The application checks the proposed change.
5. The application accepts or rejects the edit according to the configured editing policy.
6. The application revalidates the updated schedule.
7. The user reviews the updated hard-constraint and soft-constraint results.
8. The user saves or discards the change.

**Expected outcome:** The current schedule and its validation status remain consistent.

## N.8 Workflow 8: Exporting a Timetable

1. The user selects the schedule to export.
2. The user selects CSV or Excel.
3. The application prepares the export.
4. The application verifies that the export operation completed.
5. The user obtains the exported file.
6. The user can inspect the exported session data.

**Expected outcome:** The exported file matches the selected saved schedule.

If the schedule is invalid, the application should clearly disclose its validation status before export. Whether invalid schedules may be exported is an open product decision.

---

# O. Error States and Edge Cases

| ID | Error or Edge Case | Expected System Behavior |
|---|---|---|
| ERR-001 | Invalid dataset format | Reject the file, explain the supported format, and allow another upload. |
| ERR-002 | Missing required fields | Identify missing fields and prevent generation until blocking errors are resolved. |
| ERR-003 | Duplicate entity identifiers | Report the conflicting identifiers and request correction. |
| ERR-004 | Invalid entity references | Identify references to nonexistent teachers, rooms, classes, or subjects. |
| ERR-005 | Infeasible scheduling problem | Report that no feasible schedule was established; claim proven infeasibility only when the search procedure justifies that conclusion. |
| ERR-006 | No solution found within search limit | Report search-limit termination and avoid claiming that no solution exists. |
| ERR-007 | Algorithm timeout | Stop or terminate execution safely where supported, report the timeout, and retain the previous valid schedule. |
| ERR-008 | Invalid manual edit | Reject the edit or preserve it as an explicitly invalid draft, according to the confirmed editing policy. |
| ERR-009 | Incompatible room | Prevent the assignment from being accepted as valid and explain the room incompatibility. |
| ERR-010 | Insufficient teacher availability | Report the relevant availability conflict or suspected infeasibility where diagnosable. |
| ERR-011 | Teacher workload exceeded | Reject the invalid assignment or mark the candidate invalid and report the workload violation. |
| ERR-012 | Missing required session | Report the unassigned requirement and prevent the schedule from being marked complete. |
| ERR-013 | Export failure | Display an error and allow the user to retry without falsely reporting successful export. |
| ERR-014 | Partial algorithm failure | Distinguish a partial candidate from a complete valid timetable. |
| ERR-015 | Stochastic algorithm produces inconsistent outcomes | Record each run independently and report the relevant configuration and outcome. |
| ERR-016 | Dataset changes after generation | Identify that the existing schedule was generated using an earlier dataset state and require appropriate revalidation or regeneration. |
| ERR-017 | Mandatory break conflict | Reject the assignment as valid and identify the affected resource and period. |
| ERR-018 | Invalid laboratory duration | Report that the session cannot satisfy its required consecutive-period duration. |
| ERR-019 | All rooms unsuitable | Report the room-suitability problem when detectable and distinguish it from an ordinary search-limit failure. |
| ERR-020 | Independent validator failure | Do not mark the schedule valid; report that validation could not be completed. |
| ERR-021 | Invalid algorithm configuration | Reject the configuration and identify the setting that must be corrected. |
| ERR-022 | No feasible starting schedule for hybrid optimization | Report that the hybrid procedure could not establish an acceptable starting schedule within its limits. |

## O.1 General Error-Handling Rules

The following principles apply to all errors:

1. Error messages must be understandable to the user.
2. The application must not silently convert failures into successful outcomes.
3. A failed run must not silently replace a previously valid schedule.
4. Partial assignments must remain distinguishable from complete assignments.
5. The validator must remain authoritative for hard-constraint validity.
6. Where the application cannot diagnose the exact cause of infeasibility, it must communicate that limitation rather than inventing a cause.
7. Recoverable errors should allow the user to correct inputs or retry the operation.

---

# P. Success Criteria

## P.1 Mandatory Completion Criteria

The project will be considered functionally complete when the following conditions are met.

### SC-001: Dataset Processing

Users can load the documented dataset format, configure scheduling inputs, and validate the dataset.

**Verification:** Test with valid and invalid sample datasets.

### SC-002: CSP Formulation

The scheduling problem is represented using variables, domains, and constraints.

**Verification:** Demonstrate how a sample scheduling problem maps to the CSP representation.

### SC-003: Backtracking CSP

The application implements Backtracking CSP with MRV, Degree Heuristic, and Forward Checking.

**Verification:** Automated tests demonstrate correct variable selection, domain reduction, backtracking, and solution validation.

### SC-004: Min-Conflicts

The application implements Min-Conflicts and records its outcome.

**Verification:** Demonstrate the algorithm on an appropriate dataset and independently validate the returned candidate.

### SC-005: Hard-Constraint Correctness

Every timetable marked valid has zero hard-constraint violations according to the independent validator.

**Verification:** Automated tests cover each enabled hard constraint.

### SC-006: Required Session Fulfillment

Every timetable marked complete contains all required teaching sessions.

**Verification:** Compare the scheduled sessions against the authoritative session requirements.

### SC-007: Timetable Views

Class-wise, teacher-wise, and room-wise views represent the same underlying schedule.

**Verification:** Cross-check a selected session across all applicable views.

### SC-008: Manual Editing

Manual edits trigger revalidation.

**Verification:** Introduce a conflict through an edit and verify that the application identifies it.

### SC-009: Export Consistency

Exported data matches the selected saved schedule.

**Verification:** Compare exported CSV and Excel records with the underlying schedule.

### SC-010: Experiment Evaluation

The application records comparable experiment metrics.

**Verification:** Run at least two supported algorithms on the same test dataset and inspect their recorded metrics.

### SC-011: Error Handling

The application distinguishes invalid input, unsuccessful search, search-limit termination, and export failure.

**Verification:** Exercise representative error cases and confirm the expected status messages.

### SC-012: Documentation

The project includes setup instructions, dataset documentation, algorithm descriptions, tests, and experimental findings.

**Verification:** Review the submitted project documentation.

## P.2 Proposed Quantitative Acceptance Targets

The following are proposed test targets, not claims about current performance.

| Metric | Proposed Target | Verification Method |
|---|---|---|
| Hard-constraint violations in schedules marked valid | Exactly 0 | Independent validator and automated tests |
| Required session fulfillment in schedules marked complete | 100% | Session-count comparison |
| Consistency across timetable views | 100% agreement on session assignments | Cross-view comparison tests |
| Export consistency | 100% agreement on exported session records | CSV and Excel comparison tests |
| Manual-edit validation | Every accepted edit triggers revalidation | Automated interaction tests |
| Required algorithm availability | All Must Have algorithms implemented | Functional demonstration |
| Constraint-validation coverage | Every configured hard constraint tested | Constraint-specific automated tests |
| Experiment traceability | Every recorded experiment identifies its dataset, algorithm, configuration, and outcome | Experiment metadata audit |

No fixed runtime threshold is required until representative measurements have been collected on the target environment.

## P.3 Optional Bonus Achievements

The following are desirable but not mandatory for the initial minimum viable product:

1. Implement Simulated Annealing.
2. Implement Hybrid CSP + Simulated Annealing.
3. Improve soft-constraint quality beyond an initial feasible timetable.
4. Run repeated experiments for stochastic algorithms.
5. Produce statistical summaries of experimental results.
6. Provide advanced infeasibility diagnostics.
7. Support additional dataset formats.
8. Add richer visualizations for schedule quality and algorithm behavior.

---

# Q. Scope and Out of Scope

## Q.1 In Scope

The initial academic prototype includes:

- Python-based application logic.
- Streamlit dashboard.
- Dataset upload and sample dataset selection.
- Entity and scheduling requirement configuration.
- Dataset validation.
- CSP formulation.
- Backtracking CSP.
- MRV and Degree Heuristic.
- Forward Checking.
- Min-Conflicts.
- Simulated Annealing as a bonus.
- Hybrid CSP + Simulated Annealing as a bonus.
- Hard-constraint validation.
- Soft-constraint scoring.
- Class-wise, teacher-wise, and room-wise views.
- Manual timetable editing.
- Revalidation after editing.
- CSV and Excel export.
- Experiment execution.
- Algorithm comparison.
- Small and large sample datasets.
- Automated tests.
- Experimental documentation.
- Academic project report.

## Q.2 Out of Scope

The following are excluded from the initial prototype unless the project requirements are formally expanded.

### Institutional Authentication

The application will not initially implement institutional single sign-on, account provisioning, or role-based authorization.

### University ERP Integration

Integration with university management systems, attendance platforms, student information systems, or existing timetable databases is excluded.

### Production Deployment

The initial project does not require a production-grade cloud deployment, high availability, or enterprise operations infrastructure.

### Multi-Campus Optimization

Simultaneous scheduling across multiple campuses with travel-time restrictions is excluded.

### Advanced Distributed Optimization

Distributed search, large-scale parallel optimization, and specialized high-performance computing are excluded unless later required.

### Automatic Institutional Policy Discovery

The application will not automatically infer institutional scheduling rules from unstructured documents.

### Live External Data Integration

Real-time integration with external academic calendars, room booking systems, or staff availability services is excluded.

### Full Student-Level Personalized Scheduling

The initial application schedules classes and teaching resources rather than independently optimizing individual student timetables across elective combinations.

### Guaranteed Global Optimality

The project does not guarantee that every generated timetable will have the globally lowest possible soft-constraint penalty.

### Universal Scalability Guarantees

The project does not promise that every algorithm will solve arbitrarily large scheduling problems within a fixed runtime.

---

# R. Assumptions, Dependencies, and Risks

## R.1 Assumptions

### ASM-001: Fixed Planning Horizon

The initial timetable covers a configured weekly schedule.

The default proposed planning horizon is five teaching days per week.

### ASM-002: Discrete Time Slots

The initial prototype uses discrete periods rather than arbitrary start and end times.

A session occupying multiple periods must be represented in a way that preserves its duration and resource occupancy.

### ASM-003: Known Resource Requirements

Teacher assignments, room requirements, subject requirements, and class membership are supplied through the dataset.

The system does not need to infer these values automatically.

### ASM-004: Single Authoritative Constraint Configuration

Each experiment uses one explicit set of active hard constraints, soft constraints, and penalty weights.

### ASM-005: Independent Validation

Every algorithm produces a candidate that is evaluated by the same independent validator.

### ASM-006: Single-Session Academic Prototype

The initial interface is designed for a project team or timetable coordinator using the application, rather than a large number of simultaneous institutional users.

### ASM-007: Configurable Search Limits

Search limits are necessary to manage computational resources.

Reaching a search limit does not establish infeasibility.

## R.2 Dependencies

| Dependency ID | Dependency | Impact |
|---|---|---|
| DEP-001 | Python runtime and required libraries | Required to run the application and scheduling algorithms. |
| DEP-002 | Streamlit | Required for the interactive user interface. |
| DEP-003 | Input dataset specification | Required for consistent data loading and validation. |
| DEP-004 | Defined constraint model | Required for algorithm correctness and consistent validation. |
| DEP-005 | Soft-constraint scoring specification | Required for meaningful schedule-quality comparisons. |
| DEP-006 | Independent validator | Required to establish timetable validity. |
| DEP-007 | Sample datasets | Required for development, demonstration, and evaluation. |
| DEP-008 | Automated tests | Required to verify constraint correctness and regression safety. |
| DEP-009 | Export dependencies | Required for generating CSV and Excel files. |
| DEP-010 | Documented experimental configuration | Required for reproducible algorithm comparisons. |

## R.3 Risk Register

### RISK-001: Poor Dataset Quality

**Risk:** Missing or inconsistent inputs may prevent scheduling or produce misleading results.

**Impact:** High.

**Mitigation:**
- Define a documented dataset schema.
- Validate inputs before generation.
- Provide sample datasets.
- Include tests for malformed input.

### RISK-002: Infeasible Constraint Combinations

**Risk:** A dataset may contain mutually incompatible requirements.

**Impact:** High.

**Mitigation:**
- Validate obvious contradictions before search.
- Provide clear failure statuses.
- Test deliberately infeasible datasets.
- Distinguish proven infeasibility from search-limit termination.

### RISK-003: Combinatorial Search Complexity

**Risk:** Search time may increase significantly with problem size.

**Impact:** High.

**Mitigation:**
- Implement MRV, Degree Heuristic, and Forward Checking.
- Record search nodes and runtime.
- Configure search limits.
- Evaluate performance on different dataset sizes.

### RISK-004: Runtime Limitations

**Risk:** Some datasets may exceed practical runtime or memory limits.

**Impact:** High.

**Mitigation:**
- Define configurable termination limits.
- Monitor execution status.
- Avoid unbounded search.
- Report incomplete attempts accurately.

### RISK-005: Failure to Find a Solution

**Risk:** A heuristic or local-search algorithm may fail to find a valid schedule even when one exists.

**Impact:** High.

**Mitigation:**
- Use the CSP solver as the primary systematic approach.
- Evaluate stochastic algorithms across repeated runs.
- Record initialization and configuration.
- Avoid interpreting heuristic failure as proof of infeasibility.

### RISK-006: Inconsistent Hard-Constraint Definitions

**Risk:** The solver and validator may apply different interpretations of a scheduling rule.

**Impact:** Critical.

**Mitigation:**
- Maintain a single authoritative constraint specification.
- Test each constraint independently.
- Run the independent validator on every final candidate.
- Treat discrepancies between solver and validator as defects.

### RISK-007: Manual Editing Introduces Conflicts

**Risk:** A previously valid timetable may become invalid after a user changes a session.

**Impact:** High.

**Mitigation:**
- Validate each accepted edit.
- Display the current validation status.
- Keep saved and draft states distinguishable where invalid drafts are supported.
- Recalculate soft-constraint penalties.

### RISK-008: Unfair Comparison of Stochastic Algorithms

**Risk:** Different random initializations may produce substantially different results.

**Impact:** Medium to High.

**Mitigation:**
- Record random seeds where controllable.
- Use repeated runs when feasible.
- Keep dataset and scoring configurations consistent.
- Report success rates and distributions instead of relying on a single favorable run.

### RISK-009: Soft-Constraint Score Misinterpretation

**Risk:** Users may interpret a low soft-constraint penalty as proof of timetable validity.

**Impact:** High.

**Mitigation:**
- Display hard validity separately.
- Do not rank invalid schedules as equivalent to valid schedules.
- Document penalty definitions and weights.
- Require independent validation before a result is marked valid.

### RISK-010: Incorrect Laboratory Scheduling

**Risk:** A laboratory session may be assigned to incompatible periods or split when continuity is mandatory.

**Impact:** High.

**Mitigation:**
- Represent session duration and continuity requirements explicitly.
- Test consecutive-period assignments.
- Include laboratory-specific validation cases.

### RISK-011: Stale Validation Results

**Risk:** The application may display validation results calculated before the latest edit.

**Impact:** High.

**Mitigation:**
- Invalidate previous validation results after relevant changes.
- Revalidate the current schedule before marking it valid.
- Associate results with the evaluated schedule state.

### RISK-012: Export Mismatch

**Risk:** Exported data may differ from the displayed schedule.

**Impact:** Medium.

**Mitigation:**
- Export from the authoritative saved schedule.
- Test CSV and Excel records against the same source.
- Report export completion only after successful generation.

### RISK-013: Inconsistent Experiment Conditions

**Risk:** Algorithm comparisons may be misleading if algorithms use different constraints, scoring weights, or termination conditions.

**Impact:** High.

**Mitigation:**
- Record all relevant configurations.
- Use identical dataset requirements.
- Standardize metric definitions.
- Disclose differences in search limits.

### RISK-014: Scope Expansion

**Risk:** Bonus algorithms and advanced features may delay the essential implementation.

**Impact:** Medium.

**Mitigation:**
- Complete the minimum viable product first.
- Prioritize core CSP functionality and validation.
- Implement bonus algorithms only after core acceptance criteria pass.

---

# S. Deliverables and Roadmap

## S.1 Required Deliverables

### DEL-001: Working Application

A functioning Streamlit application that supports dataset loading, validation, algorithm selection, timetable generation, review, editing, and export.

### DEL-002: Source Code

Organized Python source code implementing the application and required algorithms.

### DEL-003: Sample Datasets

Documented small and large datasets, including representative feasible and infeasible test cases.

### DEL-004: Automated Tests

Tests covering:
- Dataset validation.
- Constraint checking.
- CSP behavior.
- Heuristic behavior.
- Local-search behavior.
- Manual editing.
- Export consistency.
- Error handling.

### DEL-005: Experimental Results

A record of algorithm experiments containing:
- Dataset identity.
- Algorithm and configuration.
- Runtime.
- Hard-constraint violations.
- Soft-constraint penalty.
- Search nodes or iterations where supported.
- Termination status.

### DEL-006: User Documentation

Instructions for:
- Installing and running the application.
- Preparing datasets.
- Configuring scheduling constraints.
- Selecting algorithms.
- Interpreting results.
- Editing and exporting timetables.

### DEL-007: Project Report

An academic report describing:
- Problem definition.
- CSP formulation.
- Algorithm design.
- Constraint model.
- System functionality.
- Test methodology.
- Experimental results.
- Limitations.
- Future work.

## S.2 Optional Deliverables

### DEL-008: Simulated Annealing

An optional implementation and experimental evaluation.

### DEL-009: Hybrid CSP + Simulated Annealing

An optional hybrid solver and comparison against standalone algorithms.

### DEL-010: Advanced Experimental Analysis

Optional repeated-run statistics, visualizations, and deeper performance analysis.

## S.3 Phased Implementation Roadmap

The roadmap is ordered by dependency and importance. It does not prescribe fixed calendar dates.

### Phase 1: Requirements and Dataset Definition

**Objective:** Establish the scheduling model and test data.

**Activities:**
- Finalize the dataset schema.
- Define session representation.
- Define hard constraints.
- Define soft constraints and weights.
- Prepare small and large sample datasets.
- Prepare invalid and infeasible test cases.

**Exit criteria:**
- Dataset requirements are documented.
- Sample datasets can be validated.
- Constraint definitions are unambiguous.

### Phase 2: Core Data Validation and Constraint Model

**Objective:** Establish the foundation for reliable scheduling.

**Activities:**
- Implement input validation.
- Define variables and domains.
- Establish constraint-checking behavior.
- Implement independent hard-constraint validation.
- Implement soft-constraint evaluation.
- Add tests for each hard constraint.

**Exit criteria:**
- Invalid inputs are identified.
- Candidate schedules can be independently validated.
- Hard-constraint and soft-constraint results are reported separately.

### Phase 3: Backtracking CSP

**Objective:** Implement the primary scheduling algorithm.

**Activities:**
- Implement Backtracking CSP.
- Integrate MRV.
- Integrate Degree Heuristic.
- Integrate Forward Checking.
- Add termination controls.
- Record runtime and search nodes.

**Exit criteria:**
- The solver can generate a valid schedule for the selected feasible sample dataset.
- Search-limit termination is distinguishable from exhaustive failure.
- Automated tests demonstrate the required heuristic behavior.

### Phase 4: Min-Conflicts

**Objective:** Implement and evaluate local-search scheduling.

**Activities:**
- Define initialization behavior.
- Implement Min-Conflicts.
- Define its hard-constraint handling policy.
- Record iteration counts and runtime.
- Evaluate success rates.

**Exit criteria:**
- The algorithm returns a candidate or a clear failure status.
- Candidate schedules are independently validated.
- Results are recorded consistently.

### Phase 5: Streamlit Application

**Objective:** Deliver the primary user experience.

**Activities:**
- Implement dataset selection and upload.
- Build input-validation views.
- Add algorithm selection.
- Add generation controls.
- Add timetable tables and filters.
- Add validation results.
- Add status messages.

**Exit criteria:**
- Users can complete the core workflow without directly interacting with source code.

### Phase 6: Editing and Export

**Objective:** Make generated schedules usable and adjustable.

**Activities:**
- Implement manual timetable editing.
- Add revalidation after edits.
- Implement CSV export.
- Implement Excel export.
- Verify schedule consistency across views and exports.

**Exit criteria:**
- Accepted edits trigger validation.
- Exported data matches the selected saved schedule.

### Phase 7: Experiments and Comparison

**Objective:** Evaluate algorithm behavior scientifically.

**Activities:**
- Define experiment configurations.
- Record runtime and search effort.
- Record validity and soft-constraint penalties.
- Compare algorithms on the same datasets.
- Repeat stochastic runs where feasible.
- Document limitations and findings.

**Exit criteria:**
- Comparable experiment results are available.
- All recorded results identify their dataset and configuration.
- Conclusions are supported by the measured results.

### Phase 8: Bonus Optimization Algorithms

**Objective:** Extend the application beyond its core requirements.

**Activities:**
- Implement Simulated Annealing.
- Implement Hybrid CSP + Simulated Annealing.
- Compare optimization outcomes.
- Evaluate whether soft-constraint quality improves while feasibility is preserved.

**Exit criteria:**
- Bonus algorithms are independently validated.
- Their configurations and results are documented.
- No invalid result is presented as a successful final timetable.

### Phase 9: Final Testing and Documentation

**Objective:** Prepare the academic submission.

**Activities:**
- Run regression tests.
- Verify all mandatory acceptance criteria.
- Document experimental results.
- Prepare application instructions.
- Complete the project report.
- Demonstrate the system using sample datasets.

**Exit criteria:**
- Mandatory success criteria are met.
- Known limitations are documented.
- The application can be demonstrated reliably.

---

# T. Traceability Matrix

This matrix connects project objectives to functional requirements, acceptance evidence, and evaluation metrics.

| Objective ID | Objective | Related Functional Requirements | Acceptance Evidence | Evaluation Metrics |
|---|---|---|---|---|
| OBJ-001 | Automatically generate timetables | FR-006, FR-007, FR-008, FR-011 | A complete timetable is generated for a feasible dataset. | Success rate, runtime |
| OBJ-002 | Model scheduling as a CSP | FR-008 | Variables, domains, and constraints are documented and demonstrated. | Search nodes, solution validity |
| OBJ-003 | Implement Backtracking CSP | FR-008 | Solver produces a valid schedule or a correctly classified termination status. | Runtime, search nodes, success rate |
| OBJ-004 | Implement CSP heuristics | FR-009, FR-010 | MRV, Degree Heuristic, and Forward Checking pass targeted tests. | Search nodes, runtime |
| OBJ-005 | Implement Min-Conflicts | FR-011 | Algorithm returns a candidate or documented failure status. | Iterations, runtime, success rate |
| OBJ-006 | Enforce hard constraints | FR-014, FR-016, FR-021 | Every schedule marked valid has zero hard-constraint violations. | Hard-constraint violation count |
| OBJ-007 | Evaluate soft constraints | FR-015 | Enabled penalty components and aggregate score are calculated consistently. | Soft-constraint penalty |
| OBJ-008 | Provide Streamlit dashboard | FR-001, FR-006, FR-007, FR-017 to FR-028 | User can complete the primary workflow through the interface. | Workflow acceptance tests |
| OBJ-009 | Support different dataset sizes | FR-001, FR-002, FR-023 | Small and large datasets can be loaded and evaluated. | Runtime, success rate, search effort |
| OBJ-010 | Compare algorithms | FR-023, FR-024, FR-025 | Comparable results are displayed with configuration metadata. | Runtime, success rate, penalty, search effort |
| OBJ-011 | Provide multiple timetable views | FR-017, FR-018, FR-019 | Views agree on all session assignments. | Cross-view consistency |
| OBJ-012 | Support manual editing | FR-020, FR-021 | Edits are reflected in the schedule and trigger revalidation. | Validation status, penalty change |
| OBJ-013 | Export schedules | FR-022 | CSV and Excel outputs match the selected saved schedule. | Export consistency |
| OBJ-014 | Provide actionable feedback | FR-026, FR-027 | Representative errors produce appropriate messages and statuses. | Error-handling test results |
| OBJ-015 | Reproduce experiments | FR-023, FR-025 | Runs contain dataset, algorithm, configuration, runtime, and outcome metadata. | Experiment traceability |
| OBJ-016 | Implement Simulated Annealing | FR-012 | Bonus algorithm returns a candidate and records its outcome. | Runtime, penalty, validity |
| OBJ-017 | Implement hybrid optimization | FR-013 | Hybrid algorithm records initial and final scores and validates the final schedule. | Runtime, penalty improvement, validity |
| OBJ-018 | Produce statistical summaries | FR-024, FR-025 | Repeated-run results can be summarized. | Mean, median, range, success rate |
| OBJ-019 | Provide schedule diagnostics | FR-005, FR-014, FR-026 | Detectable conflicts and relevant causes are reported accurately. | Constraint-specific test results |

## T.1 Traceability Rules

1. Every mandatory objective must map to at least one functional requirement.
2. Every mandatory functional requirement must have testable acceptance criteria.
3. Every hard constraint must have a corresponding validation test.
4. Every algorithm must be evaluated through the same independent validator.
5. Every experiment must identify the dataset and relevant algorithm configuration.
6. Any change to a hard constraint must be reflected in the solver, validator, relevant tests, and experiment documentation.
7. A requirement must not be considered complete solely because its user interface has been implemented.

---

# U. Open Questions

The following decisions should be resolved before finalizing the technical design.

These questions do not invalidate the PRD. They identify areas where the initial product specification needs further confirmation.

## U.1 Dataset and Session Modeling

**OQ-001: What input format should be used?**

Proposed default: CSV for individual datasets, with a documented schema and optional bundled sample datasets.

Decision needed: Whether Excel input is also required.

**OQ-002: How should repeated sessions be represented?**

Proposed default: Each required occurrence is represented as a schedulable session, with the required weekly total enforced by the scheduling model.

Decision needed: Whether weekly requirements are specified as periods, sessions, or teaching hours.

**OQ-003: Are all classes restricted to the same weekly calendar?**

Proposed default: All classes use a common set of teaching days and period definitions.

Decision needed: Whether different classes may have different calendars or period structures.

## U.2 Scheduling Rules

**OQ-004: Are mandatory lunch breaks identical for all classes and teachers?**

Proposed default: Break rules are configurable by applicable resource.

Decision needed: Whether lunch periods are globally fixed or resource-specific.

**OQ-005: Which laboratory sessions require consecutive periods?**

Proposed default: Each laboratory requirement explicitly declares whether consecutive periods are mandatory or preferred.

Decision needed: The exact duration and continuity rules for laboratory sessions.

**OQ-006: Can teachers teach multiple sections of the same subject?**

Proposed default: Yes, provided the dataset explicitly assigns each relevant session to the teacher.

Decision needed: Whether the system must automatically determine teacher assignments or only schedule preassigned teachers.

**OQ-007: Are teacher workload limits daily, weekly, or both?**

Proposed default: Support configurable daily and weekly limits.

Decision needed: Which limits are mandatory for the academic evaluation.

**OQ-008: Can a teacher have preferred periods in addition to unavailable periods?**

Proposed default: Yes. Unavailable periods are hard constraints, while preferences are soft constraints.

Decision needed: Whether preference weights are user-configurable or fixed for the initial prototype.

## U.3 Algorithm Behavior

**OQ-009: How should Min-Conflicts handle hard constraints?**

Proposed default: The algorithm should use a clearly documented strategy that prevents hard-constraint violations in accepted final schedules.

Decision needed: Whether the initial assignment must already be feasible or whether a separate feasibility-repair stage is allowed.

**OQ-010: Should Simulated Annealing be implemented in the initial submission?**

Proposed default: No. It is a bonus feature to be considered after all mandatory requirements pass.

Decision needed: Whether the project evaluator expects it as a required demonstration.

**OQ-011: What is the intended behavior of the hybrid algorithm when CSP does not find a feasible starting schedule?**

Proposed default: Report that the hybrid run could not establish a feasible starting schedule within its limits.

Decision needed: Whether an optional fallback to another initialization strategy is required.

**OQ-012: What termination limits should be used?**

Proposed default: Make limits configurable and record their values in experiment metadata.

Decision needed: Appropriate default limits based on observed runtime and the available hardware.

## U.4 Optimization and Evaluation

**OQ-013: What soft-constraint weights should be used?**

Proposed default: Define and document an initial weight for each enabled soft constraint, then use the same configuration for comparable experiments.

Decision needed: The initial weight values and whether users can change them.

**OQ-014: How should the application choose the best timetable?**

Proposed default: Feasibility first, followed by soft-constraint penalty. Runtime and search effort are used to evaluate algorithm performance rather than directly determining timetable quality.

Decision needed: Whether the interface should allow users to prioritize particular soft constraints.

**OQ-015: How many repeated runs should be conducted for stochastic algorithms?**

Proposed default: Use repeated runs when practical and document the number of runs and random seeds.

Decision needed: The experiment count appropriate for the available time and computational resources.

## U.5 User Experience and Data Handling

**OQ-016: Should invalid manual edits be rejected immediately or retained as drafts?**

Proposed default: Prevent invalid edits from replacing the current valid schedule. An explicitly labeled draft may be retained if useful.

Decision needed: Whether draft editing is necessary for the initial prototype.

**OQ-017: Should invalid timetables be exportable?**

Proposed default: Valid schedules are the primary export target. If invalid drafts are exportable, their validation status must be disclosed.

Decision needed: Whether to support export of incomplete or invalid candidates.

**OQ-018: Is session-level persistence required?**

Proposed default: In-memory operation is sufficient for the initial academic prototype, subject to the chosen Streamlit session model.

Decision needed: Whether schedules and experiment results must survive application restarts.

**OQ-019: Is authentication required?**

Proposed default: No authentication for the local academic prototype.

Decision needed: Whether the intended demonstration environment requires multiple users or protected access.

## U.6 Acceptance and Demonstration

**OQ-020: What hardware will be used for evaluation?**

Proposed default: Document the evaluation machine and Python environment.

Decision needed: The target machine for the final runtime measurements.

**OQ-021: What is the minimum acceptable success rate for the large dataset?**

Proposed default: Establish a target only after defining the dataset's feasibility and conducting initial experiments.

Decision needed: Whether a numerical success-rate target is required by the evaluator.

**OQ-022: Which deliverables are mandatory for the academic submission?**

Proposed default: Working application, source code, datasets, tests, experimental results, documentation, and project report.

Decision needed: Whether Simulated Annealing, the hybrid algorithm, or any additional presentation materials are mandatory.

---

# V. Final Product Definition

The AI-Based Timetable Scheduler is an academic AI application that formulates academic scheduling as a constraint satisfaction problem, applies search and optimization algorithms, and independently evaluates the resulting schedules.

The minimum viable product consists of:

1. A documented dataset format and sample datasets.
2. Input validation and scheduling configuration.
3. Backtracking CSP with MRV, Degree Heuristic, and Forward Checking.
4. Min-Conflicts local search.
5. Independent hard-constraint validation.
6. Weighted soft-constraint evaluation.
7. An interactive Streamlit dashboard.
8. Class-wise, teacher-wise, and room-wise timetable views.
9. Manual timetable editing and revalidation.
10. CSV and Excel export.
11. Experiment execution and algorithm comparison.
12. Automated tests and academic documentation.

Simulated Annealing and Hybrid CSP + Simulated Annealing are optional extensions.

The product's central acceptance principle is:

**A timetable is not considered successfully generated merely because an algorithm returns a schedule. It must contain every required session, satisfy all active hard constraints, and pass independent validation.**

Soft-constraint optimization is then used to compare the quality of valid timetables. Experimental results determine how effectively the algorithms perform on the selected datasets.

This PRD establishes the product scope and acceptance criteria. Detailed software architecture, module responsibilities, data schemas, algorithm interfaces, implementation-level decisions, and technical specifications are intentionally reserved for the separate Technical Requirements Document (TRD).

---

**End of Document**

**Document:** `PRD.md`
**Version:** 1.0
**Status:** Draft — Proposed for Academic Project Approval