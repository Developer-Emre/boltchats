"""
Workflow Service

Orchestration layer for multi-step business processes.
Workflows are triggered by events or API calls.
"""

from enum import Enum
from typing import Any, Callable, Optional

import structlog
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.services.base import BaseService


logger = structlog.get_logger()


class WorkflowStep:
    """Single step in a workflow"""

    def __init__(
        self,
        name: str,
        handler: Callable,
        on_error: str = "stop",  # stop, retry, skip
        max_retries: int = 1,
    ):
        self.name = name
        self.handler = handler
        self.on_error = on_error
        self.max_retries = max_retries
        self.retries = 0


class WorkflowStatus(str, Enum):
    """Workflow execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkflowContext:
    """Context passed through workflow steps"""

    def __init__(self, org_id: str, workflow_id: str, data: dict):
        self.org_id = org_id
        self.workflow_id = workflow_id
        self.data = data
        self.results = {}
        self.status = WorkflowStatus.PENDING
        self.current_step = 0
        self.error = None

    def set(self, key: str, value: Any) -> None:
        """Store result from step."""
        self.results[key] = value

    def get(self, key: str) -> Any:
        """Retrieve result from previous step."""
        return self.results.get(key)

    def has(self, key: str) -> bool:
        """Check if result exists."""
        return key in self.results


class Workflow:
    """Base workflow class"""

    def __init__(self, name: str):
        self.name = name
        self.steps: list[WorkflowStep] = []

    def add_step(
        self,
        name: str,
        handler: Callable,
        on_error: str = "stop",
        max_retries: int = 1,
    ) -> "Workflow":
        """Add step to workflow."""
        self.steps.append(
            WorkflowStep(name, handler, on_error, max_retries)
        )
        return self

    async def execute(
        self,
        context: WorkflowContext,
    ) -> WorkflowContext:
        """
        Execute workflow steps in sequence.
        
        Args:
            context: Workflow context
            
        Returns:
            Updated context
        """
        context.status = WorkflowStatus.RUNNING

        for i, step in enumerate(self.steps):
            context.current_step = i

            retries = 0
            while retries <= step.max_retries:
                try:
                    logger.info(
                        "workflow_step_start",
                        workflow=self.name,
                        step=step.name,
                        retry=retries,
                    )

                    # Execute step handler
                    result = await step.handler(context)

                    # Store result
                    if result is not None:
                        context.set(step.name, result)

                    logger.info(
                        "workflow_step_complete",
                        workflow=self.name,
                        step=step.name,
                    )

                    break  # Move to next step

                except Exception as e:
                    retries += 1
                    logger.error(
                        "workflow_step_failed",
                        workflow=self.name,
                        step=step.name,
                        retry=retries,
                        error=str(e),
                    )

                    if retries > step.max_retries:
                        if step.on_error == "stop":
                            context.status = WorkflowStatus.FAILED
                            context.error = str(e)
                            logger.error(
                                "workflow_stopped",
                                workflow=self.name,
                                step=step.name,
                                reason=str(e),
                            )
                            return context

                        elif step.on_error == "skip":
                            logger.warning(
                                "workflow_step_skipped",
                                workflow=self.name,
                                step=step.name,
                            )
                            break

                        elif step.on_error == "retry":
                            # Already retrying, will fail above
                            pass

        if context.status == WorkflowStatus.RUNNING:
            context.status = WorkflowStatus.COMPLETED

        logger.info(
            "workflow_completed",
            workflow=self.name,
            status=context.status,
            steps=len(self.steps),
        )

        return context


class WorkflowService(BaseService):
    """Workflow orchestration service"""

    def __init__(self, db: AsyncIOMotorDatabase):
        super().__init__(db)
        self._workflows: dict[str, Workflow] = {}

    def register_workflow(self, workflow: Workflow) -> None:
        """Register a workflow."""
        self._workflows[workflow.name] = workflow
        logger.info("workflow_registered", workflow=workflow.name)

    async def execute_workflow(
        self,
        org_id: str,
        workflow_name: str,
        data: dict,
    ) -> WorkflowContext:
        """
        Execute a registered workflow.
        
        Args:
            org_id: Organization ID
            workflow_name: Workflow name
            data: Input data
            
        Returns:
            Workflow context with results
        """
        workflow = self._workflows.get(workflow_name)
        if not workflow:
            raise ValueError(f"Workflow not found: {workflow_name}")

        context = WorkflowContext(org_id, workflow_name, data)

        await self.log_action(
            "workflow_started",
            resource_id=workflow_name,
            resource_type="workflow",
            details={"data": data},
        )

        result = await workflow.execute(context)

        await self.log_action(
            "workflow_ended",
            resource_id=workflow_name,
            resource_type="workflow",
            details={
                "status": result.status,
                "results": result.results,
            },
        )

        return result

    def get_workflow(self, name: str) -> Optional[Workflow]:
        """Get workflow by name."""
        return self._workflows.get(name)

    def list_workflows(self) -> dict[str, Workflow]:
        """List all registered workflows."""
        return self._workflows

    def get_workflow_steps(self, name: str) -> list[dict]:
        """Get steps for workflow."""
        workflow = self._workflows.get(name)
        if not workflow:
            return []

        return [
            {
                "name": step.name,
                "on_error": step.on_error,
                "max_retries": step.max_retries,
            }
            for step in workflow.steps
        ]
