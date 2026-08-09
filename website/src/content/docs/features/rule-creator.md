---
title: Rule Creator
description: A GUI for building Sigma, Yara, and Snort/Suricata rules.
sidebar:
  order: 130
---

A guided GUI for authoring detection rules across three formats:

- **[Sigma](https://github.com/SigmaHQ/sigma)** — generic SIEM detection rules.
- **[Yara](https://github.com/VirusTotal/yara)** — pattern-matching rules for identifying and
  classifying files/malware.
- **Snort/Suricata** — network intrusion detection rules.

Useful for turning an investigation's findings — an IOC from IOC Tools, a pattern spotted in
Email Analyzer, a technique tagged by Newsfeed — into something you can actually deploy, without
hand-writing rule syntax from scratch.
