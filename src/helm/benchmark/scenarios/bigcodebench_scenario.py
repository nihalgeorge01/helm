import datasets
import os
from typing import List
from helm.benchmark.scenarios.scenario import (
    Scenario,
    Instance,
    TEST_SPLIT,
    Input,
)
from helm.common.general import ensure_directory_exists


SUBSETS = ["v0.1.2"]


class BigCodeBenchScenario(Scenario):
    """BigCodeBench: Benchmarking Code Generation with Diverse Function Calls and Complex Instructions

    BigCodeBench is an easy-to-use benchmark for solving practical and challenging tasks via code.
    It aims to evaluate the true programming capabilities of large language models (LLMs) in a more realistic setting.
    The benchmark is designed for HumanEval-like function-level code generation tasks,
    but with much more complex instructions and diverse function calls."""

    name = "bigcodebench"
    description = "Benchmarking Code Generation with Diverse Function Calls and Complex Instructions"
    tags = ["coding"]

    def __init__(self, subset: str):
        super().__init__()
        assert subset in SUBSETS, "Unknown subset: {}".format(subset)
        self.subset = subset

    def get_instances(self, output_path: str) -> List[Instance]:
        # Get BigCodeBench from HuggingFace
        cache_dir = os.path.join(output_path, "data")
        ensure_directory_exists(cache_dir)
        dataset = datasets.load_dataset(
            "bigcode/bigcodebench",
            trust_remote_code=True,
            cache_dir=cache_dir,
            split="v0.1.2",
        )
        assert isinstance(dataset, datasets.Dataset)

        # Read all instances
        instances: List[Instance] = []
        for idx, row in enumerate(dataset):

            input = Input(text=row["instruct_prompt"])
            instance = Instance(
                input=input,
                references=[],
                split=TEST_SPLIT,
                extra_data={"task_id": row["task_id"]},
            )
            instances.append(instance)

        return instances