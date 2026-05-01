# Changelog

All notable changes to this project will be documented in this file.

The format is based on **Keep a Changelog**  
and this project follows **Semantic Versioning (SemVer)**.

---

## [Unreleased]

### Added
- Planned: real-time scraping improvements
- Planned: data quality validation layer
- Planned: dashboard enhancements (Streamlit)
- Planned: CI/CD pipeline for ETL automation

---

## [0.2.0] - 2026-05-01

### Added
- PostgreSQL Data Warehouse schema (star schema design)
- ETL pipeline orchestration (Extract → Transform → Load)
- Data cleaning layer with:
  - type normalization
  - missing value handling
  - deduplication logic
- Safe insert strategy using `ON CONFLICT DO NOTHING`
- Structured logging system for pipeline monitoring

### Changed
- Improved scraping stability and retry logic
- Refactored ETL scripts into modular architecture

### Fixed
- Fixed duplicate listings insertion issue in database
- Fixed inconsistent numeric parsing in price field

---

## [0.1.0] - 2026-04-20

### Added
- Initial web scraping module for Avito.ma real estate listings
- Raw data storage pipeline (CSV + staging database)
- Basic PostgreSQL integration
- First version of data schema design
- Project structure initialization

---

## [0.0.1] - 2026-04-10

### Added
- Repository setup
- Basic project structure
- README initial version