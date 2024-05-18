# Bots of the SOC

## Overview of project

This project is aiming to created a fully autonomous system cable of solving the Splunk Boss of the SOC challenges with no human interaction. They system should be able to solve all questions if provided only with the question set.

The system uses OpenAI's GPT4 with AutoGen to create a multi agent system with RAG.

## Included files

- Bots_of_the_SOC_Group_chat.py: This is a basic PoC using a group chat.
- field_explorer.py: A script to create 'botsv2_splunk_fields.json' that is used to accelerate field lookups.
- splunk_functions.py: An import containing both the python and AutoGen functions required for the agents.
- system_messages.py: A lookup containing the system messages used for the agents.

## Excluded files required for operation

- OAI_CONFIG_LIST: OpenAI API keys for each model.
- .env: Dotenv file with Splunk credentials and OpenAI key.