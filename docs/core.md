# Core

This section provides an overview of the `adqa.core` module.

## Introduction

The `adqa.core` module is intended to house the fundamental building blocks and core logic of the Autonomous Data Quality Agent. 

## Excepted implementations (Currently placeholders)

- [`agent.py`](src/adqa/core/agent.py): This file is expected to define the base `Agent` class or interface, from which specific data quality agents will inherit. It will likely establish common behaviors and properties for all agents within the system.
- [`controller.py`](src/adqa/core/controller.py): This file is anticipated to contain the `Controller` logic, responsible for orchestrating the execution of various agents, managing workflows, and handling interactions between different components of the ADQA system.
- [`datasource.py`](src/adqa/core/datasource.py): This file is designated for defining `DataSource` abstractions, enabling the ADQA to connect to and interact with different data sources (e.g., databases, data lakes, APIs) to retrieve and process data for quality checks.
- [`models.py`](src/adqa/core/models.py): This file is likely to contain data models and Pydantic schemas used across the core components, ensuring data consistency and validation for inputs, outputs, and internal states of the ADQA system.

As development progresses, these files will be populated with the detailed implementations that form the backbone of the ADQA's operational capabilities.
