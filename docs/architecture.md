# Architecture

## Product boundary

AI Cartoon Studio produces complete original episodes and their related media assets. Publishing integrations are deliberately outside the first production boundary; approved exports can be uploaded manually.

## Control plane

The FastAPI application owns projects, series, characters, episodes, scenes, shots, jobs, approvals, costs, and provider configuration.

## Production pipeline

Each episode moves through explicit stages:

`concept -> story -> script -> direction -> visual assets -> animated shots -> voice -> lip sync -> sound -> quality control -> render -> approval`

Every stage stores its inputs, outputs, provider metadata, cost, status, and retry history. This makes individual shots reproducible and prevents a failure from invalidating the entire episode.

## Provider boundary

LLM, image, video, voice, lip-sync, music, and rendering capabilities are expressed as interfaces. Concrete provider adapters live behind those interfaces and may be changed without modifying production workflows.

## Continuity

A series bible and character profiles are permanent sources of truth. Episode plans reference immutable versions of character appearance, wardrobe, voice, personality, locations, props, and world rules.

## Human approval

Automatic generation stops at review checkpoints. A user may approve, reject, edit, or regenerate an individual artifact before the workflow continues.
