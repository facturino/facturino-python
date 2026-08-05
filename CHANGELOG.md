# Changelog

All notable changes to the `facturino` Python SDK are documented here. This
project adheres to [Semantic Versioning](https://semver.org/) and
[Keep a Changelog](https://keepachangelog.com/).

## [1.1.0] - 2026-08-05

### Added
- Document `paypal` as an accepted payment method. The SDK is dynamically typed,
  so the value already passes straight through; the API may add further payment
  method values over time — tolerate unknown values.

## [1.0.1] - 2026-07-25

### Changed
- Packaging/CI: enable `skip-existing` on the PyPI publish workflow; raise the
  minimum supported Python to 3.10 (drop 3.9).

## [1.0.0] - 2026-07-25 — Initial release
