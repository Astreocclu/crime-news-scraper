# Task Master User Guide

## Introduction

Task Master is a powerful task management system that allows you to organize your projects with hierarchical tasks and subtasks. It provides a flexible way to track progress, set priorities, manage dependencies, and organize your work efficiently.

## Key Features

- **Hierarchical Task Structure**: Create main tasks with nested subtasks to any depth
- **Task Status Tracking**: Monitor the progress of tasks with different status options
- **Priority Management**: Assign priorities to tasks to focus on what's most important
- **Dependency Management**: Define dependencies between tasks to establish workflow
- **Project Organization**: Create a dedicated folder for each project with its own tasks
- **Command-Line Interface**: Manage tasks efficiently through a simple CLI

## Getting Started

### Basic Concepts

- **Task**: A unit of work with attributes like description, status, priority, and notes
- **Subtask**: A task that belongs to a parent task, creating a hierarchical structure
- **Task ID**: A unique identifier for each task, used for referencing in commands
- **Task File**: A JSON file that stores all tasks for a project

### Setting Up a New Project

1. Create a new directory for your project
2. Initialize a task file for your project:
   ```bash
   python -m task_manager.cli add "My Project" --notes "Description of my project"
   ```

## Using the Command-Line Interface

The Task Master CLI provides several commands for managing tasks:

### Adding Tasks

To add a new top-level task:
```bash
python -m task_manager.cli add "Task description" --priority 1 --notes "Additional notes"
```

To add a subtask to an existing task:
```bash
python -m task_manager.cli add "Subtask description" --parent task-id --priority 2
```

### Listing Tasks

To list all top-level tasks:
```bash
python -m task_manager.cli list
```

To list all tasks (including subtasks):
```bash
python -m task_manager.cli list --all
```

To filter tasks by status:
```bash
python -m task_manager.cli list --status pending
```

To filter tasks by priority:
```bash
python -m task_manager.cli list --priority 1
```

To show only available tasks (not blocked by dependencies):
```bash
python -m task_manager.cli list --available
```

To show only blocked tasks:
```bash
python -m task_manager.cli list --blocked
```

### Updating Tasks

To update a task's description:
```bash
python -m task_manager.cli update task-id --description "New description"
```

To update a task's status:
```bash
python -m task_manager.cli update task-id --status completed
```

Valid status values are:
- `pending`: Task is waiting to be started
- `in_progress`: Task is currently being worked on
- `completed`: Task is finished
- `failed`: Task could not be completed
- `blocked`: Task is blocked by dependencies

To update a task's priority:
```bash
python -m task_manager.cli update task-id --priority 2
```

To update a task's notes:
```bash
python -m task_manager.cli update task-id --notes "New notes"
```

To add dependencies:
```bash
python -m task_manager.cli update task-id --add-dependencies task-id-1 task-id-2
```

To remove dependencies:
```bash
python -m task_manager.cli update task-id --remove-dependencies task-id-1
```

### Removing Tasks

To remove a task:
```bash
python -m task_manager.cli remove task-id
```

### Showing Task Details

To show detailed information about a task:
```bash
python -m task_manager.cli show task-id
```

## Project Organization Strategies

### Creating a Project Structure

For effective project management, consider organizing your tasks in a hierarchical structure:

1. **Main Project Task**: Create a top-level task for the entire project
2. **Major Components**: Add subtasks for major components or phases
3. **Specific Tasks**: Break down components into specific tasks
4. **Detailed Steps**: Add further subtasks for detailed steps if needed

Example:
```
Website Development Project
├── Frontend Development
│   ├── Design UI mockups
│   ├── Implement HTML/CSS
│   └── Add JavaScript functionality
├── Backend Development
│   ├── Set up database
│   ├── Create API endpoints
│   └── Implement authentication
└── Deployment
    ├── Configure server
    ├── Set up CI/CD pipeline
    └── Deploy to production
```

### Using a Dedicated Folder for Each Project

For better organization, create a separate folder for each project:

1. Create a new directory for your project
2. Initialize a task file in that directory
3. Run all task commands from that directory

Example:
```bash
mkdir my_project
cd my_project
python -m task_manager.cli add "My Project" --notes "Description of my project"
```

### Managing Multiple Projects

To manage multiple projects:

1. Create a separate task file for each project
2. Specify the task file when running commands:
   ```bash
   python -m task_manager.cli --task-file project1/tasks.json list
   ```

## Best Practices

1. **Be Specific**: Write clear, actionable task descriptions
2. **Use Priorities**: Assign priorities to focus on what's most important
3. **Update Regularly**: Keep task statuses up to date
4. **Add Notes**: Include relevant details in the notes field
5. **Use Dependencies**: Define dependencies to establish a clear workflow
6. **Break Down Tasks**: Divide large tasks into smaller, manageable subtasks
7. **Review Regularly**: Regularly review and update your task list

## Troubleshooting

### Common Issues

- **Task Not Found**: Make sure you're using the correct task ID
- **Cannot Update Task**: Check if the task exists and if you have the correct permissions
- **File Not Found**: Ensure you're in the correct directory or specify the full path to the task file

### Getting Help

For more information on available commands and options:
```bash
python -m task_manager.cli --help
```

For help with a specific command:
```bash
python -m task_manager.cli add --help
```

## Advanced Usage

### Automating Task Management

You can create scripts to automate common task management operations:

```python
from task_manager import TaskManager

# Initialize task manager
task_manager = TaskManager("tasks.json")

# Add a new task
task = task_manager.add_task({
    "description": "My task",
    "priority": 1,
    "notes": "Task notes"
})

# Add a subtask
subtask = task.add_subtask({
    "description": "My subtask",
    "priority": 2
})

# Update task status
task_manager.update_task(task.id, status="in_progress")

# Get available tasks
available_tasks = task_manager.get_available_tasks()
for task in available_tasks:
    print(task)
```

### Integrating with Other Tools

Task Master can be integrated with other tools and workflows:

- **Version Control**: Store task files in a Git repository to track changes
- **CI/CD Pipelines**: Update task statuses automatically based on build results
- **Project Management Tools**: Import/export tasks from/to other project management tools

## Conclusion

Task Master provides a flexible and powerful way to manage your projects and tasks. By organizing your work in a hierarchical structure, setting priorities, and tracking dependencies, you can improve your productivity and ensure that nothing falls through the cracks.

Start by creating a dedicated folder for each project, add your tasks, and update their status as you make progress. Regularly review your task list to stay on track and adjust priorities as needed.

Happy task managing!
