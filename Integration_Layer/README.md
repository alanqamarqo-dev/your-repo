# Integration Layer

This directory contains the orchestration logic that binds the Core Engines together. It is responsible for routing tasks, managing context, and synthesizing results.

## Key Components

- **Mission_Control.py** (or similar): The high-level planner that breaks down complex user requests.
- **Orchestrator.py**: Manages the flow of data between different engines.
- **Prompt_Composer.py**: Constructs optimized prompts for the LLM based on the active engines and context.

## Role

The Integration Layer acts as the "Prefrontal Cortex" of the AGL system, making executive decisions on which engine to use and how to combine their outputs.
