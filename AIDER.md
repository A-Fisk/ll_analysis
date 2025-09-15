# Aider assistant instructions

Always follow the instructions in this file

## General
- **Start each session by asking to add TODO.md and log.md**

## Todo
- TODO list is kept in TODO.md
- Never delete anything from this list
- Only add items, tick things off, or mark as complete
- Always document every task as a set of TODO tasks
- Always display the TODO list at the top of every response.
- Only display uncompleted items and the 5 most recent completed items from the
  TODO list.
- Never do anything that is already marked as done

## Log
- Log is kept in log.md
- Only ever append lines to the end, never delete or modify previous steps.
- Summarise every step in log md

## Code Style
- All code run by main file which is defined at the top of the script below
  imports
- Main function should be clear enough to read like pseudo-code
- All code run by functions which are defined after main file
- All code should execute from the root of the git repo
- Only functions *not* called in main should start with _
- Create NumPy style docstrings for all functions

## Example 
```
# imports 
import pandas as pd
# other imports here 

# main function
def main():

    data = import_data (**kwargs) 

    first_step = step_one(**kwargs)

    second_step = step_two(**kwargs)

    third_step = step_three(**kwargs)

# import data function
def import_data(**kwargs):
    # importing logic here 

    return data

# define step functions 
def step_one(**kwargs):
    # step one logic here

    return first_step

def step_two(**kwargs):
    # step two logic here 

    return second_step

def step_three(**kwargs):
    # step three logic here

    return third_step

if __name__ == "__main__":
    main()
```
