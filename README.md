# AI-Based Timetable Scheduler

A Constraint Satisfaction Problem (CSP) approach to automatic academic timetable generation.

## Tech Stack

- **Python 3.11+** — core language
- **Streamlit** — interactive web UI
- **pandas / openpyxl** — data handling and Excel export
- **matplotlib** — experiment comparison charts
- **pytest** — automated testing

## Quick Start

```bash
# 1. Create a virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the app
streamlit run app.py
```

## Project Structure

```
├── app.py                   # Streamlit entry point (routing only)
├── requirements.txt
├── pytest.ini
├── data/                    # Sample datasets (JSON)
├── src/
│   ├── csp/                 # CSP core: variables, domains, constraints, validator
│   ├── algorithms/          # Backtracking, Min-Conflicts, SA, Hybrid
│   ├── services/            # Data loading, generation, editing, export
│   ├── evaluation/          # Experiment runner, metrics, plotting
│   └── ui/                  # Streamlit page modules
├── tests/                   # pytest test suite
├── experiments/             # Experiment results and figures
├── reports/                 # Project reports
└── docs/                    # Additional documentation
```

## Algorithms

| Algorithm | Type | Status |
|---|---|---|
| Backtracking + MRV + Degree + Forward Checking | CSP Search | Core |
| Min-Conflicts | Local Search | Core |
| Simulated Annealing | Metaheuristic | Bonus |
| Hybrid CSP + SA | Combined | Bonus |
